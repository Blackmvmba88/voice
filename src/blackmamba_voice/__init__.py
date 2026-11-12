"""BlackMamba Vocal Hero AI: portable local-first vocal evaluation core."""
from .pitch import PitchEstimate, estimate_pitch_yin, hz_to_midi, midi_to_hz
from .scoring import Note, Observation, NoteScore, score_notes
__all__ = ['PitchEstimate', 'estimate_pitch_yin', 'hz_to_midi', 'midi_to_hz', 'Note', 'Observation', 'NoteScore', 'score_notes']
__version__ = '0.1.0'
