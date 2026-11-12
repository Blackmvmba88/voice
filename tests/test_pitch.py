import math
import unittest
from blackmamba_voice.pitch import estimate_pitch_yin, hz_to_midi, midi_to_hz

class PitchTests(unittest.TestCase):
    def test_a4(self):
        sr = 16000
        samples = [0.5 * math.sin(2 * math.pi * 440 * i / sr) for i in range(4096)]
        est = estimate_pitch_yin(samples, sr)
        self.assertIsNotNone(est.f0_hz)
        self.assertLess(abs(est.f0_hz - 440), 3)
        self.assertGreater(est.confidence, 0.95)

    def test_c4(self):
        sr = 16000
        samples = [0.5 * math.sin(2 * math.pi * midi_to_hz(60) * i / sr) for i in range(4096)]
        est = estimate_pitch_yin(samples, sr)
        self.assertLess(abs(hz_to_midi(est.f0_hz) - 60), 0.15)

    def test_silence(self):
        self.assertIsNone(estimate_pitch_yin([0.0] * 4096, 16000).f0_hz)

    def test_short_frame(self):
        self.assertIsNone(estimate_pitch_yin([0.1] * 10, 16000).f0_hz)

    def test_invalid_frequency(self):
        with self.assertRaises(ValueError): hz_to_midi(0)

    def test_bad_pcm(self):
        with self.assertRaises(ValueError): estimate_pitch_yin([float('nan')] * 4096, 16000)
