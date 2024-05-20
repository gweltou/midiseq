from math import sin, pi
from random import random

from rtmidi.midiconstants import (
    CONTROL_CHANGE, PROGRAM_CHANGE,
    PITCH_BEND, MODULATION_WHEEL,
    PORTAMENTO,
)

from midiseq import Seq, pattern
from midiseq.modulation import Mod, ModSeq



def test_mod_fn():
    mod = Mod(lambda t: 0.5*sin(t*pi*2) + 0.5)
    start = 0.0
    dur = 0.5
    cc = mod.getValues(start=start, dur=dur)
    numval = int(dur / mod.cycle) + 1
    assert len(cc) == numval

    start = 0.5
    dur = 0.5
    cc = mod.getValues(start=start, dur=dur)
    numval = int(1 + dur / mod.cycle)
    assert len(cc) == numval


def test_mod_coords():
    mod = Mod([0, 1])
    cc = mod.getValues()
    assert len(cc) == int(1 + 1.0 / mod.cycle)

    s = pattern("x-x-xx-x --xxx--", "do")
    t = [(n[0], random()) for n in s.notes]
    m = Mod(t, interp=False)

    print(s)
    assert len(m.coords) == 8
    cc = m.getValues(dur=s.dur, fn_end=s.dur)
    print(cc)
    assert len(cc) == 8
    assert cc[0][0] == 0.0

    cc = m.getValues(start=1.0, dur=1.0, fn_end=s.dur)
    print(cc)
    assert len(cc) == 8
    assert cc[0][0] == 1.0



def test_mod_notes():
    s = Seq("do do do sol")

    mod = Mod([0, 1])
    s.addModNotes(mod, PITCH_BEND)