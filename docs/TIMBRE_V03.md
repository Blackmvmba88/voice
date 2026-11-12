# Harmonic timbre comparison v0.3 — experimental diagnostic

This additive module (`blackmamba_voice.timbre`) compares **relative harmonic amplitudes** for two clean, sustained, isolated mono vocal segments, conditioned on *independently estimated and verified* fundamental frequencies. It does not identify singers, measure anatomical resonance, estimate formants, or perform source separation.

## Usage

```python
from blackmamba_voice.core import read_mono_wav, detect_pitch
from blackmamba_voice.timbre import compare_timbre

singer, rate_a = read_mono_wav("singer_dry.wav")
reference, rate_b = read_mono_wav("reference_isolated.wav")
# Manually choose matching steady vowels (80 ms to 2 s).
a = singer[:int(.25 * rate_a)]
b = reference[:int(.25 * rate_b)]
f0_a, conf_a = detect_pitch(a, rate_a)
f0_b, conf_b = detect_pitch(b, rate_b)
if f0_a is not None and f0_b is not None and min(conf_a, conf_b) >= .85:
    result = compare_timbre(a, b, rate_a, rate_b, f0_a, f0_b)
    print(result)
```

Outputs: `status` (`ok`, `insufficient_signal`, `pitch_mismatch`), `similarity` (cosine 0–1 or null), `pitch_difference_cents`, `harmonic_count`, `reason`.

**High similarity means only that the measured harmonic-amplitude shapes match in the sampled windows**, not that singers are identical. Comparison normalizes overall gain but does not normalize phoneme, microphone EQ, room response, dynamics or reverberation. The f0 inputs are assumed independently verified; if a pitch detector gives a low-confidence value, abstain before calling the comparison.

Do not compare a singer singing over Spotify playback against the mixed original: instrumental bleed and the original singer contaminate this measurement. Use a dry, isolated user recording and a rights-cleared isolated reference, preferably matched in sustained vowel and note. Uncertain, noisy, unvoiced, silent, or pitch-mismatched segments return a null similarity rather than fabricated match scores.

The original pitch scoring, streaming implementation and `VocalFrame v1` contract are unchanged.

## Local test

```sh
PYTHONPATH=src python -m pytest -q tests/test_timbre.py
```

Nine synthetic checks exercise gain invariance, distinct harmonic profiles, pitch mismatch, silence, noise, nonfinite/multichannel input and short windows. These unit tests **do not validate accuracy on human singers, real-time latency, or identity**. Real singing comparisons require controlled recordings and evaluation across phonemes, registers, microphones and rooms.
