import re
from midiseq import Seq, Note, Chord, Sil, str2seq
from midiseq import env as env



def should_be_equal(s1, s2):
		assert str2seq(s1) == str2seq(s2)


def test_chords():
	assert True


def test_subdiv():
	should_be_equal("c%0.5", "c%.5")
	should_be_equal("c%0.5", "c%1/2")
	should_be_equal("c_c_c", "c%1/3 c%1/3 c%1/3")
	

def test_full_sequences():
	seqs = [
		"a_b 6d_b 6f# 6f# 6e . a_b 6d_b 6e 6e 6d_6c#_b . a_b 6d_b 6d 6e_6c# a a_6e 6d",
		"e_e ._e ._c e_. g . -1g"
	]

	for s in seqs:
		print(s)
		print(str2seq(s))
	
	assert False


if __name__ == "__main__":
	test_full_sequences()
