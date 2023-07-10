from midiseq import Seq, Note, Chord, Sil
from midiseq import env as env


def test_seq_init():
    def test3notes(s):
        assert s.length == 3 * env.NOTE_LENGTH
        assert len(s) == 3
    
    test3notes(Seq(1, 2, 3))
    test3notes(Seq("1 2 3"))
    test3notes(Seq(Note(1), Note(2), Note(3)))
    test3notes(Seq(1, '2', Note(3)))
    test3notes(Seq().add(Note(1)).add(Note(2)).add(Note(3)))
    test3notes(Seq().add("a b c"))
    test3notes(Seq().addNotes((1, 2, 3)))

    s = Seq("1 . 3")
    assert s.length == 3 * env.NOTE_LENGTH
    assert len(s) == 2


def test_seq_operators():
    def test3notes(s):
        assert s.length == 3 * env.NOTE_LENGTH
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
    assert (Seq(50)%0.5)[0].dur == env.NOTE_LENGTH * 0.5


def test_sil_operators():
    assert Sil(1) == Sil(2)/2
    assert Sil(2) == Sil(1) + Sil(1)
    assert Sil(2) == 2*Sil(1)

    assert type(Sil() + Note(60)) == Seq
    assert (Sil() + Note(60)).length == 2*env.NOTE_LENGTH

    assert type(Sil() + Chord(60, 62, 66)) == Seq
    assert (Sil() + Chord(60, 62, 66)).length == 2*env.NOTE_LENGTH

    assert type(Sil() + Seq((60, 62, 66))) == Seq
    assert (Sil() + Seq((60, 62, 66))).length == 4*env.NOTE_LENGTH


def test_seq_reverse():
    s = Seq("do re mi")
    assert s.reverse() == Seq("mi re do")


def test_seq_shift():
    s = Seq("do re mi")
    sc = s.copy()
    assert s == sc.shift(1).shift(-1)
    s.shift(1)
    assert s.notes[0][0] == 1.0
    s.shift(-1)
    s.shift(env.NOTE_LENGTH, wrap=True)
    assert s == Seq("mi do re")
    sc.shift(-env.NOTE_LENGTH, wrap=True)
    assert sc == Seq("re mi do")


def test_note_operators():
    assert type(Note(60)+Note(60)) == Seq
    assert type(Note(60)+Sil()) == Seq
    assert type(Note(60)+Chord(60, 65)) == Seq
    assert (Note(60)*2).length == 2*env.NOTE_LENGTH
    assert type(Note(60)*1.5) == Note
    assert (Note(60)*1.5).dur == 1.5*env.NOTE_LENGTH
    assert (Note(60)/2).dur == env.NOTE_LENGTH / 2

    assert (Note(60) + Seq(length=4)).length == 4 + env.NOTE_LENGTH