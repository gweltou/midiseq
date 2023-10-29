from math import sin, pi

from rtmidi.midiconstants import (
    CONTROL_CHANGE, PROGRAM_CHANGE,
    PITCH_BEND, MODULATION_WHEEL,
    POLY_AFTERTOUCH, CHANNEL_AFTERTOUCH,
    PORTAMENTO,
)

from midiseq.modulation import Mod, ModSeq



def test_mod():
    cnt = CONTROL_CHANGE
    channel = 1
    fn = lambda t: 0.5*sin(t*pi*2) + 0.5

    mod = Mod(fn)
    start = 0.0
    dur = 0.5
    cc = mod.getValues(start=start, dur=dur)
    numval = int( (dur-start) / mod.cycle )
    assert len(cc) == numval

    start = 0.0
    end = 1.0
    cc = mod.getValues(start=start, dur=dur)
    numval = int( (dur-start) / mod.cycle )
    assert len(cc) == numval
    
    for pos, mess in cc:
        assert 0 <= mess[2] <= 127
        assert isinstance(mess[2], int)