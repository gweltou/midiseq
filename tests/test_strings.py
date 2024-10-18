import re
from midiseq import Seq, Note, Chord, Sil, Scl
from midiseq.elements import parse_element, parse
from midiseq import env as env



def test_midinotes():
	assert parse_element("48") == Note(48)
	assert parse_element("60%0.5") == Note(60, dur=0.5)
	assert parse_element("50%5") == Note(50, dur=5)


def test_single_notes():
	assert parse_element("do") == parse_element("c") == Note(48)
	assert parse_element("5do") == parse_element("5c") == Note(60)
	assert parse_element("+do") == parse_element("+1c") == Note(60)
	assert parse_element("-do") == parse_element("-1c")== Note(36)
	assert parse_element("+2do") == parse_element("+2c") == Note(72)

	assert parse_element("do#") == parse_element("c#") == Note(49)
	assert parse_element("dob") == parse_element("cb") == Note(47)

	assert parse_element("+do#") == parse_element("+c#") == Note(61)
	assert parse_element("+2do#") == parse_element("+2c#") == Note(73)
	assert parse_element("-dob") == parse_element("-cb") == Note(35)


def test_roman_degree():
	env.scale = Scl("major", "c")
	assert parse_element("i") == Note(48)
	assert parse_element("III") == Chord(52, 55, 59)
	assert parse_element("-V") == Chord(43, 47, 50)


def test_subdiv():
	def should_be_equal(s1, s2):
		assert parse(s1)[0] == parse(s2)[0]
	
	should_be_equal("c%0.5", "c%.5")
	should_be_equal("c%0.5", "c%1/2")
	should_be_equal("c_c_c", "c%1/3 c%1/3 c%1/3")


def test_chords():
	assert parse_element("C") == Chord(48, 52, 55)
	assert parse_element("-1Dm") == Chord(38, 41, 45)
	assert parse_element("C%0.5") == Chord("48%.5 52%.5 55%.5", dur=1.0) # New behaviour