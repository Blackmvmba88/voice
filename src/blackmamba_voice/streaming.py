"""Bounded, device-agnostic streaming pitch analysis.

Push PCM from an audio capture adapter; call process_available on a worker.
No microphone permissions, network or audio device access in this module.
"""
from collections import deque
from dataclasses import dataclass, asdict
from threading import Lock
import numpy as np
from .core import detect_pitch, hz_to_midi

@dataclass(frozen=True)
class StreamFrame:
    time_s: float
    hz: float | None
    midi: float | None
    confidence: float
    rms: float

class VocalStream:
    def __init__(self, sample_rate=16000, frame_ms=50, hop_ms=10,
                 max_buffer_ms=1000, detector=detect_pitch):
        if not 8000 <= sample_rate <= 192000:
            raise ValueError("Invalid sample rate")
        if not 20 <= frame_ms <= 200 or not 5 <= hop_ms <= frame_ms:
            raise ValueError("Invalid frame/hop")
        if max_buffer_ms < 2*frame_ms:
            raise ValueError("Buffer must fit two frames")
        self.rate = sample_rate
        self.frame_size = round(sample_rate*frame_ms/1000)
        self.hop = round(sample_rate*hop_ms/1000)
        self.capacity = round(sample_rate*max_buffer_ms/1000)
        self.detector = detector
        self._buffer = deque()
        self._lock = Lock()
        self._next_sample = 0
        self._received = 0
        self.dropped_samples = 0
        self.discontinuities = 0

    def push(self, samples):
        x = np.asarray(samples, dtype=np.float64)
        if x.ndim != 1 or not np.all(np.isfinite(x)):
            raise ValueError("Expected finite mono PCM")
        if not len(x):
            return
        with self._lock:
            self._received += len(x)
            self._buffer.extend(x.tolist())
            overflow = max(0, len(self._buffer)-self.capacity)
            if overflow:
                for _ in range(overflow):
                    self._buffer.popleft()
                self._next_sample += overflow
                self.dropped_samples += overflow
                self.discontinuities += 1

    def process_available(self, max_frames=None):
        if max_frames is not None and max_frames < 0:
            raise ValueError("Invalid max_frames")
        out = []
        while max_frames is None or len(out) < max_frames:
            with self._lock:
                if len(self._buffer) < self.frame_size:
                    break
                chunk = np.fromiter(self._buffer, dtype=np.float64,
                                    count=self.frame_size)
                position = self._next_sample
                for _ in range(self.hop):
                    self._buffer.popleft()
                self._next_sample += self.hop
            hz, confidence = self.detector(chunk, self.rate)
            out.append(StreamFrame((position+self.frame_size/2)/self.rate,
                                   hz, hz_to_midi(hz) if hz is not None else None,
                                   confidence, float(np.sqrt(np.mean(chunk*chunk)))))
        return out

    def process_json(self, max_frames=None):
        return [asdict(frame) for frame in self.process_available(max_frames)]

    def stats(self):
        with self._lock:
            return dict(received_samples=self._received,
                        buffered_samples=len(self._buffer),
                        dropped_samples=self.dropped_samples,
                        discontinuities=self.discontinuities,
                        buffer_capacity_samples=self.capacity)
