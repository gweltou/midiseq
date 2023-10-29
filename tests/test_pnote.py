from midiseq import PNote


def test_pnote():
    n = PNote({"do": 1, "mi": 2})
    assert n.pdict == {48: 1/3, 52: 1.0}

    n = PNote({"do": 3, "mi": 1, "sol": 1})
    s = n * 8
    print(s)

    n = PNote(("do", "re", "mi"), dur=2)
    assert n.pdict == {48: 1/3, 50: 2/3, 52: 3/3}
