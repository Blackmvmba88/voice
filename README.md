# BLACKMAMBA VOCAL HERO AI 🎤🐍

**Local-first Vocal Gaming & Intelligence Engine** · BlackMamba Corp · v0.1.0 (experimental)

## Real status

**Implemented:** zero-dependency Python reference detector (monophonic YIN-like pitch estimator), Hz/MIDI conversion, deterministic note-level scoring with `UNSCORABLE`, PCM16 mono WAV reader, offline diagnostic CLI, synthetic tests and GitHub Actions CI configuration.

**Not yet implemented:** real-time microphone capture, UI/gameplay, lyrics window, automatic reference melody extraction, source separation, adaptive AI, Suno/Spotify/SoundCloud account connections, system-wide audio capture. These require separate permission, data, latency and quality validation. Analyzing a streamed track is **not** guaranteed by a metadata/control API.

## Operational start (Python >=3.11)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
blackmamba-voice path/to/your_mono_16bit.wav
```

No runtime network connection, cloud model or credential is needed. The command analyzes **one frame at the midpoint** of a locally provided mono PCM16 WAV and reports an estimated frequency, confidence, RMS and MIDI pitch; it does not transcribe a full song.

## Layout

```text
src/blackmamba_voice/
  pitch.py       monophonic fundamental frequency estimator
  scoring.py     reproducible, explainable note grades
  wavio.py       WAV PCM16 mono loader
  cli.py         offline diagnostic
tests/           synthetic signal and scoring tests
.github/workflows/test.yml
```

## Evaluation contract

- `Note(note_id, start_ms, end_ms, midi_pitch)` represents a **verified** reference melody event.
- `Observation(timestamp_ms, f0_hz, confidence)` represents a measured vocal frame.
- `score_notes` outputs `PERFECT` / `GREAT` / `GOOD` / `MISS` / `UNSCORABLE` with signed cents error, onset error, confidence, points and scoring version.
- Insufficient confident frames always produce `UNSCORABLE`, **not** a penalty.
- Scores are preliminary **heuristics**, not calibrated against singers; no claims about vocal skill or clinical suitability are made.
- Timestamp compensation is caller-provided and should come from measured device calibration.
- For silence or uncertain fundamental frequency the pitch detector returns `None`.

## Engineering milestones

1. **v0.1 reference core:** deterministic offline detection/scoring + synthetic test corpus.
2. **v0.2 real-time host:** Core Audio microphone adapter, rolling frames, latency calibration and safe monitoring.
3. **v0.3 reference engine:** licensed/owned audio import, verified note maps, manual note-map editor, alignment and confidence.
4. **v0.4 game:** note highway, combo, independent lyrics overlay (owned/licensed text), practice and ghost.
5. **v0.5 local intelligence:** versioned singer profile, reversible adaptive difficulty and opt-in recordings.
6. **v0.6 providers:** optional API adapters for allowed catalog/control capabilities; no DRM bypass or unlicensed lyric scraping.

## Dependency strategy

**BUILD → VALIDATE → REPLACE.** Prefer mature local libraries and OS APIs to accelerate delivery; progressively replace only strategic components when benchmarked and justified. Keep the game, provider adapters and DSP core decoupled. The v0.1 Python DSP is a correctness reference, **not** a benchmarked real-time implementation.

## Acceptance metrics planned

Compare pitch cents error across synthetic voiced tones (80–1000 Hz) and then human recordings; measure voiced/unvoiced false positives, octave errors, CPU, end-to-end latency and track-to-microphone alignment under controlled conditions. Report measured hardware and conditions. Until then, these are targets, not achieved results.

## Safety, privacy and integrations

On-device analysis is the default. Never commit recordings, access tokens or confidential catalog exports. Obtain permission for mic/system audio, and comply with streaming and lyrics licensing restrictions. No automatic playback gain or uncontrolled audio feedback.
