# BLACKMAMBA VOCAL HERO AI 🐍🎤

**Guitar Hero-style adaptive vocal game — local-first engineering prototype v0.1.0**

> **Implemented:** offline monophonic pitch estimation and explainable per-note scoring.
> **Not implemented:** real-time microphone, game UI, lyric synchronization, learning, streaming connectors or automatic reference creation.

## Goal
Build a vocal game that listens to your singing, evaluates technical accuracy, learns your capabilities without silently changing historical scores, and runs locally as much as possible. Use proven third-party libraries first; replace strategically with validated BlackMamba-owned modules.

## Local setup

Requires Python 3.10+ and NumPy. Does not need internet after installation.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
blackmamba-voice own_vocal.wav --out report.json
```

Optionally evaluate against `targets.json`:

```json
[
  {"start_s":0.0,"end_s":0.5,"midi":69},
  {"start_s":0.5,"end_s":1.0,"midi":71}
]
```

```bash
blackmamba-voice own_vocal.wav --target targets.json --out scored.json
```

The input must be uncompressed integer-PCM WAV (8/16/24/32-bit); stereo is mixed to mono. Pitch frames include timestamp, Hz, MIDI and *heuristic* confidence. Silence produces no fabricated pitch. Scores use target note intervals and 50-cent default tolerance. Without overlapping recorded frames the score is `null`, not zero. Current coverage measures target notes with observed frames, not fraction of reference duration.

## Code
- `src/blackmamba_voice/core.py`: pure local WAV decoding, FFT-accelerated YIN-style pitch tracking, note scoring.
- `src/blackmamba_voice/cli.py`: JSON report command.
- `tests/test_core.py`: 16 local synthetic and boundary tests.
- `.github/workflows/test.yml`: CI test matrix for Python 3.10/3.12/3.13.

## Limitations
This score measures **pitch alignment only**, not expressive interpretation, rhythmic accuracy, vocal quality or lyric accuracy. Dry monophonic recordings are recommended: accompaniment, harmonics and reverberation can confuse detection. No user accounts or third-party audio access are implemented.

## Roadmap
1. v0.2: local microphone bridge, timestamp calibration and latency benchmarks.
2. v0.3: visual note lanes, overlay and separate lyrics panel for rights-cleared text.
3. v0.4: onset/rhythm error measurement, confidence abstention and artistically flexible judgment.
4. v0.5: versioned on-device adaptive training, personal best and Ghost Mode.
5. v0.6: legal Suno export import and permission-constrained Spotify/SoundCloud metadata/playback connectors.

## Policy
**Build → Validate → Replace.** Start with NumPy and existing OS audio APIs; compare any replacement using repeatable pitch accuracy, p50/p95 latency, CPU and memory tests. Privacy by design; no hidden microphone capture, account secrets in Git, cloud uploads without consent, DRM bypass, or unexpected microphone monitoring.

**BlackMamba Corp — Music Intelligence Laboratory**
