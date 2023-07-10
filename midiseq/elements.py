from __future__ import annotations
from typing import Optional, Union, List, Tuple, Generator
import random
import re

import midiseq.env as env
from .definitions import scales, modes



_NOTE_CHORD_PATTERN = re.compile(r"""([+-]?\d?)?	# Octave transposition
                                    (do|re|ré|mi|fa|sol|la|si|ti|[a-g])
                                    (b|\#)?		# Accidentals (flat or sharp)
                                    (M|m|mM|\+|°|sus2|sus4)? # Maj, min, min/Maj, aug,...
                                    (7|9|11)?	# Seventh, ninth, eleventh
                                    (%[\d/.]+)?	# Time multiplication factor
                                    """, re.X|re.I)


def str2pitch(tone: str) -> int:
    """ Returns the midi pitch number given a spelled note """
    
    if not isinstance(tone, str):
        raise TypeError("Argument must be a string. Ex: 'do', '4c#', '60',...")

    tone = tone.strip()
    if tone.isdecimal():
        return int(tone)

    note_value = {  'c': 0,    'do': 0,
                    'd': 2,    're': 2,	'ré': 2,
                    'e': 4,    'mi': 4,
                    'f': 5,    'fa': 5,
                    'g': 7,    'sol': 7,
                    'a': 9,    'la': 9,
                    'b': 11,   'si': 11}

    def get_octave(s: Optional[str]) -> int:
        if not s:
            return env.DEFAULT_OCTAVE
        if s[0] in ('-','+'):
            if len(s) == 1:
                s += '1'
            octave = eval(str(env.DEFAULT_OCTAVE) + s)
            return min(max(octave, 0), 10)
        return int(s)
    
    match = _NOTE_CHORD_PATTERN.match(tone)
    if match:
        # match = match.groups(default='')
        octave = get_octave(match[1])
        pitch = 12*octave + note_value[match[2].lower()]
        pitch += 1 if match[3]=='#' else -1 if match[3]=='b' else 0
        return pitch
    
    return -1



def str2elt(string: str) -> Union[Note, Sil, Chord, None]:
    """ Return an single musical element, given its string representation """

    MIDI_PITCH_PATTERN = re.compile(r"(\d+)(%[\d/.]+)?")

    SILENCE_PATTERN = re.compile(r"(\.+)")

    intervals = {   'M': (0, 4, 7), '': (0, 4, 7), # Major
                    'm': (0, 3, 7), # Minor
                    '+': (0, 4, 9), # Augmented
                    '°': (0, 3, 6), # Diminished
                    'sus2':(0, 2, 7), # Suspended second
                    'sus4':(0, 5, 7), # Suspended fourth
                    '7': (0, 4, 7, 10), # Dominant seventh
                    'M7':(0, 4, 7, 11), # Major seventh
                    'm7':(0, 3, 7, 10), # Minor seventh
                    'mM7':(0, 3, 7, 11),# Minor/Major seventh
                    '°7':(0, 3, 6, 9),   # Diminished seventh
                }

    match = MIDI_PITCH_PATTERN.fullmatch(string)
    if match:
        pitch = int(match[1])
        dur = 1 if not match[2] else eval(match[2][1:])
        return Note(pitch, dur=dur)

    match = _NOTE_CHORD_PATTERN.fullmatch(string)
    if match:
        pitch = str2pitch(string) # XXX: the re gets executed twice...
        is_chord = match[2][0].isupper()
        dur = 1 if not match[6] else eval(match[6][1:])
        if is_chord:
            chord_type = (match[4] or '') + (match[5] or '')
            pitches = ( pitch + i for i in intervals[chord_type] )
            return Chord(*pitches, dur=dur)
        else:
            return Note(pitch, dur=dur)
    
    match = SILENCE_PATTERN.fullmatch(string)
    if match:
        return Sil(len(match[0]))
    
    raise TypeError("Unrecognized element: '{}'".format(string))



def str2seq(string: str) -> Seq:
    """ Return a Sequence, given its string representation """

    elts = []
    for elt in string.split():
        if '_' in elt:
            # Tuplet
            tup_notes = elt.split('_')
            elts.extend([ str2elt(t)/len(tup_notes) for t in tup_notes ])
        else:
            # Single element
            elts.append(str2elt(elt))
    
    return sum(elts, Seq())




