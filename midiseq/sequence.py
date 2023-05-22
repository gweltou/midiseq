from __future__ import annotations
from typing import Optional, Union
import random
import re

import midiseq.env as env


scales = {
    "chromatic":        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor":   [0, 2, 3, 5, 7, 8, 11],
    # what about the melodic minor (ascending and descending) ?
    "whole_tone":       [0, 2, 4, 6, 8, 10],
    "pentatonic":       [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "japanese":         [0, 1, 5, 7, 8],
    "zelda_ocarnia":    [0, 3, 7, 9],
}

modes = {
    "ionian":       [0, 2, 4, 5, 7, 9, 11],
    "dorian":       [0, 2, 3, 5, 7, 9, 10],
    "phrygian":     [0, 1, 3, 5, 7, 8, 10],
    "lydian":       [0, 2, 4, 6, 7, 9, 11],
    "mixolidian":   [0, 2, 4, 5, 7, 9, 10],
    "aeolian":      [0, 2, 3, 5, 7, 8, 10],
    "locrian":      [0, 1, 3, 5, 6, 8, 10],
}


# def buildScale(scale, tonic):
#     s = Seq()
#     s.scale = Scale(scale, tonic)
#     for i in range(len(s.scale) + 1):
#         s.addNote(s.scale.getDegree(i))
#     return s


def str2seq(string: str):
	NOTE_CHORD_PATTERN = re.compile(r"""([+-]?\d)?	# Octave transposition
										(do|re|ré|mi|fa|sol|la|si|[a-g])
										(b|\#)?		# Accidentals (flat or sharp)
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
			else:### Sequences

				return Note(pitch)
		match = SILENCE_PATTERN.match(s)
		if match:
			return Sil(len(match[0]))

	elts = []
	for s in string.split():
		if '_' in s:
			# Tuplet
			tup_notes = s.split('_')
			elts.extend([ parse_element(t)/len(tup_notes) for t in tup_notes ])
		else:
			# Single element
			elts.append(parse_element(s))
		
	return sum(elts, Seq()) if len(elts) > 1 else elts[0]



def noteToPitch(name):
    """ Returns the midi pitch number given a spelled note """
    
    if type(name) != str:
        raise TypeError('Argument must be a string. Ex: "do", "c#4", "60... ')

    notes = {'c': 0,    'do': 0,
             'c+': 1,   'c#': 1,    'do#': 1,
             'd': 2,    're': 2,
             'd+' : 3,  'd#' : 3,   're#': 3,
             'e': 4,    'mi': 4,
             'f': 5,    'fa': 5,
             'f+': 6,   'f#': 6,    'fa#': 6,
             'g': 7,    'sol': 7,
             'g+': 8,   'g#': 8,    'sol#': 8,
             'a': 9,    'la': 9,
             'a+': 10,  'a#': 10,   'la#': 10,
             'b': 11,   'si': 11,
             }
    p = re.compile(r'([a-z]+[#\-+]?)(\d?)', re.IGNORECASE)

    name = name.strip()
    if name.isdecimal():
        return int(name)
    
    m = p.match(name)
    if m:
        tone = m.groups()[0]
        if m.groups()[1] != '':
            oct = int(m.groups()[1])
            return 12*oct + notes[tone]
        else:
            return 12*5 + notes[tone] # Defaults to fifth octave ?
    
    return -1



def getNotesFromString(s, dur=1, vel=100, prob=1):
    """ Return a list of notes and silences from a string """
    if type(s) != str:
        raise TypeError('Argument must be a string. Ex: "do re mi" or "60 62 64"')
    
    notes = []
    for t in s.split():
        pitch = noteToPitch(t)
        if 0 < pitch < 128:
            notes.append( Note(pitch, dur, vel, prob) )
        elif pitch == 0:
            notes.append(Sil(dur))

    return notes


def noob2seq(noob: str):
	""" https://noobnotes.net/ """

	o = env.DEFAULT_OCTAVE
	s = noob.replace('^', str(o+1)).replace('*', str(o+2)) # Octave transpose, up
	s = s.replace('.', str(o-1)).replace('_', str(o-2)) # Octave transpose, down
	s = s.replace('-', '_') # Tuplets
	s = ' '.join(s.split())
	return s.lower()



class Scale():

    def __init__(self, scale="major", tonic=60):
        if type(tonic) == int:
            self.tonic = min(127, max(0, tonic))
        elif type(tonic) == str:
            self.tonic = noteToPitch(tonic)
        else:
            raise TypeError("rootnote must be a pitch number [0-127] or a valid note name")

        if type(scale) == str:
            if scale.lower() in scales:
                self.scale = scales[scale.lower()]
            elif scale.lower() in modes:
                self.scale = modes[scale.lower()]
            else:
                raise TypeError('scale "{}" is unknown'.format(scale))
        elif type(scale) == list:
            self.scale = scale
        
    
    def getClosest(self, note) -> int:
        """ Find closest note in scale given a pitch.
            Returns a corrected pitch, in range [0-127].
            Lower pitch takes precedence.
        """
        if type(note) == int:
            pitch = min(127, max(0, note))
        elif type(note) == str:
            pitch = noteToPitch(note)
        else:
            raise TypeError("Argument must be a pitch number [0-127] or a valid note name")

        octave, degree = divmod(pitch, 12)
        distances = [s-(degree-self.tonic)%12 for s in self.scale]
        min_dist = 12
        for d in distances:
            if abs(d) < abs(min_dist):
                min_dist = d
        
        return int(12 * octave + degree + min_dist)


    def getDegree(self, n) -> int:
        """ get the pitch of the n-th degree note in the current musical scale, relative to the rootnote
            Beware : degrees start at 0. The fifth degree would be n=4.
        """
        
        nth_oct, nth_degree = divmod(round(n), len(self.scale))

        if n >= 0:
            distances = self.scale
        else:  # Negative number
            distances = [ d-12 for d in self.scale]
            nth_oct += 1

        return self.tonic + 12 * nth_oct + distances[nth_degree]


    def getDegreeFrom(self, pitch, n) -> int:
        """ Returns pitch +/- n degrees in the current scale """
        oct, semi = divmod(pitch, 12)
        for i, s in enumerate(self.scale):
            if s >= semi: break
        oct_off, deg = divmod(round(n) + i, len(self.scale))
        return (oct+oct_off)*12 + self.scale[deg]
    

    def getNotes(self):
        """ Returns all midi pitches in scale """
        raise NotImplementedError


    def triad(self, degree=0, dur=1, vel=100, prob=1):
        """ Returns a triad Chord of the nth degree in the scale """
        # notes = []
        # for chord_deg in [0, 2, 4]:
        #     notes.append( self.getDegree(degree+chord_deg) )

        return Chord([self.getDegree(degree+deg) for deg in [0,2,4]],
                     dur=dur, vel=vel, prob=prob)
        # return Chord(notes, dur=dur)


    def __str__(self):
        return "{} {}".format(self.scale, self.tonic)


    def __len__(self):
        return len(self.scale)



class Note():

    def __init__(self, pitch, dur=1, vel=100, prob=1):
        if type(pitch) == str:
            pitch = noteToPitch(pitch)
        elif type(pitch) != int:
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        elif type(pitch) == int and (pitch < 0 or pitch > 127):
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        self.pitch = min(127, max(0, pitch))
        self.dur = dur * env.NOTE_LENGTH
        self.vel = vel
        self.prob = prob
    
    def copy(self) -> Note:
        n = Note(self.pitch, self.dur, self.vel, self.prob)
        n.dur = self.dur # Overrides the env note_length multiplier
        return n

    def __add__(self, other) -> Seq:
        return Seq().add(self).add(other)

    def __mul__(self, factor: Union[int, float]) -> Union[Note, Seq]:
        if isinstance(factor, int):
            # Multiply number of notes
            s = Seq()
            for _ in range(factor):
                s.add(self.copy())
            # s.length = self.dur * factor
            return s
        elif isinstance(factor, float):
            # New note with length multiplied
            n = self.copy()
            n.dur = self.dur
            return n
        else:
            raise TypeError("Can only multiply Note by an int or a float")
    
    def __rmul__(self, factor: Union[int, float]) -> Union[Note, Seq]:
        return self.__mul__(factor)
    
    def __truediv__(self, factor: Union[int, float]):
        n = self.copy()
        n.dur = self.dur / factor
        return n

    def __eq__(self, other):
        return self.pitch == other.pitch and \
               self.dur == other.dur and \
               self.vel == other.vel and \
               self.prob == other.prob


    def __str__(self):
        return "{} {} {}".format(self.pitch, self.dur, self.vel)
    
    def __repr__(self):
        args = "{}".format(self.pitch)
        if self.dur != env.NOTE_LENGTH:
            args += ",{}".format(round(self.dur, 3))
        if self.vel != 100:
            args += ",{}".format(self.vel)
        if self.prob != 1:
            args += ",{}".format(round(self.prob, 3))
        return "Note({})".format(args)



class Sil():
    """ Silence """
    
    def __init__(self, dur=1):
        self.dur = dur * env.NOTE_LENGTH
    
    def __add__(self, other) -> Union[Sil, Seq]:
        if isinstance(other, Sil):
            return Sil((self.dur + other.dur) / env.NOTE_LENGTH)
        return Seq().add(self).add(other)

    def __mul__(self, factor: Union[int, float]) -> Sil:
        return Sil(self.dur * factor / env.NOTE_LENGTH)
    
    def __rmul__(self, factor: Union[int, float]) -> Sil:
        return self.__mul__(factor)
    
    def __truediv__(self, factor: Union[int, float]) -> Sil:
        return Sil(self.dur / (factor * env.NOTE_LENGTH))

    def __eq__(self, other):
        return self.dur == other.dur

    def __repr__(self):
        return "Sil({})".format(self.dur/env.NOTE_LENGTH)



class Chord():

    def __init__(self, notes, dur=1, vel=100, prob=1):
        self.notes = []
        self.dur = dur * env.NOTE_LENGTH
        self.prob = prob
        if type(notes) == str:
            for note in getNotesFromString(notes, dur, vel, prob):
                self.notes.append(note)
        elif hasattr(notes, '__iter__'):
            for pitch in notes:
                self.notes.append(Note(pitch, dur, vel, prob))
        else:
            raise TypeError("argument `notes` must be a string or an iterable")
    
    def __add__(self, other):
        return Seq().add(self).add(other)

    def __eq__(self, other):
        return self.notes == other.notes and \
               self.dur == other.dur and \
               self.prob == other.prob

    def __repr__(self):
        return "Chord({},{},{})".format(self.notes, self.dur/env.NOTE_LENGTH, self.prob)



# class Grid():
#     """
#         General Midi drums note mapping :
#         35 Bass Drum 2
#         36 Bass Drum 1
#         37 Side Stick
#         38 Snare Drum 1 *
#         39 Hand Clap    *
#         40 Snare Drum 2 *
#         41 Low Tom 2
#         42 Closed Hi-hat *
#         43 Low Tom 1
#         44 Pedal Hi-hat
#         45 Mid Tom 2
#         46 Open Hi-hat
#         47 Mid Tom 1
#         48 High Tom 2
#         49 Crash Cymbal 1
#         50 High Tom 1
#         51 Ride Cymbal 1
#     """
    
#     def __init__(self, nsub=16, length=1):
#         self.grid = [ set() for _ in range(nsub) ]
#         self.length = length


#     #def gridRepeat(self, pattern, )

#     def repeat(self, note, div, offset=0, preserve=False):
#         """
#             Repeats a note at regular intervals

#             Parameters
#             ----------
#                 note (int/Note)
#                     midi note [0-127] or Note instance
#                 division (int)
#                     the note will be repeated every division of the grid
#                 offset (int)
#                     offset beats in grid
#                 preserve (bool)
#                     if True, will not overwrite if there's already a note registered for this beat
#         """
#         assert div > 0
#         assert offset < len(self.grid)
#         if type(note) != Note:
#             note = Note(note, 0.1)

#         i = offset
#         while i < len(self.grid):
#             if not preserve:
#                 self.grid[i].add(note.copy())
#             i += div
    

#     def clear(self):
#         self.grid = [ set() for _ in range(len(self.grid)) ]


#     def resize(self, new_size):
#         new_grid = [ set() for _ in range(new_size) ]

#         for i, col in enumerate(self.grid):
#             new_i = round(new_size * i/len(self.grid))
#             for note in col:
#                 new_grid[new_i].add(note)
        
#         self.grid = new_grid


#     def euclid(self, note, k, offset=0):
#         """ Euclidian rythm """
#         if type(note) != Note:
#             note = Note(note, dur=0.1)
#         n = len(self.grid)
#         offset = offset % n
#         onsets = [(offset+round(n*i/k))%n for i in range(k)]
#         # print(onsets)
#         for i in onsets:
#             self.grid[i].add(note.copy())

#         # grid = [ 'x' if i in onsets else '.' for i in range(n) ]
#         # print(grid)


#     def toSeq(self):
#         s = Seq()
#         s.length = self.length
#         step = self.length / len(self.grid)
#         head = 0.0
#         for col in self.grid:
#             for note in col:
#                 s.add(note, head)
#             head += step
#         return s


#     def getMidiMessages(self, channel=1):
#         return self.toSeq().getMidiMessages(channel)


#     def __str__(self):
#         s = '[ '
#         for b in [str(len(c)) if c else '.' for c in self.grid]:
#             s += b + ' '
#         s += ']'
#         return s
    

#     def __len__(self):
#         return len(self.grid)



class Seq():
    """ Sequence of notes """

    def __init__(self, notes=None, length=0):
        self.head = 0.0       # Recording head
        self.length = length  # Can be further than the end of the last note
        self.notes = []
        if notes:
            self.addNotes(notes)

    
    def copy(self) -> Seq:
        new = Seq()
        new.notes = [ (t, note.copy()) for t, note in self.notes ]
        new.length = self.length
        new.head = self.head
        # new.tonic = self.tonic
        # new.scale = self.scale
        return new
    

    def add(self, other, head=-1) -> Seq:
        """ Add notes or whole sequences starting from head position
            This will grow the sequence's length if necessary
        """
        if head >= 0:
            self.head = head
        
        if isinstance(other, Note):
            self.notes.append( (self.head, other) )
            self.head += other.dur
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        elif isinstance(other, Sil):
            self.head += other.dur
            self.length = max(self.length, self.head)
        elif isinstance(other, Chord):
            for note in other.notes:
                self.notes.append( (self.head, note) )
            self.head += other.dur
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        elif isinstance(other, Seq):
            for (t, note) in other.notes:
                self.notes.append( (self.head + t, note) )
            self.head += other.length
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        else:
            raise TypeError("Only instances of Note, Sil, Chord or Seq can be added to a Sequence")
        return self
    

    def addNotes(self, notes, dur=1, vel=100):
        """ Add notes sequencially

            Parameters
            ----------
                notes : str/list/tuple
                    A list of note pitches, can be a string or an iterable
                    Ex: "c# d f2 do re mi" or (61, 62, 29, 60, 62, 64)
                    If the value 0 is given in place of a pitch it will be treated as a silence

        """
        if type(notes) == str:
            for note in getNotesFromString(notes, dur, vel):
                self.add(note)
        elif hasattr(notes, '__iter__'):
            for pitch in notes:
                if type(pitch) in (tuple, list):
                    self.addNotes(pitch, dur/len(pitch), vel)
                elif pitch == 0:
                    self.add(Sil(dur))
                else:
                    self.add(Note(pitch, dur, vel))
        else:
            raise TypeError("argument `notes` must be a string or an iterable")


    def merge(self, other) -> Seq:
        """ Merge sequences, preserving every note's time position
            Modify this sequence in place
            Doesn't change this Sequence's length
        """
        if type(other) != type(self):
            raise TypeError("Can only merge other Sequences")
        for data in other.notes:
            self.notes.append(data)
        self.notes.sort(key=lambda x: x[0])
        return self


    def randPick(self, n=4) -> Seq:
        """ Pick randomly among previous notes in sequence """
        new_notes = []
        for _ in range(4):
            new_notes.append(random.choice(self.notes)[1])
        for note in new_notes:
            self.add(note)
        return self
    

    def euclid(self, note=36, n=4, grid=16, offset=0) -> Seq:
        """ Generate a Euclidian rythm sequence

            Parameters
            ----------
                n : int
                    Number of notes to generate
                grid : int
                    Size of the grid (should be bigger than `n`)
                offset : int
                    Number of rests before first note
        """
        if type(note) != Note:
            note = Note(note)
        
        offset = offset % grid
        onsets = [ (offset+round(grid*i/n)) % grid for i in range(n) ]
        for i in onsets:
            t = i * env.NOTE_LENGTH
            self.notes.append( (t, note.copy()) )
        self.notes.sort(key=lambda x: x[0])
        self.head += grid * env.NOTE_LENGTH
        return self


    def replacePitch(self, old, new) -> Seq:
        """ Replace notes with given pitch to a new pitch
            Modifies sequence in-place
        """
        if type(old) == str:
            old = noteToPitch(old)
        if type(new) == str:
            new = noteToPitch(new)
        for note in self.notes:
            if note.pitch == old:
                note.pitch == new
        return self


    def map(self, grid, duty_cycle=0.2) -> Seq:
        # XXX: Not usefull right now
        beat_len = (self.length - self.head) / len(grid)
        note_dur = duty_cycle * beat_len
        for pitch in grid:
            if 0 < pitch <= 127:
                self.add(Note(pitch, note_dur))
                self.head += beat_len - note_dur
            else:
                self.head += beat_len
        return self


    def stretch(self, factor, stretch_notes_dur=True) -> Seq:
        """ Stretch sequence in time (modify sequence in place)
            Modifies sequence in-place
        """
        for i in range(len(self.notes)):
            t, note = self.notes[i]
            if stretch_notes_dur:
                note.dur *= factor
            self.notes[i] = t * factor, note
        self.length *= factor
        return self


    def transpose(self, semitones: int) -> Seq:
        """ Transpose all notes in sequence by semitones
            Modifies sequence in-place
        """
        for _, note in self.notes:
            note.pitch += semitones
        return self


    def expandPitch(self, factor: float) -> Seq:
        """ Expand or compress notes pitches around the mean value of the whole sequence
            Modifies sequence in-place
        """
        sum = 0
        for _, note in self.notes:
            sum += note.pitch
        mean = sum / len(self.notes)

        for _, note in self.notes:
            diff = note.pitch - mean
            note.pitch = round(mean + diff * factor)
            note.pitch = min(255, max(0, note.pitch))
        return self
    

    def splitNotes(self, n=2) -> Seq:
        """ Modifies sequence in-place """
        if type(n) != int or n <= 0:
            raise TypeError("number of splits should be equal to 2 or greater ")
        
        orig = self.notes[:]
        self.clear()
        for t, note in orig:
            split_dur = note.dur / n
            for i in range(n):
                self.notes.append( (t + i * split_dur, Note(note.pitch, split_dur, note.vel, note.prob)) )
        return self


    def decimate(self, prob=0.2) -> Seq:
        """ Erase notes randomly based on the given probability
            Modifies sequence in-place
        """
        orig = self.notes[:]
        self.clear()
        for t, note in orig:
            if random.random() > prob:
                self.notes.append( (t, note) )
        return self
    

    def humanize(self, tfactor=0.02, veldev=10) -> Seq:
        """ Randomly changes the notes time and duration
            Modifies sequence in-place

            Parameters
            ----------
                tfactor : 0.0 < float < 1.0
                    variation en note temporal position
                veldev : float
                    velocity standard deviation
        """
        new_notes = []
        for t, note in self.notes:
            t = t + 2 * (random.random()-0.5) * tfactor
            note.dur = note.dur + random.random() * tfactor
            note.vel = int(100 + random.gauss(0, veldev))
            note.vel = min(127, max(0, note.vel))
            new_notes.append( (t, note) )
        self.notes = new_notes
        return self


    def clear(self):
        self.notes.clear()
        self.head = 0.0


    def crop(self) -> Seq:
        """ Shorten or delete notes before time 0 and after the sequence's length
            Modifies sequence in-place
        """
        cropped_notes = []
        for t, n in self.notes:
            if t + n.dur > 0 and t < self.length:
                if t < 0:
                    n.dur += t
                elif t + n.dur > self.length:
                    n.dur -= t + n.dur - self.length
                t = (min(max(t, 0), self.length))
                cropped_notes.append( (t, n) )
            self.notes = cropped_notes
        return self


    def shift(self, dt, wrap=False) -> Seq:
        """ Shift note onset times by a given delta time
            Modifies sequence in-place.

            Parameters
            ----------
                wrap : bool
                    if True, notes that were pushed out of the sequence get appendend to the other side
        """
        new_notes = []
        for t, n in self.notes:
            new_notes.append( (t+dt, n) )
        self.notes = new_notes
        return self


    def getMidiMessages(self, channel=0):
        """
            Parameters
            ----------
                channel : int
                    Midi channel [0-15]
        """
        midi_seq = []
        for pos, note in self.notes:
            # End of sequence
            if pos >= self.length:
                break
            # Truncate last note if necesary
            if pos + note.dur > self.length:
                note = note.copy()
                note.dur = self.length - pos

            # Probability
            if note.prob < 1 and random.random() > note.prob:
                continue
            
            # pitch = self.getClosestNoteInScale(note.pitch)

            # note_on = Message.noteOn(channel, note.pitch, note.vel)
            # note_off = Message.noteOff(channel, note.pitch)
            note_on = [0x90+channel, note.pitch, note.vel]
            note_off = [0x80+channel, note.pitch, 0]
            midi_seq.append( (pos, note_on) )
            midi_seq.append( (pos + note.dur, note_off) )

        midi_seq.sort(key=lambda x: x[0])
        return midi_seq
    

    def selectNotes(self, key_fn):
        """ Return a list of notes selected by key_fn
            Notes will be selected if key_fn returns True on them

            Parameters
            ----------
                key_fn : lambda function
            
            Returns
            -------
                A list of Notes
        """
        selection = [n for _, n in self.notes if key_fn(n)]
        return selection


    def filter(self, key_fn) -> Seq:
        """ Return copy of the sequence with notes filtered by key_fn
            Notes will be kept if key_fn returns True on them

            Parameters
            ----------
                key_fn : lambda function
            
            Returns
            -------
                A filtered Sequence
        """
        new_seq = self.copy()
        new_seq.notes = [(t, n) for t, n in self.notes if key_fn(n)]
        return new_seq


    def __and__(self, other) -> Seq:
        new = self.copy()
        new.merge(other)
        return new


    def __add__(self, other) -> Seq:
        if not type(other) in (type(self), Note, Sil, Chord):
            raise TypeError("Only Note, Sil, Chord and other Seq can be added to sequences")
        
        new_seq = self.copy()
        new_seq.add(other)
        return new_seq
    

    def __mul__(self, n) -> Seq:
        if type(n) == float:
            new_sequence = self.copy()
            new_sequence.stretch(n)
            return new_sequence
        elif type(n) == int and n >= 0:
            new_sequence = self.copy()
            new_sequence.clear()
            new_sequence.length = 0
            for _ in range(n):
                new_sequence.add(self)
            
            return new_sequence
        else: raise TypeError

    
    def __rshift__(self, other) -> Seq:
        if isinstance(other, float):
            copy = self.copy()
            copy.shift(other)
            return copy

    def __lshift__(self, other) -> Seq:
        if isinstance(other, float):
            return self.__rshift__(-other)
    

    def __setitem__(self, index, newvalue):
        if type(newvalue) is Note:
            self.notes[index][1] = newvalue
        elif type(newvalue) is int:
            self.notes[index][1].pitch = newvalue
        elif type(newvalue) is tuple:
            num = len(newvalue)
            dur = self.notes[index][1].dur / num
            t = self.notes[index][0]
            del self.notes[index]
            for n in newvalue:
                new_note = Note(n)
                new_note.dur = dur
                self.notes.append((t, new_note))
                t += dur
            self.notes.sort(key=lambda x: x[0]) 

    def __getitem__(self, index):
        if type(index) is int:
            return self.notes[index][1]
        if type(index) is slice:
            start = index.start
            stop = index.stop
            if type(start) is float or type(stop) is float:
                if start == None: start = 0.0
                if stop == None: stop = self.length
                l = stop-start
                assert l > 0.0
                new_seq = Seq()
                for t,n in self.notes:
                    if t + n.dur >= start and t < stop:
                        new_seq.notes.append( (t-start, n) )
                new_seq.length = l
                new_seq.crop()
                return new_seq
            else:
                new_seq = Seq()
                if start == None: start = 0
                offset = self.notes[start][0]
                new_seq.notes = [(t-offset, n.copy()) for t,n in self.notes[index]]
                new_seq.length = new_seq.notes[-1][0] + new_seq.notes[-1][1].dur
                return new_seq
    
    def __delitem__(self, index):
        del self.notes[index]
    
    def __len__(self):
        return len(self.notes)

    def __str__(self):
        return str(self.notes)
    
    def __repr__(self):
        return str(self)    



# Sequence building functions

def rand(n=4, min=36, max=96, scale:Scale=None) -> Seq:
    """ Generate a sequence of random notes

        Parameters
        ----------
            n : int
                Number of notes to generate
            min : int
                Minimum midi pitch boundary
            max : int
                Maximum midi pitch boundary
            scale : Scale
                Constrain generated notes to the given scale
    """
    seq = Seq()
    for _ in range(n):
        pitch = random.randint(min, max)
        if scale:
            pitch = env.SCALE.getClosest(pitch)
        elif type(env.SCALE) is Scale:
            pitch = env.SCALE.getClosest(pitch)
        seq.add(Note(pitch))
    return seq


def randWalk(n=4, start=60, steps=[-3,-2,-1,0,1,2,3], skip_first=False, scale:Scale=None) -> Seq:
    """ Create a sequence of notes moving from last note by a random interval

        Parameters
        ----------
            n : int
                Number of notes to generate
            start : int or str
                Starting note of the sequence
            steps : list of int
                Possible intervals to step from last note
            skip_first:
                Skip starting note
            scale : Scale
                Constrain generated notes to the given scale
    """
    if type(start) is str:
        start = noteToPitch(start)
    pitch = start
    if not scale:
        scale = env.SCALE
    if skip_first:
        pitch = scale.getDegreeFrom(pitch, random.choice(steps))
    seq = Seq()
    for _ in range(n):
        seq.add(Note(pitch))
        pitch = env.SCALE.getDegreeFrom(pitch, random.choice(steps))
    return seq


def randGauss(n=4, mean=60, dev=3, scale:Scale=None) -> Seq:
    """ Generate random notes with a normal distribution around a mean value

        Parameters
        ----------
            n : int
                Number of notes to generate
            mean : int
                Mean pitch value
            dev : float
                Standard deviation
    """
    if not scale:
        scale = env.SCALE
    seq = Seq()
    for _ in range(n):
        if type(scale) is Scale:
            pitch = scale.getDegreeFrom(mean, round(random.gauss(0, dev)))
        else:
            pitch = round(random.gauss(mean, dev))
        seq.add(Note(pitch))
    return seq



class Track():
    """ Track where you can add Sequence.
        You can had a silence by adding an empty Sequence with a non-zero length.
        You can define a generator callback function by modifing the generator property.

        Parameters
        ----------
            channel : int
                Midi channel [0-15]
    """

    # We should define different types of looping:
    # Looping from the start or looping the last sequence/generator 

    def __init__(self, channel=0):
        self.midiport = None
        self.channel = channel
        self.instrument = None
        self.gen_func =  None
        self.gen_args = None
        self.generator = None
        self.seqs = []
        self.loop = False
        self.reset()
    

    def add(self, sequence):
        self.seqs.append(sequence)
        self.ended = False
    

    def clear(self):
        self.seqs.clear()
        self.seq_i = 0
        self.ended = True
        self.gen_func = None
        self.generator = None
        self.gen_args = None
    
    
    def reset(self, offset=0.0):
        self._next_timer = offset
        self.ended = False
        self.seq_i = 0
        if callable(self.gen_func):
            if self.gen_args:
                self.generator = self.gen_func(*self.gen_args)
            else:
                self.generator = self.gen_func()


    def update(self, timedelta):
        """ Returns MidiMessages when a new sequence just started """
        #TODO: write a function "next" or something instead

        if self.ended:
            return
        self._next_timer -= timedelta

        if self.seq_i < len(self.seqs) and self._next_timer <= 0.0:
            # Send next sequence
            i = self.seq_i
            self.seq_i += 1
            messages = self.seqs[i].getMidiMessages(self.channel)
            messages = [ (t+self._next_timer, mess) for t, mess in messages ]
            self._next_timer += self.seqs[i].length
            return messages

        elif self.seq_i == len(self.seqs) and self._next_timer <= 0.0:
            #TODO: allow looping for finished generators
            if self.generator:
                try:
                    new_seq = next(self.generator)
                    self._next_timer += new_seq.length
                    return new_seq.getMidiMessages(self.channel)
                except StopIteration:
                    if self.loop:
                        self.reset()
                    else:
                        self.ended = True
            elif self.loop:
                self.reset(self._next_timer)
            else:
                self.ended = True




class Song():

    def __init__(self):
        self.tempo = 120
        self.time_signature = (4, 4)
        self.tracks = []