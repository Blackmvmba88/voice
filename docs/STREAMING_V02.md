# v0.2 — Streaming analysis core

This is a **device-independent streaming processor**, not a finished microphone capture app.

## Usage

```python
from blackmamba_voice.streaming import VocalStream
stream = VocalStream(sample_rate=16000, frame_ms=50, hop_ms=10)
stream.push(mono_float_pcm_chunk)
frames = stream.process_json(max_frames=8)
print(stream.stats())
```

Use `push()` from the capture adapter and `process_available()` on a worker thread, not inside the real-time audio callback. Python allocations and locking in `push()` are **not real-time safe**; a native ring buffer is required before production low-latency capture.

### Contracts
- PCM: finite mono float samples, explicit sample rate.
- Output: sample-clock midpoint timestamp, Hz, MIDI, heuristic confidence, RMS.
- Queue: bounded; on overflow oldest samples are discarded and counted.
- Time discontinuity: `discontinuities` and `dropped_samples` expose loss.
- No network, device capture, telemetry, or external account access.

### Next
- macOS AVAudioEngine/Core Audio adapter with user-approved microphone access.
- Worker queue + native lock-free ring buffer; p50/p95 latency benchmarks.
- Reference-note lane renderer and separate licensed lyric window.
- Keep local deterministic replay fixtures for CI.
