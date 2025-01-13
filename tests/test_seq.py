from midiseq import Seq, Note, Sil, Scl, rnd
from midiseq import env as env


def test_seq_init():
    def test3notes(s):
        assert s.dur == 3 * env.note_dur
        assert len(s) == 3
    
    test3notes(Seq(1, 2, 3))
    test3notes(Seq("1 2 3"))
    test3notes(Seq(Note(1), Note(2), Note(3)))
    test3notes(Seq(1, '2', Note(3)))
    test3notes(Seq().add(Note(1)).add(Note(2)).add(Note(3)))
    test3notes(Seq().add("a b c"))
    test3notes(Seq().addNotes((1, 2, 3)))

    s = Seq("1 . 3")
    assert s.dur == 3 * env.note_dur
    assert len(s) == 2


def test_seq_operators():
    def test3notes(s):
        assert s.dur == 3 * env.note_dur
        assert len(s) == 3
    
    test3notes(Seq(1, 2) + Note(3))
    test3notes(Seq(1, 2) + Seq(3))
    test3notes(Seq(1, 2) + 3)
    test3notes(Seq(1, 2) + "3")
    test3notes(Seq("do") * 3)

    assert Seq("c d e") == Seq(48, 50, 52)
    assert Seq("c d e") != Seq(48, 50, 51)

    # add/mul
    s = Seq("do re mi fa")
    assert 2 * s == s + s
    assert s[0] == Note("do")
    assert s[-1] == Note("fa")

    # neg
    assert Seq("do re mi") == -Seq("mi re do")

    # xor (transpose)
    assert Seq(50, 52, 54)^2 == Seq(52, 54, 56)
    assert Seq(50, 52, 54)^-5 == Seq(45, 47, 49)

    # modulo (gate)
    assert (Seq(50)%0.5)[0].dur == env.note_dur * 0.5


def test_seq_reverse():
    s = Seq("do re mi")
    assert s.reverse() == Seq("mi re do")


def test_seq_shift():
    s = Seq("do re mi")
    sc = s.copy()
    assert s == sc.shift(1.0).shift(-1.0)
    s.shift(1.0)
    assert s.notes[0][0] == 1.0
    s.shift(-1.0)
    s.shift(env.note_dur, wrap=True)
    assert s == Seq("mi do re")
    s.shift(-1, wrap=True)
    assert s == Seq("do re mi")
    sc.shift(-env.note_dur, wrap=True)
    assert sc == Seq("re mi do")




def test_seq_strip():
    s = Sil() + Seq("a b c") + Sil()
    s2 = s.copy()
    assert s.dur == 5 * env.note_dur
    s.stripTail()
    assert s.dur == 4 * env.note_dur
    assert s.head == s.dur
    assert len(s) == 3
    s.stripHead()
    assert s.dur == 3 * env.note_dur
    assert s.head == s.dur
    assert len(s) == 3
    s2.strip()
    assert s2.dur == 3 * env.note_dur
    assert s2.head == s2.dur
    assert len(s2) == 3


def test_seq_scalepitch():
    scl = Scl("minor", "g")
    env.scale = scl
    s = rnd(16)
    for n in s:
        assert n.pitch in scl.notes

    s.scalePitch(0.5)
    for n in s:
        assert n.pitch in scl.notes
    
    s.scalePitch(2.0)
    for n in s:
        assert n.pitch in scl.notes


def test_merge():
    s = Seq("50 50 . 50")
    s.merge(Seq(". 60 60 ."))
    assert len(s) == 5
    s = Seq("1 2 3 4")
    s &= Seq("5 6 7 8")
    assert len(s) == 8


def test_crop():
    env.note_dur = 1/4  
    s = rnd(6)
    s.head = -0.35
    s.add(Note(66))
    assert len(s) == 7
    assert s.notes[0][0] == -0.35
    s.dur = 1
    s.crop()
    assert len(s) == 4


def test_select():
    s = Seq("8 9 10 11 12 13")
    selection = s.selectNotes(lambda x: x.pitch <= 10)
    assert len(selection) == 3


def test_index_slice():
    env.note_dur = 1/4
    s = Seq("60 61 62 63 64 65")
    assert s[0] == Note(60)
    assert len(s[0:3]) == 3
    assert len(s[:3]) == 3
    s = s[0.0:1.0]
    assert len(s) == 4
    assert s.dur == 1.0


def test_filter():
    s = Seq("60 61 62 63 64 65")
    assert(len(s.filter(lambda n: n.pitch<=62)) == 3)


def test_selectnotes():
    s = Seq("60 61 62 63 64 65")
    assert(len(s.selectNotes(lambda n: n.pitch<=62)) == 3)