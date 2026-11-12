import uuid
import pytest
from blackmamba_voice.contract import VocalFrameV1, FrameSequenceValidator

def valid(**updates):
    data=dict(schema_version="1.0.0",event_type="vocal.frame",
              session_id=str(uuid.uuid4()),sequence=0,sample_rate=48000,
              sample_position=2400,detector="yin-v0.2",f0_hz=440.,
              midi_pitch=69.,f0_confidence=.96,rms_dbfs=-17.1,
              discontinuity=False)
    data.update(updates)
    return data

def test_round_trip():
    payload=valid()
    assert VocalFrameV1.from_dict(payload).to_dict()==payload

def test_silence():
    assert VocalFrameV1.from_dict(valid(f0_hz=None,midi_pitch=None,rms_dbfs=None)).f0_hz is None

@pytest.mark.parametrize("field,value",[
    ("sequence",-1),("sample_position",-1),("sample_rate",2000),
    ("f0_confidence",1.1),("f0_hz",-440),("midi_pitch",70),
    ("rms_dbfs",1.0),("detector",""),("session_id","not-uuid"),
    ("discontinuity",1),("schema_version","2.0.0")
])
def test_reject_invalid(field,value):
    with pytest.raises(ValueError):
        VocalFrameV1.from_dict(valid(**{field:value}))

def test_missing_or_extra():
    payload=valid();payload["unknown"]=1
    with pytest.raises(ValueError):VocalFrameV1.from_dict(payload)

def test_monotonic():
    session=str(uuid.uuid4())
    validator=FrameSequenceValidator()
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session)))
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1,sample_position=2880)))
    with pytest.raises(ValueError):
        validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1,sample_position=3000)))

def test_reject_sample_regression():
    session=str(uuid.uuid4())
    validator=FrameSequenceValidator()
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session)))
    with pytest.raises(ValueError):
        validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1,sample_position=2399)))

def test_separate_sessions():
    validator=FrameSequenceValidator()
    validator.accept(VocalFrameV1.from_dict(valid()))
    validator.accept(VocalFrameV1.from_dict(valid()))

def test_rate_change():
    session=str(uuid.uuid4())
    validator=FrameSequenceValidator()
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session)))
    with pytest.raises(ValueError):
        validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1,sample_position=2880,sample_rate=44100)))

def test_one_cent_boundary():
    payload=valid(midi_pitch=69.01)
    assert VocalFrameV1.from_dict(payload).midi_pitch==69.01
    with pytest.raises(ValueError):
        VocalFrameV1.from_dict(valid(midi_pitch=69.0101))

@pytest.mark.parametrize("field,value",[
    ("f0_confidence","0.9"),("f0_confidence",None),
    ("f0_hz","440"),("midi_pitch","69"),("rms_dbfs","-17"),
    ("f0_hz",None)
])
def test_invalid_types_and_null_coherence(field,value):
    with pytest.raises((ValueError,TypeError)):
        VocalFrameV1.from_dict(valid(**{field:value}))

def test_gap_is_allowed_and_observable():
    session=str(uuid.uuid4())
    validator=FrameSequenceValidator()
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1024,sample_position=491520)))
    validator.accept(VocalFrameV1.from_dict(valid(session_id=session,sequence=1026,sample_position=492480,discontinuity=True)))
