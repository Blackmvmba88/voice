"""Offline developer CLI: inspect monophonic WAV with local pitch detector."""
import argparse
import json
from .wavio import read_mono_pcm16
from .pitch import estimate_pitch_yin, hz_to_midi


def main() -> None:
    parser = argparse.ArgumentParser(description='BlackMamba Vocal Hero offline diagnostic')
    parser.add_argument('wav', help='mono PCM16 WAV to analyze')
    parser.add_argument('--min-hz', type=float, default=80.0)
    parser.add_argument('--max-hz', type=float, default=1000.0)
    args = parser.parse_args()
    sr, samples = read_mono_pcm16(args.wav)
    # One frame from the middle: explicitly a diagnostic, not a song transcription.
    frame_size = max(2048, int(sr * 0.08))
    mid = len(samples) // 2
    frame = samples[max(0, mid - frame_size // 2): max(0, mid - frame_size // 2) + frame_size]
    est = estimate_pitch_yin(frame, sr, min_hz=args.min_hz, max_hz=args.max_hz)
    print(json.dumps({'f0_hz': est.f0_hz, 'confidence': est.confidence,
                      'rms': est.rms, 'midi': hz_to_midi(est.f0_hz) if est.f0_hz else None}, indent=2))

if __name__ == '__main__':
    main()
