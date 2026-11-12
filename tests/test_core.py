import math
import wave
import numpy as np
import pytest
from blackmamba_voice.core import (PitchFrame, TargetNote, analyze_audio,
                                    detect_pitch, hz_to_midi, read_mono_wav, score_notes)

def tone(hz=440, sr=16000, duration=.3):
    t=np.arange(round(sr*duration))/sr
    return .5*np.sin(2*np.pi*hz*t)

@pytest.mark.parametrize("hz",[110,220,440,880])
def test_pitch(hz):
    detected,conf=detect_pitch(tone(hz),16000)
    assert detected is not None and abs(1200*math.log2(detected/hz))<15
    assert conf>.85

def test_silence():
    assert detect_pitch(np.zeros(4000),16000)==(None,0.0)

def test_conversion():
    assert hz_to_midi(440)==69
    with pytest.raises(ValueError):
        hz_to_midi(0)

def test_monotonic_frames():
    frames=analyze_audio(tone(duration=.2),16000)
    assert len(frames)>=12
    assert all(a.time_s < b.time_s for a,b in zip(frames,frames[1:]))

def test_perfect():
    frames=[PitchFrame(.1,440,69,1),PitchFrame(.2,440,69,1)]
    out=score_notes(frames,[TargetNote(0,.3,69)])
    assert out["score"]==100 and out["coverage"]==1

def test_deviation_and_miss():
    frames=[PitchFrame(.1,440,69.3,1),PitchFrame(.2,None,None,0)]
    assert score_notes(frames,[TargetNote(0,.3,69)])["score"]==20

def test_no_targets():
    assert score_notes([],[])["score"] is None

def test_absent_audio_not_fake_zero():
    result=score_notes([],[TargetNote(0,.5,69)])
    assert result["score"] is None and result["coverage"]==0

def test_overlap():
    with pytest.raises(ValueError):
        score_notes([],[TargetNote(0,1,69),TargetNote(.5,1.5,70)])

def test_invalid_note():
    with pytest.raises(ValueError):
        TargetNote(1,0,69)

def test_wav(tmp_path):
    path=tmp_path/"sample.wav"
    sig=tone(duration=.1)
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000)
        f.writeframes((sig*32767).astype("<i2").tobytes())
    samples,rate=read_mono_wav(path)
    assert rate==16000 and len(samples)==len(sig)
    assert np.max(np.abs(sig-samples))<1e-4

def test_stereo(tmp_path):
    path=tmp_path/"stereo.wav"
    a=np.column_stack([np.zeros(8,dtype="<i2"),np.full(8,16384,dtype="<i2")])
    with wave.open(str(path),"wb") as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(16000)
        f.writeframes(a.tobytes())
    data,_=read_mono_wav(path)
    assert np.allclose(data,.25)

def test_nonfinite():
    with pytest.raises(ValueError):
        detect_pitch(np.full(500,float("nan")),16000)
