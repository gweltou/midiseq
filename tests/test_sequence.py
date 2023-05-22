from midiseq import Seq, Note, Chord, Sil
from midiseq import env as env


def test_sil_operators():
    assert Sil(1) == Sil(2)/2
    assert Sil(2) == Sil(1) + Sil(1)
    assert Sil(2) == 2*Sil(1)

    assert isinstance(Sil() + Note(60), Seq)
    assert (Sil() + Note(60)).length == 2*env.NOTE_LENGTH

    assert isinstance(Sil() + Chord((60, 62, 66)), Seq)
    assert (Sil() + Chord((60, 62, 66))).length == 2*env.NOTE_LENGTH

    assert isinstance(Sil() + Seq((60, 62, 66)), Seq)
    assert (Sil() + Seq((60, 62, 66))).length == 4*env.NOTE_LENGTH