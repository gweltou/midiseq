from midiseq.generators import (
    genFunc, genPattern, genMapRhythm
)
from midiseq.utils import rnd, euclid


def test_genFunc():
    g = genFunc(rnd, n=8, lo=40, hi=60)
    for i in range(16):
        s = next(g)
        assert len(s) == 8


def test_genPattern():
    g = genPattern(rnd, pattern="ABBA")
    seqs = [s for s in g]
    assert len(seqs) == 4
    assert seqs[0] == seqs[-1]
    assert seqs[1] == seqs[2]


def test_genMapRhythm():
    m = rnd(6)
    r = euclid(48, 5, 16)
    g = genMapRhythm(m, r)
    seqs = [s for s in g]
    assert len(seqs) == 6