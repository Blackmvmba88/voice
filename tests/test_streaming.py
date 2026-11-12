import math
import numpy as np
import pytest
from blackmamba_voice.streaming import VocalStream

def tone(hz=440, duration=.3, rate=16000):
    t=np.arange(round(duration*rate))/rate
    return .5*np.sin(2*np.pi*hz*t)

def test_chunk_invariance():
    data=tone()
    a=VocalStream();a.push(data)
    first=a.process_json()
    b=VocalStream()
    for chunk in np.array_split(data,17):b.push(chunk)
    second=b.process_json()
    assert len(first)==len(second)
    assert [x["time_s"] for x in first]==[x["time_s"] for x in second]
    assert all(x["hz"] is not None and abs(1200*math.log2(x["hz"]/440))<20 for x in first)

def test_silence():
    s=VocalStream();s.push(np.zeros(1000))
    assert all(f.hz is None for f in s.process_available())

def test_no_frame_until_full():
    s=VocalStream();s.push(np.ones(799))
    assert s.process_available()==[]
    s.push(np.ones(1))
    assert len(s.process_available())==1

def test_limit():
    s=VocalStream();s.push(tone())
    assert len(s.process_available(2))==2
    assert len(s.process_available(0))==0
    assert len(s.process_available())>0

def test_overflow_accounted():
    s=VocalStream(max_buffer_ms=100);s.push(np.zeros(3200))
    assert s.stats()["dropped_samples"]==1600
    assert s.stats()["discontinuities"]==1
    assert s.process_available()[0].time_s >= .1

def test_reject_invalid():
    with pytest.raises(ValueError):VocalStream(frame_ms=5)
    with pytest.raises(ValueError):VocalStream(max_buffer_ms=40)
    s=VocalStream()
    with pytest.raises(ValueError):s.push(np.array([float("nan")]))
    with pytest.raises(ValueError):s.push(np.zeros((10,2)))
    with pytest.raises(ValueError):s.process_available(-1)

def test_no_data():
    s=VocalStream();s.push([])
    assert s.process_available()==[] and s.stats()["received_samples"]==0

def test_injectable_detector():
    s=VocalStream(detector=lambda samples,rate:(220.,.9))
    s.push(np.zeros(800))
    frame=s.process_available()[0]
    assert frame.midi==57 and frame.confidence==.9
