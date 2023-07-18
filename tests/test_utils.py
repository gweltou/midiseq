from midiseq import (
    Seq,
    pattern,
    lcm,
    rnd, rndWalk, rndGauss, rndPick,
)
from midiseq import env as env


def test_pattern():
    s = pattern("x--- x--- x--- x---", 48)
    assert s.dur == 16 * env.note_dur


def test_lcm():
    s = lcm(rnd(3), rnd(5), rnd(7))
    assert s.dur == 105 * env.note_dur