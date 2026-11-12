import unittest
from blackmamba_voice.scoring import Note, Observation, score_notes

class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.note = Note('n1', 1000, 1500, 69)

    def test_perfect(self):
        frames = [Observation(t, 440, .99) for t in (1000, 1020, 1040, 1060)]
        result = score_notes([self.note], frames)[0]
        self.assertEqual(result.status, 'PERFECT')
        self.assertEqual(result.points, 100)
        self.assertAlmostEqual(result.pitch_error_cents, 0)

    def test_wrong_pitch(self):
        frames = [Observation(t, 493.88, .99) for t in (1000, 1020, 1040)]
        self.assertEqual(score_notes([self.note], frames)[0].status, 'MISS')

    def test_uncertain_is_unscorable(self):
        frames = [Observation(t, 440, .3) for t in (1000, 1020, 1040)]
        self.assertEqual(score_notes([self.note], frames)[0].status, 'UNSCORABLE')

    def test_latency_correction(self):
        frames = [Observation(t, 440, .99) for t in (1070, 1090, 1110)]
        self.assertEqual(score_notes([self.note], frames, latency_compensation_ms=70)[0].status, 'PERFECT')

    def test_invalid_note(self):
        with self.assertRaises(ValueError): Note('bad', 100, 100, 69)

    def test_invalid_observation(self):
        with self.assertRaises(ValueError): Observation(10, -50, .9)
