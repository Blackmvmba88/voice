# BLACKMAMBA VOCAL HERO AI — operational architecture

Design status: **specification**, not implementation.

## Mission

A local-first rhythm game and training system that scores a singer's pitch, onset timing, note coverage and musical expression against verified vocal note references, exposing confidence and uncertainty rather than fabricating grades.

## Pipeline

Owned/licensed audio → source adapter → reference note map (manual/verified first) → timestamp alignment → mic pitch observations → explainable scoring → game events → optional adaptive profile.

## Product windows

**Arena:** scrolling notes, pitch curve, combo, score, confidence and calibration.

**Lyrics/Coach:** separately dockable and synchronized window displaying owned/licensed lyrics, feedback, repeats and timing deviations.

## Planned adapters

- macOS Core Audio / AVAudioEngine microphone input.
- Local WAV/FLAC/MP3 imports, extending beyond the v0.1 WAV PCM16 diagnostic.
- Suno exports of user-owned recordings, if available and authorized.
- Spotify/SoundCloud for allowed metadata and playback control; do not assume raw PCM API access, download rights or lyric rights.
- Optional system capture only with user permission and compatible platform/provider restrictions.

## Local-first strategy

Use mature OS APIs and local libraries to ship and benchmark quickly; replace strategic components with BlackMamba-owned implementations only when tests justify it. Avoid any default cloud upload of microphone content. Version all scoring and personal models; never retroactively alter saved competition scores.

## Engineering gates

1. v0.1: synthetic fixed-frequency detection and note scoring, deterministic local tests.
2. v0.2: streaming, measured end-to-end latency and microphone calibration.
3. v0.3: reference separation/transcription and human-verified note maps.
4. v0.4: game UI, multiwindow lyrics and ghost.
5. v0.5: adaptive learning benchmarked for regressions, reversible profile.
6. v0.6: provider adapters under current terms and permissions.

**Not shipped:** game renderer, streaming audio I/O, neural separator, lyric transcription, trained adaptive model, third-party platform integrations. No measured real-time latency or human-singer accuracy has been established.

## Reproducibility

Run `PYTHONPATH=src python -m unittest discover -s tests -v`. For one-frame pitch diagnostics on an owned 16-bit mono WAV, run `PYTHONPATH=src python -m blackmamba_voice.cli sample.wav`. Synthetic tones only establish controlled unit-level behavior, not end-to-end vocal performance.
