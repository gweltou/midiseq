from midiseq import (
    Seq,
    pattern,
    lcm,
    rnd, rndDur, rndWalk, rndGauss, rndPick,
)
from midiseq import env as env


def test_pattern():
    s = pattern("x--- x--- x--- x---", 48)
    assert s.dur == 16 * env.note_dur

    s = pattern("x-x-", "do")
    assert s[0].pitch == 48


def test_lcm():
    s = lcm(rnd(3), rnd(5), rnd(7))
    assert s.dur == 105 * env.note_dur


def test_rnddur():
    for _ in range(32): 
        s = rndDur(1.0)
        assert s.dur == 1.0
    for _ in range(32):
        s = rndDur(1.0, durs=[0.33, 0.5, 1.33])
        assert s.dur == 1.0