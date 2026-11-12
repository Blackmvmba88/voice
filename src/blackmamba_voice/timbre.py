"""Experimental, pitch-conditioned harmonic-envelope comparison.

Requires clean, isolated, sustained mono vocal segments. It does NOT identify
singers, measure anatomical resonance, or imply that two voices are the same.
This module never changes the existing VocalFrame v1 or pitch scoring.
"""
from dataclasses import asdict, dataclass
from math import isfinite, log2

import numpy as np


@dataclass(frozen=True)
class HarmonicProfile:
    f0_hz: float
    rms: float
    harmonicity: float
    amplitudes: tuple[float, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def harmonic_profile(samples, sample_rate: int, f0_hz: float, *,
                     max_harmonics: int = 24, max_frequency_hz: float = 5000.0,
                     min_rms: float = 0.003) -> HarmonicProfile | None:
    """Extract normalized harmonic amplitudes from one steady vowel/voiced frame.

    Pass an *independently verified* fundamental frequency (e.g. existing pitch
    estimator). Return None if signal is too short, quiet, or insufficiently
    harmonic; do not fabricate pitch or a valid voice match.
    """
    if type(sample_rate) is not int or not 8000 <= sample_rate <= 192000:
        raise ValueError("sample_rate must be an integer in [8000, 192000]")
    if not isfinite(f0_hz) or not 60 <= f0_hz <= 1200:
        raise ValueError("f0_hz must be finite and within [60, 1200]")
    if type(max_harmonics) is not int or not 3 <= max_harmonics <= 64:
        raise ValueError("max_harmonics must be in [3, 64]")
    if not isfinite(max_frequency_hz) or max_frequency_hz <= 0:
        raise ValueError("invalid max_frequency_hz")
    if not isfinite(min_rms) or min_rms < 0:
        raise ValueError("invalid min_rms")
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise ValueError("Expected finite mono PCM")
    if len(x) < int(0.08 * sample_rate) or len(x) > 2 * sample_rate:
        raise ValueError("Provide one isolated frame between 80 ms and 2 s")
    x = x - np.mean(x)
    rms = float(np.sqrt(np.mean(x * x)))
    if rms < min_rms:
        return None
    upper = min(max_frequency_hz, sample_rate * 0.45)
    count = min(max_harmonics, int(upper / f0_hz))
    if count < 3:
        return None
    spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    frequencies = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    valid = (frequencies >= 60.0) & (frequencies <= upper)
    total = float(np.sum(spectrum[valid]))
    if total <= 1e-20:
        return None
    peaks = []
    harmonic_mask = np.zeros(len(spectrum), dtype=bool)
    bin_hz = sample_rate / len(x)
    for harmonic in range(1, count + 1):
        center_hz = harmonic * f0_hz
        # Window covers frequency quantization and mild f0 drift, but avoids
        # including the adjacent harmonic for singing fundamentals.
        tolerance = max(1.5 * bin_hz, 0.015 * center_hz)
        tolerance = min(tolerance, 0.20 * f0_hz)
        region = np.abs(frequencies - center_hz) <= tolerance
        harmonic_mask |= region
        peaks.append(float(np.sqrt(np.max(spectrum[region]))) if np.any(region) else 0.0)
    harmonicity = float(np.sum(spectrum[harmonic_mask & valid]) / total)
    if harmonicity < 0.60:
        return None
    vector = np.asarray(peaks, dtype=np.float64)
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-20:
        return None
    return HarmonicProfile(f0_hz, rms, harmonicity,
                           tuple(float(v) for v in vector / norm))


def compare_timbre(first, second, first_rate: int, second_rate: int,
                   first_f0_hz: float, second_f0_hz: float, *,
                   max_pitch_difference_cents: float = 100.0) -> dict:
    """Compare harmonic *shapes*, abstaining on mismatched notes/poor signal.

    Similarity is a diagnostic cosine coefficient, not an identity probability
    or a music-performance grade. Reference and singer must be isolated,
    aligned to a similar sustained vowel, and free of instrument bleed.
    """
    if not isfinite(max_pitch_difference_cents) or not 0 < max_pitch_difference_cents <= 200:
        raise ValueError("Invalid pitch difference tolerance")
    # Let harmonic_profile validate even if the pitches do not match.
    a = harmonic_profile(first, first_rate, first_f0_hz)
    b = harmonic_profile(second, second_rate, second_f0_hz)
    cents = abs(1200.0 * log2(first_f0_hz / second_f0_hz))
    result = {"status": "insufficient_signal", "similarity": None,
              "pitch_difference_cents": round(cents, 2),
              "harmonic_count": 0, "reason": None}
    if a is None or b is None:
        result["reason"] = "At least one signal is silent, unvoiced, or insufficiently harmonic"
        return result
    if cents > max_pitch_difference_cents:
        result.update(status="pitch_mismatch", reason="Compare the same note or transposed reference")
        return result
    n = min(len(a.amplitudes), len(b.amplitudes))
    u = np.asarray(a.amplitudes[:n])
    v = np.asarray(b.amplitudes[:n])
    denom = float(np.linalg.norm(u) * np.linalg.norm(v))
    if denom <= 1e-20:
        result["reason"] = "No comparable harmonic amplitudes"
        return result
    result.update(status="ok", similarity=round(float(np.clip(np.dot(u, v) / denom, 0, 1)), 5),
                  harmonic_count=n, reason=None)
    return result
