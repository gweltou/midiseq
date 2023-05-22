from midiseq import Seq, Note, Chord, Sil
from midiseq import env as env


def test_sil_operators():
    assert Sil(1) == Sil(2)/2
    assert Sil(2) == Sil(1) + Sil(1)
    assert Sil(2) == 2*Sil(1)

    assert type(Sil() + Note(60)) == Seq
    assert (Sil() + Note(60)).length == 2*env.NOTE_LENGTH

    assert type(Sil() + Chord((60, 62, 66))) == Seq
    assert (Sil() + Chord((60, 62, 66))).length == 2*env.NOTE_LENGTH

    assert type(Sil() + Seq((60, 62, 66))) == Seq
    assert (Sil() + Seq((60, 62, 66))).length == 4*env.NOTE_LENGTH

def test_note_operators():
    assert type(Note(60)+Note(60)) == Seq
    assert type(Note(60)+Sil()) == Seq
    assert type(Note(60)+Chord((60, 65))) == Seq
    assert (Note(60)*2).length == 2*env.NOTE_LENGTH
    assert type(Note(60)*1.5) == Note
    assert type(Note(60)*1.5).dur == 1.5*env.NOTE_LENGTH
    assert (Note(60)/2).dur == env.NOTE_LENGTH / 2

    assert (Note(60) + Seq(length=4)).length == 4 + env.NOTE_LENGTH