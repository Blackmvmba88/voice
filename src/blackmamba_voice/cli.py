"""Offline command-line analysis."""
import argparse
import json
from pathlib import Path
from .core import TargetNote, analyze_audio, pitch_frame_dicts, read_mono_wav, score_notes

def main() -> None:
    parser = argparse.ArgumentParser(description="BlackMamba Vocal Hero: local pitch evaluator")
    parser.add_argument("wav", help="Own isolated vocal PCM WAV")
    parser.add_argument("--target", help="Optional JSON array of target notes")
    parser.add_argument("--out", help="Write JSON output to this path")
    args = parser.parse_args()
    samples, rate = read_mono_wav(args.wav)
    frames = analyze_audio(samples, rate)
    report = {"version":"0.1.0","input":args.wav,"sample_rate":rate,
              "duration_s":round(len(samples)/rate,3),"pitch_frames":pitch_frame_dicts(frames)}
    if args.target:
        payload = json.loads(Path(args.target).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            parser.error("Target file must be a JSON array")
        report["evaluation"] = score_notes(frames,[TargetNote(**entry) for entry in payload])
    result = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    if args.out:
        Path(args.out).write_text(result,encoding="utf-8")
    else:
        print(result)

if __name__ == "__main__":
    main()
