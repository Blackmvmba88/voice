"""Explainable note-level scoring with explicit uncertainty and versioning."""
from dataclasses import dataclass
from math import isfinite, log2
from statistics import median
from typing import Sequence

SCORING_VERSION = '0.1.0'

@dataclass(frozen=True)
class Note:
    note_id: str
    start_ms: float
    end_ms: float
    midi_pitch: float

    def __post_init__(self):
        if not self.note_id or not all(map(isfinite, (self.start_ms, self.end_ms, self.midi_pitch))):
            raise ValueError('note fields must be valid')
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError('note interval must have positive duration')

@dataclass(frozen=True)
class Observation:
    timestamp_ms: float
    f0_hz: float | None
    confidence: float

    def __post_init__(self):
        if not isfinite(self.timestamp_ms) or self.timestamp_ms < 0 or not isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError('invalid observation timestamp or confidence')
        if self.f0_hz is not None and (not isfinite(self.f0_hz) or self.f0_hz <= 0):
            raise ValueError('invalid observed frequency')

@dataclass(frozen=True)
class NoteScore:
    note_id: str
    status: str
    pitch_error_cents: float | None
    onset_error_ms: float | None
    confidence: float
    points: int
    scoring_version: str = SCORING_VERSION


def score_notes(notes: Sequence[Note], observations: Sequence[Observation], *,
                min_confidence: float = 0.7, min_frames: int = 3,
                latency_compensation_ms: float = 0.0) -> list[NoteScore]:
    """Score known reference notes against monophonic measured frames.

    Onset = first confident voiced observation within note interval (after
    explicit calibrated timestamp correction). No dynamic time warp is used.
    If coverage is insufficient, return UNSCORABLE rather than invent MISS.
    """
    if not 0 <= min_confidence <= 1 or min_frames < 1 or not isfinite(latency_compensation_ms):
        raise ValueError('invalid scoring configuration')
    result = []
    for note in notes:
        accepted = [o for o in observations if o.f0_hz is not None and o.confidence >= min_confidence
                    and note.start_ms <= o.timestamp_ms - latency_compensation_ms < note.end_ms]
        if len(accepted) < min_frames:
            result.append(NoteScore(note.note_id, 'UNSCORABLE', None, None, 0.0, 0))
            continue
        target_hz = 440.0 * 2.0 ** ((note.midi_pitch - 69) / 12.0)
        errors = [1200 * log2(o.f0_hz / target_hz) for o in accepted]
        abs_error = median(abs(e) for e in errors)
        onset = min(o.timestamp_ms - latency_compensation_ms for o in accepted) - note.start_ms
        if abs_error <= 20 and onset <= 60:
            status, points = 'PERFECT', 100
        elif abs_error <= 50 and onset <= 120:
            status, points = 'GREAT', 75
        elif abs_error <= 100 and onset <= 200:
            status, points = 'GOOD', 40
        else:
            status, points = 'MISS', 0
        result.append(NoteScore(note.note_id, status, round(median(errors), 2), round(onset, 2),
                                round(median(o.confidence for o in accepted), 3), points))
    return result
