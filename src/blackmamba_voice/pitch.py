"""Reference implementation of YIN-like difference pitch detection.

Designed for correctness and zero runtime dependencies; real-time backend and
performance optimization are deliberately deferred until benchmarks exist.
"""
from dataclasses import dataclass
from math import isfinite, log2
from typing import Sequence

@dataclass(frozen=True)
class PitchEstimate:
    f0_hz: float | None
    confidence: float
    rms: float


def hz_to_midi(hz: float) -> float:
    if not isfinite(hz) or hz <= 0:
        raise ValueError('frequency must be finite and positive')
    return 69.0 + 12.0 * log2(hz / 440.0)


def midi_to_hz(midi: float) -> float:
    if not isfinite(midi):
        raise ValueError('MIDI pitch must be finite')
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def estimate_pitch_yin(samples: Sequence[float], sample_rate: int, *,
                       min_hz: float = 80.0, max_hz: float = 1000.0,
                       threshold: float = 0.12, silence_rms: float = 0.001) -> PitchEstimate:
    """Estimate monophonic fundamental frequency for one PCM frame.

    Returns no pitch for insufficient data, silence or uncertain periodicity.
    Uses unoptimized difference function and cumulative mean normalized difference.
    Background instruments and polyphony are not supported by this detector.
    """
    if sample_rate <= 0 or not 0 < min_hz < max_hz < sample_rate / 2:
        raise ValueError('invalid sample rate or pitch range')
    if not 0 < threshold < 1 or silence_rms < 0:
        raise ValueError('invalid threshold or silence level')
    n = len(samples)
    if not n:
        return PitchEstimate(None, 0.0, 0.0)
    if any(not isfinite(x) for x in samples):
        raise ValueError('PCM samples must be finite')
    rms = (sum(v * v for v in samples) / n) ** 0.5
    min_tau = max(2, int(sample_rate / max_hz))
    max_tau = min(int(sample_rate / min_hz), n // 2 - 1)
    if rms < silence_rms or max_tau <= min_tau:
        return PitchEstimate(None, 0.0, rms)
    # Fix comparison window length to avoid a lag-dependent scale distortion.
    window = n - max_tau
    diffs = [0.0] * (max_tau + 1)
    for tau in range(1, max_tau + 1):
        diffs[tau] = sum((samples[i] - samples[i + tau]) ** 2 for i in range(window))
    cmnd = [1.0] * (max_tau + 1)
    running = 0.0
    for tau in range(1, max_tau + 1):
        running += diffs[tau]
        if running > 1e-20:
            cmnd[tau] = diffs[tau] * tau / running
    candidate = None
    for tau in range(min_tau, max_tau + 1):
        if cmnd[tau] < threshold:
            while tau + 1 <= max_tau and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            candidate = tau
            break
    if candidate is None:
        return PitchEstimate(None, 0.0, rms)
    lag = float(candidate)
    if 1 <= candidate < max_tau:
        y0, y1, y2 = cmnd[candidate - 1:candidate + 2]
        denom = y0 - 2 * y1 + y2
        if abs(denom) > 1e-12:
            lag += max(-0.5, min(0.5, 0.5 * (y0 - y2) / denom))
    confidence = max(0.0, min(1.0, 1.0 - cmnd[candidate]))
    return PitchEstimate(sample_rate / lag, confidence, rms)
