"""VocalFrame v1 semantic validation and monotonic per-session sequence checks.

JSON Schema checks shape; this module additionally checks Hz/MIDI coherence,
strictly increasing sequence and sample positions for each session.
"""
from dataclasses import dataclass, asdict
from math import isfinite, log2
from uuid import UUID

@dataclass(frozen=True)
class VocalFrameV1:
    schema_version: str
    event_type: str
    session_id: str
    sequence: int
    sample_rate: int
    sample_position: int
    detector: str
    f0_hz: float | None
    midi_pitch: float | None
    f0_confidence: float
    rms_dbfs: float | None
    discontinuity: bool

    def __post_init__(self):
        if self.schema_version != "1.0.0" or self.event_type != "vocal.frame":
            raise ValueError("Unsupported frame contract")
        try:
            UUID(self.session_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("Invalid session_id UUID") from exc
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("Invalid sequence")
        if type(self.sample_rate) is not int or not 8000 <= self.sample_rate <= 192000:
            raise ValueError("Invalid sample_rate")
        if type(self.sample_position) is not int or self.sample_position < 0:
            raise ValueError("Invalid sample_position")
        if not isinstance(self.detector, str) or not 1 <= len(self.detector) <= 128:
            raise ValueError("Invalid detector")
        if type(self.discontinuity) is not bool:
            raise ValueError("Invalid discontinuity")
        if type(self.f0_confidence) not in (float, int) or not isfinite(self.f0_confidence) or not 0 <= self.f0_confidence <= 1:
            raise ValueError("Invalid confidence")
        if self.rms_dbfs is not None and (type(self.rms_dbfs) not in (float, int) or not isfinite(self.rms_dbfs) or self.rms_dbfs > 0):
            raise ValueError("Invalid RMS dBFS")
        if (self.f0_hz is None) != (self.midi_pitch is None):
            raise ValueError("Pitch and MIDI must both be null or both be present")
        if self.f0_hz is not None:
            if type(self.f0_hz) not in (float, int) or not isfinite(self.f0_hz) or not 0 < self.f0_hz <= 10000:
                raise ValueError("Invalid f0_hz")
            if type(self.midi_pitch) not in (float, int) or not isfinite(self.midi_pitch) or not 0 <= self.midi_pitch <= 127:
                raise ValueError("Invalid midi_pitch")
            expected = 69 + 12 * log2(self.f0_hz / 440)
            if abs(expected - self.midi_pitch) > 0.01 + 1e-12:
                raise ValueError("Hz/MIDI mismatch beyond 1 cent")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, payload):
        if set(payload) != set(cls.__dataclass_fields__):
            raise ValueError("Missing or unknown fields")
        return cls(**payload)

class FrameSequenceValidator:
    """Sequence is per session, not global. Tracks each session independently."""
    def __init__(self):
        self._last = {}

    def accept(self, frame: VocalFrameV1):
        previous = self._last.get(frame.session_id)
        if previous is not None:
            last_seq, last_sample, last_rate = previous
            if frame.sequence <= last_seq or frame.sample_position <= last_sample:
                raise ValueError("Non-monotonic sequence/sample position")
            if frame.sample_rate != last_rate:
                raise ValueError("Sample rate changed within session")
        self._last[frame.session_id] = (frame.sequence, frame.sample_position, frame.sample_rate)
        return frame
