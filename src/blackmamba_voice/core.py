"""Offline voice pitch analysis and auditable note scoring."""
from dataclasses import asdict, dataclass
import math
import wave
from pathlib import Path
import numpy as np

@dataclass(frozen=True)
class PitchFrame:
    time_s: float
    hz: float | None
    midi: float | None
    confidence: float

@dataclass(frozen=True)
class TargetNote:
    start_s: float
    end_s: float
    midi: float
    def __post_init__(self):
        if not all(math.isfinite(x) for x in (self.start_s, self.end_s, self.midi)):
            raise ValueError("Non-finite target")
        if self.start_s < 0 or self.end_s <= self.start_s or not 0 <= self.midi <= 127:
            raise ValueError("Invalid target note")

def hz_to_midi(hz: float) -> float:
    if not math.isfinite(hz) or hz <= 0:
        raise ValueError("Hz must be positive and finite")
    return 69 + 12 * math.log2(hz / 440)

def read_mono_wav(path: str | Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        rate, channels, width = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        if wf.getcomptype() != "NONE" or width not in (1, 2, 3, 4):
            raise ValueError("Only integer PCM WAV is supported")
        if not 8000 <= rate <= 192000 or not 1 <= channels <= 16:
            raise ValueError("Unsupported sample rate or channels")
        raw = wf.readframes(wf.getnframes())
    if width == 1:
        samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        samples = ((v ^ 0x800000) - 0x800000).astype(np.float64) / (2**23)
    else:
        samples = np.frombuffer(raw, dtype="<i2" if width == 2 else "<i4").astype(np.float64) / (2 ** (8 * width - 1))
    return samples.reshape(-1, channels).mean(axis=1), rate

def detect_pitch(frame: np.ndarray, sample_rate: int, min_hz: float = 80,
                 max_hz: float = 1100, silence_rms: float = 0.008) -> tuple[float | None, float]:
    x = np.asarray(frame, dtype=np.float64)
    if x.ndim != 1 or len(x) < 32 or sample_rate <= 0:
        raise ValueError("Expected a mono frame and positive rate")
    if not np.all(np.isfinite(x)):
        raise ValueError("Non-finite audio")
    x = x - np.mean(x)
    if float(np.sqrt(np.mean(x * x))) < silence_rms:
        return None, 0.0
    lo = max(2, int(sample_rate / max_hz))
    hi = min(int(sample_rate / min_hz), len(x) // 2)
    if hi <= lo:
        return None, 0.0
    size = 1 << (2 * len(x) - 1).bit_length()
    fft = np.fft.rfft(x, n=size)
    ac = np.fft.irfft(fft * np.conj(fft), n=size)[:hi + 1]
    prefix = np.r_[0.0, np.cumsum(x * x)]
    lags = np.arange(1, hi + 1)
    energy = prefix[len(x) - lags] + prefix[len(x)] - prefix[lags]
    diff = np.maximum(energy - 2 * ac[1:hi + 1], 0.0)
    cmnd = np.ones(hi + 1, dtype=np.float64)
    cmnd[1:] = diff * lags / np.maximum(np.cumsum(diff), 1e-12)
    troughs = [i for i in range(lo + 1, hi) if cmnd[i] < .16 and cmnd[i] <= cmnd[i-1] and cmnd[i] < cmnd[i+1]]
    lag = troughs[0] if troughs else min(range(lo, hi+1), key=lambda i: cmnd[i])
    confidence = float(np.clip(1 - cmnd[lag], 0, 1))
    if confidence < .75:
        return None, confidence
    refined = float(lag)
    if 1 < lag < hi:
        a, b, c = cmnd[lag-1:lag+2]
        denom = a - 2*b + c
        if abs(denom) > 1e-12:
            refined += float(np.clip(.5*(a-c)/denom, -.5, .5))
    return sample_rate / refined, confidence

def analyze_audio(samples: np.ndarray, rate: int, frame_ms: int = 50,
                  hop_ms: int = 10) -> list[PitchFrame]:
    if not 20 <= frame_ms <= 200 or not 5 <= hop_ms <= frame_ms:
        raise ValueError("Invalid frame/hop")
    frame_size, hop = round(rate * frame_ms / 1000), round(rate * hop_ms / 1000)
    if frame_size < 32 or hop < 1:
        raise ValueError("Invalid rate")
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 1:
        raise ValueError("Expected mono audio")
    frames = []
    for i in range(0, len(samples)-frame_size+1, hop):
        hz, confidence = detect_pitch(samples[i:i+frame_size], rate)
        frames.append(PitchFrame((i+frame_size/2)/rate, hz,
                                 hz_to_midi(hz) if hz is not None else None, confidence))
    return frames

def score_notes(frames: list[PitchFrame], notes: list[TargetNote],
                tolerance_cents: float = 50) -> dict:
    if tolerance_cents <= 0 or not math.isfinite(tolerance_cents):
        raise ValueError("Invalid cents tolerance")
    notes = sorted(notes, key=lambda note: note.start_s)
    if any(a.end_s > b.start_s for a,b in zip(notes, notes[1:])):
        raise ValueError("Overlapping notes")
    if not notes:
        return {"score": None, "coverage": 0.0, "notes": [], "reason": "No target notes"}
    results = []
    for n in notes:
        matched = [f for f in frames if n.start_s <= f.time_s < n.end_s]
        voiced = [f for f in matched if f.midi is not None]
        values = [max(0., 1. - abs(f.midi-n.midi)*100/tolerance_cents)
                  if f.midi is not None else 0. for f in matched]
        score = 100*float(np.mean(values)) if values else None
        offsets = [(f.midi-n.midi)*100 for f in voiced]
        results.append({"start_s": n.start_s, "end_s": n.end_s, "target_midi": n.midi,
                        "score": round(score,2) if score is not None else None,
                        "frames": len(matched), "voiced_frames": len(voiced),
                        "median_cents_error": round(float(np.median(offsets)),2) if offsets else None})
    available = [r["score"] for r in results if r["score"] is not None]
    return {"score": round(float(np.mean(available)),2) if available else None,
            "coverage": round(sum(r["frames"]>0 for r in results)/len(results),3),
            "notes": results, "reason": None if available else "No measured target frames"}

def pitch_frame_dicts(frames: list[PitchFrame]) -> list[dict]:
    return [asdict(frame) for frame in frames]
