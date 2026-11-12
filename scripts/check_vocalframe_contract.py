#!/usr/bin/env python3
"""Reproducible VocalFrame v1 contract smoke check; stdlib only."""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blackmamba_voice.contract import VocalFrameV1, FrameSequenceValidator


def payload(**changes):
    result = dict(schema_version="1.0.0", event_type="vocal.frame",
                  session_id=str(uuid4()), sequence=0, sample_rate=48000,
                  sample_position=2400, detector="yin-v0.2", f0_hz=440.0,
                  midi_pitch=69.0, f0_confidence=0.96,
                  rms_dbfs=-17.1, discontinuity=False)
    result.update(changes)
    return result


def check(tolerance_cents):
    passed = 0
    failures = []

    def run(name, test):
        nonlocal passed
        try:
            test()
            passed += 1
            print("PASS", name)
        except Exception as exc:
            failures.append({"case": name, "error": repr(exc)})
            print("FAIL", name, repr(exc))

    def accepted(p):
        VocalFrameV1.from_dict(p)

    def rejected(p):
        try:
            accepted(p)
        except (ValueError, TypeError):
            return
        raise AssertionError("Invalid frame accepted")

    def boundary():
        # The validator contract is fixed at 1 cent; CLI tolerance is
        # used to generate the two probes, not to change production rules.
        if not math.isclose(tolerance_cents, 1.0, abs_tol=1e-12):
            raise ValueError("VocalFrame v1 requires exactly 1.00 cent")
        accepted(payload(midi_pitch=69.01))
        rejected(payload(midi_pitch=69.0101))

    run("one_cent_boundary", boundary)
    run("invalid_frequency_type", lambda: rejected(payload(f0_hz="440")))
    run("invalid_confidence_type", lambda: rejected(payload(f0_confidence="0.96")))
    run("null_confidence", lambda: rejected(payload(f0_confidence=None)))
    run("negative_frequency", lambda: rejected(payload(f0_hz=-1)))
    run("null_pitch_pair", lambda: accepted(payload(f0_hz=None, midi_pitch=None)))
    run("unknown_field", lambda: rejected(dict(payload(), extra=1)))

    def sequence_gap():
        session = str(uuid4())
        validator = FrameSequenceValidator()
        validator.accept(VocalFrameV1.from_dict(payload(
            session_id=session, sequence=1024, sample_position=491520)))
        validator.accept(VocalFrameV1.from_dict(payload(
            session_id=session, sequence=1026, sample_position=492480,
            discontinuity=True)))
    run("sequence_gap_allowed", sequence_gap)

    report = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  schema_version="1.0.0", passed=passed,
                  failed=len(failures), failures=failures)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--cents-tolerance", type=float, default=1.0)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        from contextlib import redirect_stdout
        with args.log.open("w", encoding="utf-8") as output:
            with redirect_stdout(output):
                code = check(args.cents_tolerance)
        print(args.log.read_text(encoding="utf-8"), end="")
        return code
    return check(args.cents_tolerance)


if __name__ == "__main__":
    raise SystemExit(main())