# def buildScale(scale, tonic):
#     s = Seq()
#     s.scale = Scale(scale, tonic)
#     for i in range(len(s.scale) + 1):
#         s.addNote(s.scale.getDegree(i))
#     return s


class Scale():

    def __init__(self, scale="major", tonic=60):
        if isinstance(tonic, int):
            self.tonic = min(127, max(0, tonic))
        elif isinstance(tonic, str):
            self.tonic = str2pitch(tonic)
        else:
            raise TypeError("rootnote must be a pitch number [0-127] or a valid note name")

        if isinstance(scale, str):
            if scale.lower() in scales:
                self.scale = scales[scale.lower()]
                self.scale_name = scale.lower()
            elif scale.lower() in modes:
                self.scale = modes[scale.lower()]
                self.scale_name = scale.lower()
            else:
                raise TypeError('scale "{}" is unknown'.format(scale))
        elif isinstance(scale, list):
            self.scale = scale
            self.scale_name = str(scale)
        self.notes = self._getNotes()
        
    
    def getClosest(self, note: Union[str, int]) -> int:
        """ Find closest note in scale given a pitch
            Returns a corrected pitch, in range [0-127]
            If the correct pitch is right in the middle, lower pitch takes precedence
        """
        if type(note) == int:
            pitch = min(127, max(0, note))
        elif type(note) == str:
            pitch = str2pitch(note)
        else:
            raise TypeError("Argument must be a pitch number [0-127] or a valid note name")

        octave, degree = divmod(pitch, 12)
        distances = [s-(degree-self.tonic)%12 for s in self.scale]
        min_dist = 12
        for d in distances:
            if abs(d) < abs(min_dist):
                min_dist = d
        
        return int(12 * octave + degree + min_dist)


    def getDegree(self, n: int) -> int:
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


    def getDegreeFrom(self, pitch: Union[str, int], n: int) -> int:
        """ Returns pitch +/- n degrees in the current scale """
        if isinstance(pitch, str):
            pitch = str2pitch(pitch)
        
        for i, p in enumerate(self.notes):
            if p == pitch:
                # Pitch is in scale
                idx = i
                break
            if p > pitch:
                # Find closest between prev an next
                d_prev = pitch - self.notes[i-1]
                d_next = p - pitch
                if d_prev <= d_next:
                    idx = i-1
                idx = i
                break
        return self.notes[idx+n]

 

    def _getNotes(self):
        """ Returns all midi pitches in scale """
        pitches = []
        smallest_tonic = self.tonic % 12
        for oct in range(-1, 11):
            for d in self.scale:
                pitch = oct*12 + smallest_tonic + d
                if 0 <= pitch < 128:
                    pitches.append(pitch)
        return pitches


    def triad(self, degree=0, dur=1, vel=100, prob=1):
        """ Returns a triad Chord of the nth degree in the scale """
        return Chord([self.getDegree(degree+deg) for deg in [0,2,4]],
                     dur=dur, vel=vel, prob=prob)


    def __str__(self):
        return "{} {}".format(self.scale, self.tonic)
    
    def __repr__(self):
        scale_name = f"'{self.scale_name}'" if isinstance(self.scale_name, str) else self.scale_name
        return f"Scale({scale_name}, {self.tonic})"

    def __len__(self):
        return len(self.scale)



class Note():

    def __init__(self, pitch, dur=1, vel=100, prob=1):
        if isinstance(pitch, str):
            pitch = str2pitch(pitch)
        elif isinstance(pitch, int) and (pitch < 0 or pitch > 127):
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        elif not isinstance(pitch, int):
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
            # New note with dur multiplied
            n = self.copy()
            n.dur = self.dur * factor
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
            args += ",{}".format(round(self.dur/env.NOTE_LENGTH, 3))
        if self.vel != 100:
            args += ",{}".format(self.vel)
        if self.prob != 1:
            args += ",{}".format(round(self.prob, 3))
        return "Note({})".format(args)



