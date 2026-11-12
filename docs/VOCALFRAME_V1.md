# VocalFrame v1 — frozen contract proposal

The schema is in `schemas/vocal-frame-v1.schema.json`. `contract.py` performs semantic checks beyond JSON Schema: frequency-to-MIDI consistency (1 cent), per-session sequence/sample monotonicity and stable sample rate.

- `sequence` starts at 0 and increases **per session**.
- `sample_position` is the center of the analysis window, expressed in microphone sample-clock samples, not presentation frames.
- `session_id` is a UUID generated at session start.
- `f0_hz` and `midi_pitch` are both null for unvoiced or uncertain pitch. A3 = MIDI 57.0, A4 = MIDI 69.0. Fractional MIDI represents cents; do not infer nearest-note error from rounding when a target note is known.
- `f0_confidence` is detector-specific heuristic confidence, not a calibrated probability. `detector` identifies the algorithm/version.
- `rms_dbfs` is 20 log10(linear RMS); null means digital silence.
- `discontinuity` marks a lost-sample boundary. Downstream scoring must not silently bridge it.

## Clock model

Four separate domains: reference audio sample clock, microphone sample clock, render simulation clock and presentation/vsync clock. Calibration offsets are **not** baked into VocalFrame; a separate calibration event will record offset and measurement uncertainty.

## Acceptance tests (Given / When / Then)

1. **Given** 10 s of continuous 48 kHz PCM, **when** the capture adapter finishes, **then** exactly 480000 samples must be accounted for with zero dropped samples and zero discontinuities (subject to explicit device-start/end boundaries).
2. **Given** a stable A4 at 440 Hz, **when** the detector emits frames, **then** the MIDI value is approximately 69 and confidence is traceable to the detector version.
3. **Given** an unvoiced frame, **when** serialized, **then** both f0 and MIDI are null.
4. **Given** repeated or reordered sequence numbers, **when** validated within the same session, **then** reject.
5. **Given** a new session UUID, **when** sequence restarts, **then** accept.
6. **Given** missing or unknown contract fields, **when** parsed, **then** reject.
7. **Given** reference and microphone sample clocks, **when** calibrating, **then** record offset and uncertainty; no hard-coded 5 ms driver diagnosis.
8. **Given** expression features (vibrato, dynamics), **when** rendering v0.3, **then** display passively; do not include them in technical score until validated.

**Status:** contract and offline validation implemented; physical microphone capture and 10-second acceptance test not yet run.
