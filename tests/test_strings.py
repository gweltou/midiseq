import re
from midiseq import Seq, Note, Chord, Sil, str2elt, str2seq
# from midiseq import env as env



def test_midinotes():
	assert str2elt("48") == Note(48)
	assert str2elt("60%0.5") == Note(60, dur=0.5)
	assert str2elt("50%5") == Note(50, dur=5)


def test_single_notes():
	assert str2elt("do") == str2elt("c") == Note(48)
	assert str2elt("5do") == str2elt("5c") == Note(60)
	assert str2elt("+do") == str2elt("+1c") == Note(60)
	assert str2elt("-do") == str2elt("-1c")== Note(36)
	assert str2elt("+2do") == str2elt("+2c") == Note(72)

	assert str2elt("do#") == str2elt("c#") == Note(49)
	assert str2elt("dob") == str2elt("cb") == Note(47)

	assert str2elt("+do#") == str2elt("+c#") == Note(61)
	assert str2elt("+2do#") == str2elt("+2c#") == Note(73)
	assert str2elt("-dob") == str2elt("-cb") == Note(35)


def test_subdiv():
	def should_be_equal(s1, s2):
		assert str2seq(s1) == str2seq(s2)
	
	should_be_equal("c%0.5", "c%.5")
	should_be_equal("c%0.5", "c%1/2")
	should_be_equal("c_c_c", "c%1/3 c%1/3 c%1/3")


def test_chords():
	assert str2elt("C") == Chord(48, 52, 55)
	assert str2elt("-1Dm") == Chord(38, 41, 45)
	assert str2elt("C%0.5") == Chord(48, 52, 55, dur=0.5)