class Sil():
    """ Silence (non-mutable) """
    
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
    """ Chords are made of many notes playing at the same time """

    def __init__(self, *notes, dur=1, vel=100, prob=1):
        # XXX: prob parameter is not really used for now
        # XXX: vel parameter is not really used for now
        self.notes = []
        self.pitches = set() # Helps to avoid duplicate notes
        self.dur = dur * env.NOTE_LENGTH
        self.prob = prob

        for elt in notes:
            if isinstance(elt, int) and elt not in self.pitches:
                self.notes.append(Note(elt, dur, vel))
                self.pitches.add(elt)
            elif isinstance(elt, Note) and elt.pitch not in self.pitches:
                new_note = elt.copy()
                new_note.dur = min(new_note.dur, self.dur)
                self.notes.append(new_note)
                self.pitches.add(new_note.pitch)
            elif isinstance(elt, str):
                self._parse_string(elt)
            elif isinstance(elt, Chord):
                self._merge_chord(elt)
            else:
                raise TypeError("Argument `notes` must be Notes, strings or integers")
    

    def arp(self, type="up", times=1, octaves=1) -> Seq:
        arp_seq = Seq()
        if type == "up":
            for oct in range(octaves):
                for n in sorted(self.notes, key=lambda n: n.pitch):
                    new_note = n.copy()
                    new_note.pitch += 12*oct
                    arp_seq.add(new_note)
        return arp_seq


    def _parse_string(self, string: str) -> None:
        for elt in string.split():
            elt = str2elt(elt)
            if isinstance(elt, Note) and elt.pitch not in self.pitches:
                elt.dur = min(elt.dur, self.dur)
                self.notes.append(elt)
                self.pitches.add(elt.pitch)
            elif isinstance(elt, Chord):
                self._merge_chord(elt)
            else:
                raise TypeError("Unrecognized element : {}".format(elt))
    

    def _merge_chord(self, other: Chord) -> None:
        for note in other.notes:
            if note.pitch not in self.pitches:
                new_note = note.copy()
                new_note.dur = min(new_note.dur, self.dur)
                self.notes.append(new_note)
                self.pitches.add(new_note.pitch)


    def __add__(self, other):
        return Seq().add(self).add(other)

    def __eq__(self, other):
        return self.notes == other.notes and \
               self.dur == other.dur and \
               self.prob == other.prob

    def __repr__(self):
        if self.dur != env.NOTE_LENGTH:
            return "Chord({})".format(', '.join( [str(n.pitch) for n in self.notes] ))
        return "Chord({}, dur={})".format(
                ', '.join( [str(n.pitch) for n in self.notes] ),
                self.dur / env.NOTE_LENGTH
                )



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

    def __init__(self, *notes, length=0):
        self.head = 0.0       # Recording head
        self.length = length  # Can be further than the end of the last note
        self.notes: List[Tuple[float, Note]] = []
        self.silences = []  # Keep a record of silence, used for random picking
                            # so no need to sort it
        for elt in notes:
            if isinstance(elt, int):
                self.add(Note(elt))
            elif type(elt) in (Note, Sil, Chord, Seq, str):
                self.add(elt)
            elif isinstance(elt, str) or hasattr(elt, '__iter__'):
                self.addNotes(elt)
            else:
                raise TypeError

    
    def copy(self) -> Seq:
        new = Seq()
        new.notes = [ (t, n.copy()) for t, n in self.notes ]
        new.silences = [ (t, s) for t, s in self.silences ]
        new.length = self.length
        new.head = self.head
        return new
    

    def add(self, other, head=-1) -> Seq:
        """ Add a single musical element or whole sequences at the recording head position
            This will grow the sequence's length if necessary
        """
        if head >= 0:
            self.head = head
        
        if isinstance(other, int):
            self.add(Note(other))
        elif isinstance(other, str):
            self.add(str2seq(other))
        elif isinstance(other, Note):
            self.notes.append( (self.head, other.copy()) )
            self.head += other.dur
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        elif isinstance(other, Sil):
            self.silences.append( (self.head, other) )
            self.head += other.dur
            self.length = max(self.length, self.head)
        elif isinstance(other, Chord):
            for note in other.notes:
                self.notes.append( (self.head, note.copy()) )
            self.head += other.dur
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        elif isinstance(other, Seq):
            for (t, note) in other.notes:
                self.notes.append( (self.head + t, note.copy()) )
            for (t, sil) in other.silences:
                self.silences.append( (self.head + t, sil) )
            self.head += other.length
            self.length = max(self.length, self.head)
            self.notes.sort(key=lambda x: x[0])
        else:
            raise TypeError("Only instances of Note, Sil, Chord, Seq or string sequences can be added to a Sequence")
        return self
    

    def addNotes(self, notes, dur=1, vel=100):
        # XXX: maybe do without this method altogether
        """ Add notes sequencially from a string sequence or an iterable.
            If an iterable is given, it can contain sub-lists,
            which will subdivide the time

            Parameters
            ----------
                notes : str/list/tuple
                    A list of note pitches, can be a string or an iterable
                    Ex: "c# d f2 do re mi" or (61, 62, 29, 60, 62, 64)
        """
        if isinstance(notes, str):
            self.add(str2seq(notes))
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
        return self


    def merge(self, other) -> Seq:
        """ Merge sequences, preserving every note's time position
            Modify this sequence in place
            Doesn't change this Sequence's length
        """
        if type(other) != type(self):
            raise TypeError("Can only merge other Sequences")
        for t, n in other.notes:
            self.notes.append( (t, n.copy()) )
        for t, s in other.silences:
            self.silences.append( (t, s) )
        self.notes.sort(key=lambda x: x[0])
        return self


    def replacePitch(self, old, new) -> Seq:
        """ Replace notes with given pitch to a new pitch
            Modifies sequence in-place
        """
        # TODO: `all_octaves` option
        if type(old) == str:
            old = str2pitch(old)
        if type(new) == str:
            new = str2pitch(new)
        for note in self.notes:
            if note.pitch == old:
                note.pitch == new
        return self


    def stretch(self, factor, stretch_notes=True) -> Seq:
        """ Stretch sequence in time (modify sequence in place)
            Modifies sequence in-place
        """
        for i in range(len(self.notes)):
            t, note = self.notes[i]
            if stretch_notes:
                note.dur *= factor
            self.notes[i] = t * factor, note
        self.length *= factor
        return self


    def reverse(self) -> Seq:
        """ Reverse notes order
        """
        new_notes = []
        for t, n in self.notes:
            new_notes.append( (self.length - t - n.dur, n) )
        self.notes = sorted(new_notes)
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
        """ Randomly offsets the notes time and duration
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
        """ Shift note onset times by a given *absolute* delta time
            Modifies sequence in-place.

            Parameters
            ----------
                wrap : bool
                    if True, notes that were pushed out of the sequence get appendend to the other side
        """
        new_notes = []
        for t, n in self.notes:
            new_time = t+dt
            if wrap:
                if t+dt >= self.length:
                    new_time -= self.length
                elif t+dt < 0:
                    new_time += self.length
            new_notes.append( (new_time, n) )
        self.notes = sorted(new_notes)
        return self
    

    def shuffle(self):
        """ Shuffle the sequence """


    def getMidiMessages(self, channel=0) -> List[tuple]:
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
        new_seq = self.copy()
        new_seq.add(other)
        return new_seq
    
    def __mul__(self, factor: Union[int, float]) -> Seq:
        if type(factor) == float:
            new_sequence = self.copy()
            new_sequence.stretch(factor)
            return new_sequence
        elif type(factor) == int and factor >= 0:
            new_sequence = self.copy()
            new_sequence.clear()
            new_sequence.length = 0
            for _ in range(factor):
                new_sequence.add(self)
            
            return new_sequence
        else: raise TypeError
    
    def __rmul__(self, factor: Union[int, float]) -> Seq:
        return self.__mul__(factor)
    
    def __truediv__(self, factor: Union[int, float]):
        new_sequence = self.copy()
        new_sequence.stretch(1/factor)
        return new_sequence
    
    def __rshift__(self, other) -> Seq:
        if isinstance(other, float):
            copy = self.copy()
            copy.shift(other)
            return copy

    def __lshift__(self, other) -> Seq:
        if isinstance(other, float):
            return self.__rshift__(-other)
    
    def __mod__(self, factor: float) -> Seq:
        copy = self.copy()
        for _, n in copy.notes:
            n.dur *= factor
        return copy
    
    def __neg__(self):
        """ Reverse sequence """
        return self.copy().reverse()
    
    def __xor__(self, semitones):
        """ Transpose sequence in semitones """
        return self.copy().transpose(semitones)

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
    
    # def __lt__(self, other):
    #     return self.length < other.length
    
    def __eq__(self, other):
        return (
            self.length == other.length
                and self.notes == other.notes
        )

    def __str__(self):
        return str(self.notes)
    
    def __repr__(self):
        return str(self)    



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

    #_all_tracks = set() # All instanciated tracks
    #_priority_list = [] # Class variable to synchronize update order
    #_top_priority = []  # list of tracks to update first

    def __init__(self,
                channel=0, instrument=None,
                name=None, loop=True,
                sync_from: Optional[Track] = None
                ):
        self.port = None
        self.channel = channel
        self.instrument = instrument
        # self.gen_func =  None
        # self.gen_args = None
        # self.generator = None
        self.seqs: List[Union[Seq, Generator]] = []
        self.muted = False
        self.loop = loop
        self.loop_type = "last" # "last" / "all"
        self.shuffle = False    # Not Implemented
        self.name = name #or f"Track{len(Track._all_tracks)+1}"
        self.ended = True
        self.offset = 0.0
        self.send_program_change = True
        #self.reset()

        self._sync_children: List[Track] = []
        self._sync_from: Optional[Track] = sync_from
        if sync_from != None:
            sync_from._sync_children.append(self)
        # if self._sync_from != None and:
        #     self._build_sync_priority_list()
    

    def add(self, sequence: Union[Seq, str, Generator]) -> Track:
        if isinstance(sequence, str):
            sequence = str2elt(sequence)
        self.seqs.append(sequence)
        return self


    def clear(self):
        self.seqs.clear()
        self.seq_i = 0
        self.ended = True
        # self.gen_func = None
        # self.generator = None
        # self.gen_args = None
    
    
    def reset(self):
        if not self.seqs:
            return
        
        self._next_timer = self.offset
        self.ended = False
        self.seq_i = 0
        # self.signal_sequence_end = True
        # if callable(self.gen_func):
        #     if self.gen_args:
        #         self.generator = self.gen_func(*self.gen_args)
        #     else:
        #         self.generator = self.gen_func()


    def setGroup(self, track_group):
        self._sync_group = track_group
        for t in self._sync_children:
            t.setGroup(track_group)

    def syncFrom(self, other: Track) -> None:
        self._sync_from = other
    
    def _sync(self) -> None:
        if not self.seqs:
            return
        
        if self.ended:
            self.reset()
        # else:
        #     self.seq_i += 1
        #     if self.seq_i == len(self.seqs):
        #         if self.loop_type == "all":
        #             self.reset()
        #         elif self.loop_type == "last":
        #             self.seq_i -= 1
        #             self._next_timer = 0.0
    
    def _get_priority_list(self) -> List[Track]:
        pl = [self]
        for t in self._sync_children:
            pl.extend(t._get_priority_list())
        return pl


    def update(self, timedelta):
        """ Returns MidiMessages when a new sequence just started """
        # TODO: allow looping for finished generators

        if self.ended or not self.seqs:
            return
        
        # Time flowing
        self._next_timer -= timedelta
        if self._next_timer > 0.0:
            return
        
        for t in self._sync_children:
            t._sync()

        if self.seq_i < len(self.seqs):
            # Send next sequence
            sequence = self.seqs[self.seq_i]
            if isinstance(sequence, Generator):
                try:
                    sequence = next(sequence)
                except StopIteration:
                    self.seq_i += 1
                    return self.update(0.0)
                finally:
                    self.seq_i -= 1
            
            messages = sequence.getMidiMessages(self.channel)
            messages = [ (t+self._next_timer, mess) for t, mess in messages ]
            self._next_timer += sequence.length
            self.seq_i += 1

            if self.instrument and self.send_program_change:
                program_change = [0xC0 + self.channel, self.instrument]
                # Make sure the instrument change precedes the notes
                return [ (-0.0001, program_change) ] + messages
            return messages if not self.muted else None

        elif self.seq_i >= len(self.seqs):
            # End of track reached
            if not self.loop:
                self.ended = True
                return
            
            # Looping
            if self.loop_type == "all":
                self.seq_i = 0
                return self.update(0.0)
            elif self.loop_type == "last":
                self.seq_i -= 1
                return self.update(0.0)
            else:
                raise Exception(f"'loop_type' property should be set to 'all' or 'last', but got '{self.loop_type}' instead")
            
            # if self.generator:
            #     try:
            #         new_seq = next(self.generator)
            #         self._next_timer += new_seq.length
            #         return new_seq.getMidiMessages(self.channel)
            #     except StopIteration:
            #         if self.loop:
            #             self.reset()
            #         else:
            #             self.ended = True
    
    def __len__(self):
        return len(self.seqs)
    
    def __repr__(self):
        if self._sync_from != None:
            return f"Track({self.channel=},{self.loop=}, {self.name=}, {self._sync_from.name=})"
        return f"Track({self.channel=},{self.loop=}, {self.name=})"



class Song():

    def __init__(self):
        self.tempo = 120
        self.time_signature = (4, 4)
        self.tracks = []