"""Local, mono PCM16 WAV import for baseline experiments."""
import struct
import wave
from pathlib import Path


def read_mono_pcm16(path: str | Path) -> tuple[int, list[float]]:
    with wave.open(str(path), 'rb') as wav:
        if wav.getcomptype() != 'NONE' or wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError('v0.1 supports only mono uncompressed 16-bit WAV')
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    count = len(frames) // 2
    data = struct.unpack('<' + 'h' * count, frames)
    return sample_rate, [x / 32768.0 for x in data]
