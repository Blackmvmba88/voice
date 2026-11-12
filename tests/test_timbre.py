"""Deterministic synthetic tests; NOT validation against real singers."""
import numpy as np
import pytest
from blackmamba_voice.timbre import harmonic_profile, compare_timbre

RATE = 16000
T = np.arange(4096) / RATE


def signal(f0=220.0, amplitudes=(1.0, 0.6, 0.3, 0.15), gain=0.3):
    return gain * sum(a * np.sin(2 * np.pi * (i + 1) * f0 * T)
                      for i, a in enumerate(amplitudes))


def test_gain_invariance():
    x = signal()
    result = compare_timbre(x, x * 0.33, RATE, RATE, 220, 220)
    assert result['status'] == 'ok'
    assert result['similarity'] == pytest.approx(1.0, abs=0.001)
    assert result['harmonic_count'] >= 4


def test_different_harmonic_envelopes_are_less_similar():
    x = signal(amplitudes=(1, 0.7, 0.2, 0.05))
    y = signal(amplitudes=(0.1, 0.1, 1.0, 0.9))
    result = compare_timbre(x, y, RATE, RATE, 220, 220)
    assert result['status'] == 'ok'
    assert result['similarity'] < 0.7


def test_pitch_mismatch_abstains():
    result = compare_timbre(signal(220), signal(261.63), RATE, RATE, 220, 261.63)
    assert result['status'] == 'pitch_mismatch'
    assert result['similarity'] is None


def test_silence_abstains():
    assert harmonic_profile(np.zeros(len(T)), RATE, 220) is None
    assert compare_timbre(signal(), np.zeros(len(T)), RATE, RATE, 220, 220)['similarity'] is None


def test_noise_abstains():
    noise = np.random.default_rng(1234).normal(0, 0.15, len(T))
    assert harmonic_profile(noise, RATE, 220) is None


@pytest.mark.parametrize('bad', [np.array([float('nan')]*4096), np.zeros((2, 4096))])
def test_bad_signal_rejected(bad):
    with pytest.raises(ValueError):
        harmonic_profile(bad, RATE, 220)


def test_invalid_pitch_rejected():
    with pytest.raises(ValueError):
        harmonic_profile(signal(), RATE, float('nan'))
    with pytest.raises(ValueError):
        compare_timbre(signal(), signal(), RATE, RATE, 220, 220, max_pitch_difference_cents=0)


def test_short_frame_rejected():
    with pytest.raises(ValueError):
        harmonic_profile(np.zeros(128), RATE, 220)
