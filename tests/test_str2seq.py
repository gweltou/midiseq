from typing import Optional, Union
import re
from midiseq import Seq, Note, Chord, Sil
from midiseq import env as env


def str2seq(string: str):
	NOTE_CHORD_PATTERN = re.compile(r"""([+-]?\d)?	# Octave transposition
										(do|re|ré|mi|fa|sol|la|si|[a-g])
										(b|\#)?		# Flat or sharp
										(M|m|\+|°)?	# Maj, min, aug, dim
										(7|9|11)?	# Seventh, ninth, eleventh
										(%[\d/.]+)?	# Time multiplication factor
										""", re.X|re.I)
	
	SILENCE_PATTERN = re.compile(r"(\.+)")

	note_value = {	'c': 0,    'do': 0,
					'd': 2,    're': 2,	'ré': 2,
					'e': 4,    'mi': 4,
					'f': 5,    'fa': 5,
					'g': 7,    'sol': 7,
					'a': 9,    'la': 9,
					'b': 11,   'si': 11}
	
	def get_octave(s: Optional[str]) -> int:
		if not s:
			return 5 # Default octave is 5
		if s[0] in ('-','+'):
			return min(max(eval('5'+s), 0), 10)
		return int(s)
	
	def parse_element(s: str) -> Union[Note, Chord, Sil]:
		match = NOTE_CHORD_PATTERN.match(s)
		if match:
			octave = get_octave(match[1])
			pitch = 12*octave + note_value[match[2]]
			pitch += 1 if s=='#' else -1 if s=='b' else 0
			is_chord = match[2][0].isupper()
			if is_chord:
				return Chord((pitch))
			else:
				return Note(pitch)
		match = SILENCE_PATTERN.match(s)
		if match:
			return Sil(len(match[0]))

	elts = []

	for s in string.split():
		if '_' in s:
			# Tuplet
			tup_notes = s.split('_')
			elts.extend(parse_element(t) for t in tup_notes)
		else:
			elts.append(parse_element(s))
		
	return sum(elts, Seq()) if len(elts) > 1 else elts[0]


def noob2seq(noob: str):
	""" https://noobnotes.net/ """

	o = env.DEFAULT_OCTAVE
	s = noob.replace('^', str(o+1)).replace('*', str(o+2)) # Octave transpose, up
	s = s.replace('.', str(o-1)).replace('_', str(o-2)) # Octave transpose, down
	s = s.replace('-', '_') # Tuplets
	s = ' '.join(s.split())
	return s.lower()


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
		"6e_6e_._6e ._6c_6e_. 6g g"
	]

	for s in seqs:
		print(s)
		print(str2seq(s))
	
	assert False


if __name__ == "__main__":
	test_full_sequences()