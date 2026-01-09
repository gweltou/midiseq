from __future__ import annotations
from typing import Optional, Union, List, Tuple, Generator, Callable
import random
import re
from math import pow
import json

from rtmidi.midiconstants import (
    NOTE_ON, NOTE_OFF,
    PROGRAM_CHANGE, POLY_AFTERTOUCH
)


import midiseq.env as env
from .definitions import scales, modes
from .modulation import Mod, ModSeq



NOTE_CHORD_PATTERN = re.compile(r"""([+-]?\d?)?	# Octave transposition
                                    (do|re|ré|mi|fa|sol|la|si|ti|[a-g])
                                    (b|\#)?			# Accidentals (flat or sharp)
                                    (M|m|mM|\+|°|sus2|sus4)? # Maj, min, min/Maj, aug,...
                                    (6|7|9|11|13)?		# Seventh, ninth, eleventh
                                """, re.X|re.I)

# MIDI_PITCH_PATTERN = re.compile(r"(\d+)(%[\d/.]+)?")
MIDI_PITCH_PATTERN = re.compile(r"(\d+)")


ROMAN_DEGREE_PATTERN = re.compile(r"""([+-]?\d?)?	# Octave transposition
                                    ([ivx]+)		# Degree
                                    (6|7|9|11|13)?		# Seventh, ninth, eleventh
                                """, re.X|re.I)

SILENCE_PATTERN = re.compile(r"(\.+)")

chord_intervals = {
    'M':   (0, 4, 7), '': (0, 4, 7), # Major
    'm':   (0, 3, 7), # Minor
    '+':   (0, 4, 9), # Augmented
    '°':   (0, 3, 6), # Diminished
    'sus2':(0, 2, 7), # Suspended second
    'sus4':(0, 5, 7), # Suspended fourth
    '6':   (0, 4, 7, 9), 'M6': (0, 4, 7, 9), # Major sixth
    'm6':  (0, 3, 7, 9), # Minor sixth
    '7':   (0, 4, 7, 10), # Dominant seventh
    'M7':  (0, 4, 7, 11), # Major seventh
    'm7':  (0, 3, 7, 10), # Minor seventh
    'mM7': (0, 3, 7, 11), # Minor/Major seventh
    '°7':  (0, 3, 6, 9),  # Diminished seventh
    '9':   (0, 4, 7, 10, 14), # Dominant ninth
    'M9':  (0, 4, 7, 11, 14), # Major ninth
    'm9':  (0, 3, 7, 10, 14), # Minor seventh
    '11':  (0, 4, 7, 10, 14, 17), # Dominant eleventh
    'M11': (0, 4, 7, 11, 14, 17), # Major eleventh
    'm11': (0, 3, 7, 10, 14, 17), # Minor eleventh
    '13':  (0, 4, 7, 10, 14, 17, 21), # Dominant thirteen
    'M13': (0, 4, 7, 11, 14, 17, 21), # Major thirteen
    'm13': (0, 3, 7, 10, 14, 17, 21), # Minor thirteen
}

roman2num = {
    'i'	    : 0,
    'ii'	: 1,
    'iii'   : 2,
    'iv'	: 3,
    'v'	    : 4,
    'vi'	: 5,
    'vii'   : 6,
    'viii'  : 7,
    'ix'	: 8,
    'x'	    : 9,
    'xi'	: 10,
    'xii'   : 11,
}




def _get_octave(s: Optional[str]) -> int:
        """
        Convert octave transpose, in mini-notation, to an integer value.
        Octave can be relative (if prefixes with +/-) or absolute (single digit).
        """
        if not s:
            return env.default_octave
        if s[0] in ('-','+'):
            if len(s) == 1:
                s = s[0] + '1'
            octave = eval(str(env.default_octave) + s)
            return min(max(octave, 0), 10)
        return int(s)



def str2pitch(tone: str) -> int:
    """
    Returns the midi pitch number given a spelled note
    
    String pitches
        48 50 52
        a b c d e f g
        do re mi fa sol la si
        a# la# cb dob
    
    Octave changes
        +la 3la -c -do# -2fa +8sib
    """
    
    if not isinstance(tone, str):
        raise TypeError("Argument must be a string. Ex: 'do', '4c#', '60',...")

    tone = tone.strip()
    if tone.isdecimal():
        return min(max(0, int(tone)), 255)

    note_value = {  
        'c': 0,	   'do': 0,
        'd': 2,	   're': 2,	'ré': 2,
        'e': 4,	   'mi': 4,
        'f': 5,	   'fa': 5,
        'g': 7,	   'sol': 7,
        'a': 9,	   'la': 9,
        'b': 11,   'si': 11
    }
    
    match = NOTE_CHORD_PATTERN.match(tone)
    if match:
        octave = _get_octave(match[1])
        pitch = 12 * octave + note_value[match[2].lower()]
        pitch += 1 if match[3]=='#' else -1 if match[3]=='b' else 0
        return pitch
    return -1




class Scl():
    """Musical scale"""

    def __init__(self, scale: Union[str, List]="major", tonic: Union[str, int]=60):
        if isinstance(tonic, int):
            self.tonic = min(127, max(0, tonic))
        elif isinstance(tonic, str):
            self.tonic = str2pitch(tonic)
        else:
            raise TypeError("root note must be a pitch number [0-127] or a valid note name")

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


    def _getNotes(self):
        """Returns all midi pitches in scale"""
        pitches = []
        smallest_tonic = self.tonic % 12
        for oct in range(-1, 11):
            for d in self.scale:
                pitch = oct*12 + smallest_tonic + d
                if 0 <= pitch < 128:
                    pitches.append(pitch)
        return pitches


    def getClosest(self, val: Union[str, int]) -> int:
        """
        Find closest note in scale given a pitch
        Returns a corrected pitch, in range [0-127]
        If the given pitch is between scale pitches, picks the lower scale pitch
        """
        if isinstance(val, int):
            pitch = min(127, max(0, val))
        elif isinstance(val, str):
            pitch = parse_element(val).pitch
        else:
            raise TypeError(f"Argument must be a pitch number [0-127] or a valid note name, got {val}")

        octave, degree = divmod(pitch, 12)
        distances = [s-(degree-self.tonic)%12 for s in self.scale]
        min_dist = 12
        for d in distances:
            if abs(d) < abs(min_dist):
                min_dist = d
        
        return int(12 * octave + degree + min_dist)


    def getDegree(self, n: int, oct=0) -> int:
        """ 
        Get the pitch of the n-th degree note in the current musical scale, relative to the rootnote
        Beware : degrees start at 0. The fifth degree would be n=4.
        """
        
        nth_oct, nth_degree = divmod(round(n), len(self.scale))
        nth_oct += oct

        if n >= 0:
            distances = self.scale
        else:  # Negative number
            distances = [ d-12 for d in self.scale]
            nth_oct += 1

        return self.tonic + 12 * nth_oct + distances[nth_degree]


    def getDegreeFrom(self, pitch: Union[str, int], n: int) -> int:
        """Returns pitch +/- n degrees in the current scale"""
        if isinstance(pitch, str):
            pitch = str2pitch(pitch)
        
        for i, p in enumerate(self.notes):
            if p == pitch:
                # Pitch is in scale
                idx = i + n
                break
            if p > pitch:
                # Find closest between prev an next
                d_prev = pitch - self.notes[i-1]
                d_next = p - pitch
                if d_prev <= d_next:
                    idx = i - 1 + n
                else:
                    idx = i + n
                break
        
        idx = min(max(idx, 0), len(self.notes))
        return self.notes[idx]


    def triad(self, degree=0, oct=0, dur=1, vel=100):
        """ Returns a triad Chord of the nth degree in the scale """
        return Chord(*[self.getDegree(degree+inter, oct=oct) for inter in [0,2,4]],
                     dur=dur, vel=vel)


    def seventh(self, degree=0, oct=0, dur=1, vel=100):
        """ Returns a seventh Chord of the nth degree in the scale """
        return Chord(*[self.getDegree(degree+inter, oct=oct) for inter in [0,2,4,6]],
                     dur=dur, vel=vel)


    def __str__(self):
        return "{} {}".format(self.scale, self.tonic)
    
    def __repr__(self):
        scale_name = f"'{self.scale_name}'" if isinstance(self.scale_name, str) else self.scale_name
        return f"Scale({scale_name}, {self.tonic})"

    def __len__(self):
        return len(self.scale)






class BaseElement():

    def __mul__(self, factor: Union[int, float]) -> Element:
        if isinstance(factor, int):
            # Repeat
            s = Seq()
            iterations: int = factor
            for _ in range(iterations):
                s.add(self.copy())
            return s
        elif isinstance(factor, float):
            # Stretch
            n = self.copy()
            n.stretch(factor)
            return n
        else:
            raise TypeError("Can only multiply elements by an int or a float")
    
    def __rmul__(self, factor: Union[int, float]) -> Element:
        return self.__mul__(factor)






class Note(BaseElement):

    def __init__(
            self,
            pitch: Union[int, str],
            dur: float = 1.0,
            vel: int = 100,
            prob: float = 1.0
        ):
        if isinstance(pitch, str):
            pitch = parse_element(pitch).pitch
        elif isinstance(pitch, int) and (pitch < 0 or pitch > 127):
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        self.pitch = min(max(pitch, 0), 127)
        self.dur = dur * env.note_dur
        self.vel = vel
        self.prob = prob

        # Poly-Aftertouch
        self.pat = None
        self.patval = None
    

    def copy(self) -> Note:
        new_note = Note(self.pitch, self.dur, self.vel, self.prob)
        new_note.dur = self.dur # Overrides the env note_dur multiplier
        new_note.pat = self.pat
        new_note.patval = self.patval
        return new_note


    def aftertouch(self, mod: Mod) -> Note:
        """Add a poly-aftertouch modulation to this note"""
        self.pat = mod
        self.patval = mod.getValues(0.0, 1.0, stretch=self.dur)
        return self


    def stretch(self, factor) -> Note:
        """Stretch or shrink the duration of the note"""
        self.dur *= factor
        if self.pat is not None:
            self.patval = self.pat.getValues(0.0, 1.0, stretch=self.dur)
        return self
    
    def stretched(self, factor) -> Note:
        """Stretch or shrink the duration of the note"""
        new_note = self.copy()
        new_note.dur *= factor
        if new_note.pat is not None:
            new_note.patval = new_note.pat.getValues(0.0, 1.0, stretch=new_note.dur)
        return new_note


    def transpose(self, semitones) -> Note:
        self.pitch = min(max(self.pitch + semitones, 0), 127)
        return self
    
    def transposed(self, semitones) -> Note:
        new_note = self.copy()
        new_note.pitch = min(max(new_note.pitch + semitones, 0), 127)
        return new_note


    def __add__(self, other) -> Seq:
        return Seq().add(self).add(other)
    
    def __truediv__(self, factor: Union[int, float]):
        n = self.copy()
        n.dur = self.dur / factor
        if n.pat is not None:
            n.patval = n.pat.getValues(0.0, 1.0, stretch=n.dur)
        return n
    
    def __xor__(self, semitones):
        """ Transpose sequence in semitones """
        n = self.copy()
        n.pitch = min(max(n.pitch + semitones, 0), 127)
        return n

    def __mod__(self, factor: float) -> Note:
        n = self.copy()
        n.stretch(factor)
        return n

    def __eq__(self, other):
        return self.pitch == other.pitch and \
               self.dur == other.dur and \
               self.vel == other.vel and \
               self.prob == other.prob

    def __str__(self):
        if hasattr(self, "string"):
            return self.string
        return self.__repr__()
    
    def __repr__(self):
        args = "{}".format(self.pitch)
        if self.dur != env.note_dur:
            args += ",{}".format(round(self.dur/env.note_dur, 3))
        if self.vel != 100:
            args += ",{}".format(self.vel)
        if self.prob != 1:
            args += ",{}".format(round(self.prob, 3))
        return "Note({})".format(args)






class PNote(Note):
    def __init__(self, wdict, dur=None, vel=100, prob=1):
        """
        *Experimental*
    
        A Schroedinger's note.
        Only one will be played, depending on probability weights.
        All given notes should be of the same duration.

        Parameters
        ----------
            pdict: dict
                '{"do": 1, "mi": 2, "sol": 1}'
        
        * Could we give Chords instead of notes ? Maybe
        """
        self.dur = dur if dur != None else env.note_dur # XXX Absolute duration
        self.vel = vel
        self.prob = prob

        # Poly-Aftertouch
        self.pat = None
        self.patval = None

        self.pdict = {}
        self.sum_weights = 0
        if isinstance(wdict, dict):
            # Normalizing probabilites
            self.sum_weights = sum(wdict.values())
            self.pdict = self._weights_to_prob(wdict)
        elif isinstance(wdict, (list, tuple, set)):
            # Same probability for all notes
            self.sum_weights = len(wdict)
            cumul = 1/len(wdict)
            for n in wdict:
                if isinstance(n, str):
                    n = str2pitch(n)
                elif isinstance(n, (Note,)):
                    n = n.pitch
                self.pdict[n] = cumul
                cumul += 1/len(wdict)
        elif isinstance(wdict, str):
            # Same probability for all notes
            self.pdict = self._weights_to_prob( {str2pitch(n): 1 for n in wdict.split()} )
            self.sum_weights = len(wdict)
        else:
            raise TypeError("pdict should be a dictionary (pitch -> prob weight) or an iterable")
    

    def copy(self):
        n = PNote({})
        n.pdict = self.pdict
        n.sum_weights = self.sum_weights
        n.dur = self.dur # Overrides the env note_dur multiplier
        n.vel = self.vel
        n.prob = self.prob
        n.pat = self.pat
        n.patval = self.patval
        return n


    def add(self, pitch, weight):
        """ Add a note, with a probability weight """
        wdict = self._prop_to_weights()
        if isinstance(pitch, str):
            pitch = str2pitch(pitch)
        wdict[pitch] = weight
        self.pdict = self._weights_to_prob(wdict)


    @staticmethod
    def _weights_to_prob(wdict: dict) -> dict:
        pdict = dict()
        sum_weights = sum(wdict.values())
        cumul = 0
        for n, w in wdict.items():
            if isinstance(n, str):
                n = str2pitch(n)
            cumul += w/sum_weights
            pdict[n] = cumul
        return pdict

    def _prop_to_weights(self) -> dict:
        wdict = dict()
        last_p = 0
        for n, p in self.pdict.items():
            w = (p - last_p) * self.sum_weights
            last_p = p
            wdict[n] = w
        return wdict
    

    @property
    def pitch(self) -> int:
        r = random.random()
        for pitch, prob in self.pdict.items():
            if r < prob:
                return pitch
    
    @pitch.setter
    def pitch(self, i: int) -> None:
        print("You shouldn't assign a pitch to a PNote")


    def transpose(self, semitones):
        self.pdict = {n+semitones: self.pdict[n] for n in self.pdict}

    def __repr__(self):
        return f"PNote({self._prop_to_weights()})"






class Sil(BaseElement):
    """Silence"""
    
    def __init__(self, dur = 1.0):
        self.dur = dur * env.note_dur


    def stretch(self, factor) -> Sil:
        self.dur *= factor
        return self

    def stretched(self, factor) -> Sil:
        new_sil = Sil()
        new_sil.dur *= factor
        return new_sil


    def copy(self) -> Sil:
        new_sil = Sil()
        new_sil.dur = self.dur
        return new_sil
    

    def __add__(self, other) -> Union[Sil, Seq]:
        if isinstance(other, Sil):
            return Sil((self.dur + other.dur) / env.note_dur)
        return Seq().add(self).add(other)

    def __mul__(self, factor: Union[int, float]) -> Sil:
        return Sil(self.dur * factor / env.note_dur)
    
    def __truediv__(self, factor: Union[int, float]) -> Sil:
        return Sil(self.dur / (factor * env.note_dur))

    def __eq__(self, other):
        return self.dur == other.dur

    def __str__(self):
        if hasattr(self, "string"):
            return self.string
        return self.__repr__()
    
    def __repr__(self):
        arg_dur = ""
        if self.dur != env.note_dur:
            arg_dur = str(round(self.dur/env.note_dur, 3))
        return "Sil({})".format(arg_dur)




class Chord(BaseElement):
    """ Chords are made of many notes playing at the same time """

    def __init__(self, *notes, dur=None, vel=None):
        self.notes = []
        self.pitches = set() # Helps to avoid duplicate notes
        # self.prob = prob

        for elt in notes:
            if isinstance(elt, int):
                elt = Note(elt, dur=dur or 1.0, vel=vel or 100)
            
            if isinstance(elt, Note):
                self._insert_note(elt.copy())
            elif isinstance(elt, str):
                self._parse_string(elt)
            elif isinstance(elt, Chord):
                self._merge_chord(elt)
            else:
                raise TypeError(f"Argument `notes` must be Notes, strings or integers, got {elt} ({type(elt)})")
        
        self.dur = (dur or 1.0) * env.note_dur
        # if dur:
        #     # Constrain all notes to the chord duration
        #     for n in self.notes:
        #         n.dur = dur * env.note_dur
        #     self.dur = dur * env.note_dur
        # else:
        #     # Use duration of longest note
        #     max_dur = max( [n.dur for n in self.notes] )
        #     self.dur = max_dur


    def copy(self) -> Note:
        new_chord = Chord()
        new_chord.notes = [ n.copy() for n in self.notes ]
        new_chord.pitches = self.pitches.copy()
        return Chord(self)
    

    def arp(self, oct=1, mode="up") -> Seq:
        """
        Return the sequence the arpeggiated Chord
        

        Args:
            type: str
                "up" / "down"
                "updown" / "downup"
                "rnd"
            oct: int
                Number of octaves to aperggiate
                Additional octaves will be of higher pitch
        """
        notes = []
        if mode == "up":
            for n_oct in range(oct):
                for n in sorted(self.notes, key=lambda n: n.pitch):
                    new_note = n.copy()
                    new_note.pitch += 12 * n_oct
                    notes.append(new_note)
        elif mode == "down":
            return self.arp(mode="up", oct=oct).reverse()
        elif mode == "updown":
            for n_oct in range(oct):
                for n in sorted(self.notes, key=lambda n: n.pitch):
                    new_note = n.copy()
                    new_note.pitch += 12 * n_oct
                    notes.append(new_note)
            notes += notes[-2:0:-1]
        elif mode == "downup":
            for n_oct in range(oct):
                for n in sorted(self.notes, key=lambda n: n.pitch, reverse=True):
                    new_note = n.copy()
                    new_note.pitch += 12 * (oct - (n_oct+1))
                    notes.append(new_note)
            notes += notes[-2:0:-1]
        elif mode == "rnd":
            for n_oct in range(oct):
                for n in self.notes:
                    new_note = n.copy()
                    new_note.pitch += 12 * n_oct
                    notes.append(new_note)
            random.shuffle(notes)
        else:
            raise ValueError(f"{mode} is not a recognized arpeggiator mode")
        
        arp_seq = Seq()
        for n in notes:
            arp_seq.add(n)
        return arp_seq


    def _insert_note(self, note: Note) -> None:
        if note.pitch in self.pitches:
            # Note already in chord, keep longest
            for n in self.notes:
                if n.pitch == note.pitch:
                    self.notes.remove(n)
                    self.notes.append(note)
                    break
        else:
            self.notes.append(note)
            self.pitches.add(note.pitch)


    def _parse_string(self, string: str) -> None:
        for elt in string.split():
            elt = parse_element(elt)
            if isinstance(elt, Note):
                self._insert_note(elt)
            elif isinstance(elt, Chord):
                self._merge_chord(elt)
            else:
                raise TypeError("Unrecognized element : {}".format(elt))
    

    def _merge_chord(self, other: Chord) -> None:
        for note in other.notes:
            self._insert_note(note)


    def stretch(self, factor) -> Chord:
        self.dur *= factor
        return self.gate(factor)
    
    def stretched(self, factor) -> Chord:
        new_chord = Chord()
        self.dur *= factor
        return self.gate(factor)


    def gate(self, factor) -> Chord:
        """ Stretch notes duration without changing the whole chord duration """
        for n in self.notes:
            n.dur *= factor
        return self


    def transpose(self, semitones) -> Chord:
        for n in self.notes:
            n.transpose(semitones)
        self.pitches = set([n.pitch for n in self.notes])
        return self


    def __xor__(self, semitones):
        """ Transpose chord in semitones """
        return Chord(*[ n^semitones for n in self.notes ])

    def __add__(self, other):
        return Seq().add(self).add(other)

    def __mod__(self, factor: float) -> Chord:
        chord = self.copy()
        chord.gate(factor)
        return chord

    def __eq__(self, other):
        if self.dur != other.dur:
            return False
        if len(self.notes) != len(other.notes):
            return False
        return all( [n1 == n2 for n1, n2 in zip(self.notes, other.notes)] )

    def __len__(self):
        return len(self.notes)

    def __iter__(self):
        yield from self.notes
    
    def __str__(self):
        if hasattr(self, "string"):
            return self.string
        return self.__repr__()

    def __repr__(self):
        if self.dur != env.note_dur:
            return "Chord({}, dur={})".format(
                ', '.join( [str(n.pitch) for n in self.notes] ),
                self.dur / env.note_dur
                )
        return "Chord({})".format(', '.join( [str(n.pitch) for n in self.notes] ))




class Seq(BaseElement):
    """Sequence of notes"""

    def __init__(self, *notes, dur=0):
        self.notes: List[Tuple[float, Note]] = []
        self.silences: List[Tuple[float, Sil]] = []  # Keep a record of silence, only used for random picking
                                                     # so no need to sort it
        self.dur = dur  # Can be further than the end of the last note
        self.head = 0.0 # Recording head

        self.modseq = None
        self.string = ""  # Symbolic string representation

        for elt in notes:
            if isinstance(elt, int):
                self._addNote(Note(elt))
            elif isinstance(elt, Note):
                self._addNote(elt)
            elif isinstance(elt, (Sil, Chord, Seq, str)):
                self.add(elt)
            elif isinstance(elt, tuple):
                # A (time_pos, Note) tuple
                time_pos, note = elt
                self.add(note, head=time_pos)
            elif hasattr(elt, '__iter__'):
                self.addNotes(elt)
            else:
                raise TypeError

    
    def copy(self) -> Seq:
        new = Seq()
        new.notes = [ (t, n.copy()) for t, n in self.notes ]
        new.silences = [ (t, s) for t, s in self.silences ]
        new.dur = self.dur
        new.head = self.head
        new.string = self.string
        return new

    
    def __getstate__(self) -> object:
        def serialize_note(t: float, n: Note):
            data = [t, n.pitch, n.dur / env.note_dur, n.vel]
            if n.prob != 1.0:
                data.append(n.prob)
            return data
        
        data = self.__dict__.copy()
        data["notes"] = [ serialize_note(t, n) for t, n in self.notes ]
        del data["modseq"]

        return data


    def toJson(self) -> str:
        """Serialize this sequence to a string"""
        obj = self.__getstate__()
        return json.dumps(obj)
    

    @classmethod
    def from_json(cls, json_str) -> Seq:
        s = cls()
        data = json.loads(json_str)
        notes = []
        for n in data["notes"]:
            notes.append( (n[0], Note(*n[1:])) )
        s.notes = notes

        s.dur = data["dur"]
        s.head = data["head"]
        s.string = data["string"]

        return s
    

    def getMidiMessages(self, channel=0) -> List[Tuple[float, list]]:
        """Return this sequence as a list of MIDI messages

        Parameters:
            channel (int):
                Midi channel [0-15]
        """
        messages = []
        for pos, note in self.notes:
            # Probability
            if note.prob < 1 and random.random() > note.prob:
                continue
            
            pitch = min(max(note.pitch, 0), 127)
            note_on = [NOTE_ON | channel, pitch, note.vel]
            messages.append( (pos, note_on) )
            if note.pat != None:
                messages.extend(
                    [
                        (
                            pos + p,
                            [
                                POLY_AFTERTOUCH | channel,
                                note.pitch,
                                min(max(int(val * 128), 0), 127)
                            ]
                        )
                    for p, val in note.patval ]
                )

            note_off = [NOTE_OFF|channel, pitch, 0]
            messages.append( (pos + note.dur, note_off) )

        # messages.sort(key=lambda n: (n[0],n[1][0]))
        return messages


    def clear(self):
        self.notes.clear()
        self.silences.clear()
        self.head = 0.0
        self.string = ""


    def add(
        self,
        element: Union[int, str, Note, Sil, Chord, Seq],
        head: Optional[float] = None
    ) -> Seq:
        """
        Add a single musical element or whole sequences at the recording head position.
        This will grow the sequence's duration if necessary.

        **Modifies the sequence in-place**
        """
        if isinstance(head, (float, int)):
            self.head = head
        
        # int and string types call 'add' recursively
        if isinstance(element, int):
            return self.add(Note(element))
        elif isinstance(element, str):
            s, _ = parse(element)
            self.string = ' '.join([self.string, s.string])
            return self.add(s)
        
        elif isinstance(element, Note):
            self._addNote(element)
            return self
        elif isinstance(element, Sil):
            self.silences.append( (self.head, element.copy()) )
        elif isinstance(element, Chord):
            for note in element.notes:
                self.notes.append( (self.head, note.copy()) )
        elif isinstance(element, Seq):
            for (t, note) in element.notes:
                self.notes.append( (self.head + t, note.copy()) )
            for (t, sil) in element.silences:
                self.silences.append( (self.head + t, sil.copy()) )
        else:
            raise TypeError(f"Only instances of Note, Sil, Chord, Seq or string sequences can be added to a Sequence, got {element} ({type(element)})")
        
        self.head += element.dur
        self.dur = max(self.dur, self.head)
        self.notes.sort(key=lambda x: x[0])
        return self
    

    def _addNote(self, note: Note) -> None:
        self.notes.append( (self.head, note) )
        self.head += note.dur
        self.dur = max(self.dur, self.head)
        self.notes.sort(key=lambda x: x[0])


    def addNotes(self, notes, dur=1, vel=100):
        # XXX: maybe do without this method altogether
        """Add notes sequencially from a string sequence or an iterable.
        
        If an iterable is given, it can contain sub-lists to provide notes duration.

        Parameters:
            notes (str/list/tuple):
                A list of note pitches, can be a string or an iterable
                Ex: "c# d f2 do re mi" or (61, 62, 29, 60, 62, 64)
        """
        # if isinstance(notes, str):
        #     self.add(str2seq(notes))
        if hasattr(notes, '__iter__'):
            for pitch in notes:
                if type(pitch) in (tuple, list):
                    self.addNotes(pitch, dur / len(pitch), vel)
                elif pitch == 0:
                    self.add(Sil(dur))
                else:
                    self.add(Note(pitch, dur, vel))
        else:
            raise TypeError("argument `notes` must be a string or an iterable")
        return self


    def addMod(self, mod: Mod, controler: int) -> Seq:
        if not self.modseq:
            self.modseq = ModSeq(dur=self.dur)
        
        self.modseq.add(mod, controler)
        return self
    

    def addModNotes(
        self,
        mod: Mod,
        controler: int,
        notes: Union[int, List, None] = None
    ) -> Seq:
        if not self.modseq:
            self.modseq = ModSeq(dur=self.dur)
        
        for t, note in self.notes:
            self.modseq.add(mod, controler, t, note.dur)
        return self
    

    def clearMod(self):
        self.modseq = None


    def merge(self, other: Union[Seq, Note, Chord]) -> Seq:
        """
        Merge sequences, preserving every note's time position.
        This Sequence's new duration will be the max of every merged element.

        **Modifies sequence in-place**
        """
        if isinstance(other, Seq):
            # Merging two sequences together
            for t, n in other.notes:
                self.notes.append( (t, n.copy()) )
            for t, s in other.silences:
                self.silences.append((t, s))
        elif isinstance(other, (Note, Chord)):
            # Merging this sequence with a single element
            self.notes.append((0, other.copy()))
        elif isinstance(other, Sil):
            # Who would do that ?
            self.silences.append((0, other))
        else:
            raise TypeError("Can only merge Sequences with Notes, Chords or other Sequences")
        
        self.notes.sort(key=lambda x: x[0])
        self.dur = max(self.dur, other.dur)
        return self

    def merged(self, other: Union[Seq, Note, Chord]) -> Seq:
        new_seq = self.copy()
        return new_seq.merge(other)


    def stretch(self, factor, stretch_notes=True) -> Seq:
        """
        Stretch the sequence in time

        **Modifies the sequence in-place**
        """
        for i in range(len(self.notes)):
            t, note = self.notes[i]
            if stretch_notes:
                note.stretch(factor)
            self.notes[i] = t * factor, note
        self.dur *= factor
        self.head *= factor
        return self
    
    def stretched(self, factor, stretch_notes=True) -> Seq:
        new_seq = self.copy()
        return new_seq(factor, stretch_notes)


    def compress(self, dur_factor=1.0, vel_factor=1.0) -> Seq:
        """
        Compress silences and note durations by a given factor.
        
        **Modifies the sequence in-place**
        """
        new_seq = Seq()
        for _, note in self.notes:
            new_dur = note.dur * (1.0 - dur_factor) + dur_factor
            new_vel = note.vel * (1.0 - vel_factor) + round(127 * vel_factor)
            new_seq.add(Note(note.pitch, new_dur, new_vel))

        self.notes = new_seq.notes
        self.head = new_seq.head
        self.dur = new_seq.dur
        return self
    
    def compressed(self, dur_factor=1.0, vel_factor=1.0) -> Seq:
        new_seq = Seq()
        return new_seq.compress(dur_factor, vel_factor)


    def gate(self, factor) -> Seq:
        """
        Stretch notes without modifying the sequence's length
        
        **Modifies the sequence in-place**
        """
        for _, note in self.notes:
            note.stretch(factor)
        
        for _, sil in self.silences:
            sil.stretch(factor)

        return self


    def reverse(self) -> Seq:
        """
        Reverse notes order
        
        **Modifies sequence in-place**
        """
        new_notes = []
        for t, n in self.notes:
            new_notes.append( (self.dur - t - n.dur, n) )
        self.notes = sorted(new_notes)
        self.string = "" # TODO

        return self
    
    def reversed(self) -> Seq:
        new_seq = self.copy()
        return new_seq.reverse()


    def transpose(self, semitones: int) -> Seq:
        """
        Transpose all notes in sequence by semitones
        
        **Modifies sequence in-place**
        """
        
        for _, note in self.notes:
            note.transpose(semitones)
        self.string = "" # TODO
        return self
    
    def transposed(self, semitones: int) -> Seq:
        new_seq = self.copy()
        return new_seq.transpose(semitones)


    def scalePitch(self, factor: float, in_scale=True) -> Seq:
        """
        Expand or compress notes pitches around the mean value of the whole sequence.

        Args:
            factor (float):
                Expansion factor (< 1.0 for compression, > 1.0 for expension)
            in_scale (boolean):
                If True, expanded/compressed pitches will stay in env scale
        """
        # XXX: Won't work with PNotes for now
        # Find mean pitch of this sequence
        sum = 0
        for _, note in self.notes:
            sum += note.pitch
        mean = sum / len(self.notes)

        for _, note in self.notes:
            diff = note.pitch - mean
            pitch = round(mean + diff * factor)
            if in_scale and env.scale:
                pitch = env.scale.getClosest(pitch)
            note.pitch = min(255, max(0, pitch))
        return self
    

    def stutter(self, n=2, prob=1.0, idx: Optional[int] = None) -> Seq:
        """
        Split every note in equal divisions.
        
        **Modifies the sequence in-place**

        Args:
            n (int):
                Number of divisions
            prob (float):
                The probability the splitting happens
            idx (int):
                If used, divide only the note at that position
        """
        if type(n) != int or n <= 0:
            raise TypeError("number of splits should be equal to 2 or greater ")

        if isinstance(idx, int):
            if idx >= len(self.notes):
                raise ValueError("idx is greater than number of notes in sequence")
            if random.random() < prob:
                t, note = self.notes[idx]
                split_dur = note.dur / n
                old_head = self.head
                del self.notes[idx]
                self.head = t
                for i in range(n):
                    n = note.copy()
                    n.dur = split_dur
                    self.add(n)
                self.head = old_head
            return self

        orig = self.notes[:]
        self.clear()
        for t, note in orig:
            if random.random() < prob:
                split_dur = note.dur / n
                for i in range(n):
                    splitted_note = note.copy()
                    splitted_note.dur = split_dur
                    self.notes.append( (t + i * split_dur, splitted_note) )
            else:
                self.notes.append((t, note))
        return self


    def decimate(self, prob=0.2) -> Seq:
        """
        Erase notes randomly based on the given probability
        
        **Modifies the sequence in-place**
        """
        new_notes = []
        for t, note in self.notes:
            if random.random() > prob:
                new_notes.append( (t, note) )
        self.notes = new_notes

        new_silences = []
        for t, s in self.silences:
            if random.random() > prob:
                new_silences.append( (t, s) )
        self.silences = new_silences

        return self
    
    def decimated(self, prob=0.2) -> Seq:
        new_seq = self.copy()
        return new_seq.decimate(prob)



    def attenuate(self, factor=1.0) -> Seq:
        """
        Attenuate notes velocity by a given factor
        
        **Modifies the sequence in-place**
        """
        for _, note in self.notes:
            note.vel = min(max(round(note.vel * factor), 0), 127)
        return self
    
    def attenuated(self, factor=1.0) -> Seq:
        new_seq = self.copy()
        return new_seq.attenuate(factor)


    def humanize(self, tfactor=0.01, veldev=5) -> Seq:
        """
        Randomly offsets the notes time and duration
        
        **Modifies the sequence in-place**

        Args:
            tfactor: 0.0 < float < 1.0 (default 0.01)
                variation en note temporal position
            veldev: float (default 5)
                velocity standard deviation
        """
        new_notes = []
        for t, note in self.notes:
            t = t + 2 * (random.random()-0.5) * tfactor
            note.stretch(1 + random.random() * tfactor)
            note.vel = round(note.vel + random.gauss(0, veldev))
            note.vel = min(max(note.vel, 0), 127)
            new_notes.append( (t, note) )
        self.notes = new_notes
        return self
    
    def humanized(self, tfactor=0.01, veldev=5) -> Seq:
        new_seq = self.copy()
        return new_seq.humanize(tfactor, veldev)


    def octShift(self, prob_up=0.1, prob_down=0.1) -> Seq:
        """
        Transpose notes one octave up or one octave down randomly.
        
        **Modifies the sequence in-place**
        """
        for _, note in self.notes:
            if random.random() < prob_up:
                note.transpose(12)
            elif random.random() < prob_down:
                note.transpose(-12)
        return self


    def crop(self) -> Seq:
        """
        Shorten or delete notes before time 0 and after the sequence's duration.
        
        **Modifies the sequence in-place**
        """
        cropped_notes = []
        for t, n in self.notes:
            if t + n.dur > 0 and t < self.dur:
                if t < 0:
                    n.dur += t
                elif t + n.dur > self.dur:
                    n.dur -= t + n.dur - self.dur
                t = (min(max(t, 0), self.dur))
                cropped_notes.append( (t, n) )
            self.notes = cropped_notes
        return self
    
    def cropped(self) -> Seq:
        new_seq = self.copy()
        return new_seq.crop()
    

    def strip(self) -> Seq:
        """ Remove silences from both ends of the sequence
            Modifies sequence in-place
        """
        return self.stripHead().stripTail()
    
    def stripped(self) -> Seq:
        new_seq = self.copy()
        return new_seq.strip()
    
    def stripHead(self) -> Seq:
        """ Remove silences in front of the sequence
            Modifies sequence in-place
        """
        head_offset = self.notes[0][0] # Expects self.notes to be sorted
        new_notes = []
        for t, n in self.notes:
            new_notes.append( (t-head_offset, n) )
        self.notes = new_notes
        self.head -= head_offset
        self.dur -= head_offset
        return self
    
    def stripTail(self) -> Seq:
        """ Remove silences at the end of the sequence
            Modifies sequence in-place
        """
        last_onset, last_note = self.notes[-1]
        last_note_end = last_onset + last_note.dur # Expects self.notes to be sorted

        if self.dur > last_note_end:
            self.dur -= self.dur - last_note_end
        if self.head > self.dur:
            self.head = self.dur
        return self


    def shift(self, offset, wrap=False, stretch=False) -> Seq:
        """
        Shift note onset times by a given *absolute* delta time
        Modifies sequence in-place.

        Args:
            offset : [int, float]
                If `offset` is a `float`, will shift sequence by an absolute duration
                If `offset` is a `int`, will shift sequence by the default duration of notes
                A positive `offset` will shift to the right, while negative will shift to the left
            wrap : bool
                Notes that were pushed out of the sequence get appendend to the other side, if true
            stretch : bool
                A positive shift will grow the Seq duration accordingly, if true
        """
        
        if not(offset):
            return self
        
        if isinstance(offset, int):
            offset *= env.note_dur

        new_notes = []
        for t, n in self.notes:
            new_time = t+offset
            if wrap:
                if t+offset >= self.dur:
                    new_time -= self.dur
                elif t+offset < 0:
                    new_time += self.dur
            new_notes.append( (new_time, n) )
        self.notes = sorted(new_notes)

        if stretch and offset > 0:
            self.dur += offset

        return self
    
    def shifted(self, offset, wrap=False, stretch=False) -> Seq:
        new_seq = self.copy()
        return new_seq.shift(offset, wrap, stretch)


    def echo(self, offset, n=1, att=0.8) -> Seq:
        """
        Add delay/echo to sequence without changing its duration
        
        Args:
            offset: [int, float]
                Time delay
            n: int
                Number of echoes
            att: float [0.0-1.0]
                velocity attenuation of echoes 
        """
        new_notes = []
        for t, note in self.notes:
            new_notes.append( (t, note) )
            for i in range(n):
                t_echo = t + offset * (i+1)
                note_echo = note.copy()
                note_echo.vel = round(note_echo.vel * att**(i+1))
                new_notes.append( (t_echo, note_echo) )
        self.notes = sorted(new_notes, key=lambda x: x[0])
        return self
    

    def shuffle(self) -> Seq:
        """
        TODO: Adapt to polyphony

        **Modifies the sequence in place**
        """
        elements: List[Union[Note, Sil]] = [ elt for _, elt in self.notes ]
        elements.extend([ s for _, s in self.silences ])
        random.shuffle(elements)

        onsets = [ t for t,_ in self.notes ]
        onsets.extend( [ t for t,_ in self.silences ] )
        onsets.sort()
        new_notes = []
        new_silences = []
        for t in onsets:
            elt = elements.pop()
            if isinstance(elt, Sil):
                new_silences.append( (t, elt) )
            else:
                new_notes.append( (t, elt) )
        self.notes = new_notes
        self.silences = new_silences
        return self
    
    def shuffled(self) -> Seq:
        new_seq = self.copy()
        return new_seq.shuffle()


    def replacePitch(self, old, new) -> Seq:
        """
        Replace notes with given pitch to a new pitch.

        **Modifies the sequence in-place**
        """
        # TODO: `all_octaves` option
        # XXX: Won't work with PNotes
        if type(old) == str:
            old = str2pitch(old)
        if type(new) == str:
            new = str2pitch(new)
        for note in self.notes:
            if type(note) == Note and note.pitch == old:
                note.pitch = new
        return self


    def mutate(self, prob=0.1, steps=[-5, -3, -1, 1, 3, 5]) -> Seq:
        for _, n in self.notes:
            if random.random() < prob:
                n.pitch = env.scale.getDegreeFrom(n.pitch, random.choice(steps))
        return self
    
    def mutated(self, prob=0.1, steps=[-5, -3, -1, 1, 3, 5]) -> Seq:
        new_seq = self.copy()
        return new_seq.mutate(prob, steps)


    def selectNotes(self, key_fn) -> List[Note]:
        """
        Return a list of notes selected by key_fn
        Notes will be selected if key_fn returns True on them

        Args:
            key_fn: lambda function
        
        Returns:
            A list of Notes
        """
        selection = [ n for _, n in self.notes if key_fn(n) ]
        return selection


    def filtered(self, key_fn) -> Seq:
        """
        Return copy of the sequence with notes filtered by key_fn.
        Notes will be kept if key_fn returns True on them.

        Args:
            key_fn: lambda function
        
        Returns:
            A filtered Sequence
        """
        new_seq = self.copy()
        new_seq.notes = [ (t, n) for t, n in self.notes if key_fn(n) ]
        return new_seq


    Interval = List[float]


    def _getActiveMask(self) -> List[Interval]:
        """Return a list of intervals where there is active notes"""

        active_intervals = []
        for t, note in self.notes:
            if not active_intervals:
                active_intervals.append([t, t+note.dur])
                continue
            last = active_intervals[-1]
            if t <= last[1]:
                if t+note.dur > last[1]:
                    # Extend last active interval
                    last[1] = t+note.dur
            else:
                # New interval
                active_intervals.append([t, t+note.dur])
        return active_intervals


    def _getNotActiveMask(self) -> List[Interval]:
        """Return a list of intervals where there is silence"""

        active_intervals = self._getActiveMask()
        if not active_intervals:
            return [[0.0, self.dur]]
        
        notactive_intervals = []
        if active_intervals[0][0] > 0.0:
            notactive_intervals.append([0.0, active_intervals[0][0]])
        
        last = active_intervals[0][1]
        for interval in active_intervals[1:]:
            notactive_intervals.append([last, interval[0]])
            last = interval[1]
        
        last = active_intervals[-1][1]
        if last < self.dur:
            notactive_intervals.append([last, self.dur])
        return notactive_intervals


    def _mask(self, mask: List[Interval]):
        new_notes = []
        start_i = 0
        s = self.copy()
        for interval in mask:
            for i, (t, note) in enumerate(s.notes[start_i:]):
                if t + note.dur <= interval[0]:
                    # Note is before interval
                    continue
                if t >= interval[1]:
                    # Note is after interval
                    start_i = i
                    break
                start = max(t, interval[0])
                end = min(t + note.dur, interval[1])
                new_note = note.copy()
                new_note.dur = end - start
                new_notes.append((start, new_note))
        s.notes = new_notes
        return s


    def mask(self, other: Seq):
        """Keep notes from this sequences only when sequence `other` has active notes"""
        return self._mask(other._getActiveMask())


    def maskNot(self, other: Seq):
        """
        Keep notes from this sequences only when sequence `other` is silent
        """
        return self._mask(other._getNotActiveMask())


    def mapRhythm(self, rhythm: Union[Seq, list], mode="wrap") -> Seq:
        """
        Map the rhythm of another sequence, or list of duration, to this sequence

        Args:
            other (seq | list):
                An other sequence to map the rhythm from.
                Or a list of duration.
            mode (str):
                "crop": Crop to shortest sequence
                "wrap": Wrap to longest sequence
                "lcm": least common multiplier
        """
        def lcm(a, b):
            """ Returns the least common multiplier between A and B """
            return a*b
        
        if isinstance(rhythm, list):
            s = Seq()
            for d in rhythm:
                s.add(Note('c', dur=d))
            rhythm = s
        
        if mode == "crop":
            n = min(len(self), len(rhythm))
        elif mode == "wrap":
            n = max(len(self), len(rhythm))
        elif mode == "lcm":
            n = lcm(len(self), len(rhythm))
        else:
            raise ValueError(f"Unrecognized mode: {mode}")

        mapped = Seq()
        for i in range(n):
            mel_note = self.notes[i%len(self)][1].copy()
            t, rhy_note = rhythm.notes[i%len(rhythm)]
            t += rhythm.dur * (i // len(rhythm))
            mel_note.dur = rhy_note.dur
            mel_note.vel = rhy_note.vel # Apply rhythm velocity
            mapped.add(mel_note, t)
        m, r = divmod(n, len(rhythm))
        if r == 0:
            # The duration of the mapped sequence is set
            # to a multiple of the duration of the rhythm sequence
            mapped.dur = m * rhythm.dur
            mapped.head = mapped.dur
        
        return mapped


    def __and__(self, other: Seq) -> Seq:
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
            new_sequence.dur = 0
            for _ in range(factor):
                new_sequence.add(self)
            
            return new_sequence
        else: raise TypeError
    
    def __truediv__(self, factor: Union[int, float]):
        new_sequence = self.copy()
        new_sequence.stretch(1/factor)
        return new_sequence
    
    def __rshift__(self, offset: Union[int, float]) -> Seq:
        copy = self.copy()
        copy.shift(offset)
        return copy

    def __lshift__(self, offset) -> Seq:
        return self.__rshift__(-offset)
    
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
        return self.copy().transpose(semitones) if semitones else self

    def __setitem__(self, index, newvalue):
        if isinstance(newvalue, Note):
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
                if stop == None: stop = self.dur
                l = stop-start
                assert l > 0.0
                new_seq = Seq()
                for t,n in self.notes:
                    if t + n.dur >= start and t < stop:
                        new_seq.notes.append( (t-start, n) )
                new_seq.dur = l
                new_seq.crop()
                return new_seq
            else:
                new_seq = Seq()
                if start == None: start = 0
                offset = self.notes[start][0]
                new_seq.notes = [(t-offset, n.copy()) for t,n in self.notes[index]]
                new_seq.dur = new_seq.notes[-1][0] + new_seq.notes[-1][1].dur
                return new_seq
    
    def __delitem__(self, index):
        del self.notes[index]
    
    def __len__(self):
        """Returns the number of notes in the sequence"""
        return len(self.notes)
    
    # def __lt__(self, other):
    #     return self.length < other.length
    
    def __eq__(self, other):
        return \
            abs(self.dur - other.dur) < 0.001 \
            and self.notes == other.notes

    # def __str__(self):
    #     return str(self.notes)
    
    def __repr__(self):
        notes_repr = ', '.join([str(tn) for tn in self.notes])
        return f"Seq({notes_repr}, dur={self.dur})"





# class Song():

#     def __init__(self):
#         self.tempo = 120
#         self.time_signature = (4, 4)
#         self.tracks = []





Element = Union[Note, Chord, Sil, Seq]


def split_elements(seq_string):
    """Split symbolic string sequence in its root sub-elements"""
    seq_string = seq_string.strip()
    op_depth = 0
    elements = []
    elt_start = 0
    for i in range(len(seq_string)):
        if seq_string[i] in "<{[(":
            # Check for coalesced operators (ex: "[a b c][d e f]")
            if op_depth == 0 and i > 0 and seq_string[i-1] != ' ':
                elements.append(seq_string[elt_start:i])
                elt_start = i
            op_depth += 1
        elif seq_string[i] in ">}])":
            # Check if there is a prepended modifier
            op_depth -= 1
        
        if op_depth == 0 and seq_string[i].isspace():
            # Skip multi-spaces
            if i > 0 and seq_string[i-1].isspace():
                pass
            else:
                elements.append(seq_string[elt_start:i])
            elt_start = i+1
    
    elements.append(seq_string[elt_start:])
    return elements


def apply_modifiers(elt: Element, modifiers: str) -> Element:
    """
    Apply the modifiers to the given element

    Args:
        modifiers (str)

    Modifiers:
        *0.5    stretch by 0.5
        %       gate
        ^       transpose
        x       multiply (conflict with roman notation)
        ?       existence
        /       arpeggiate up
        \\      arpeggiate down
        s       stutter "s2,0.2" (2 stutter with 0.2 probability)
        r       (randomize) shuffle sequence
        
        #       Sequence index (spacial)
    """
    int_float_or_frac = r"(\d*\.?\d+(?:\/\d*\.?\d+)?)"

    while modifiers:
        # '*' Stretch modifier, followed by an int, a float or a fraction
        match = re.match(r"\*" + int_float_or_frac, modifiers)
        if match:
            elt.stretch(eval(match[1]))
            modifiers = modifiers[match.end():]
            continue

        # '%' Gate modifier, followed by an int, a float or a fraction
        match = re.match(r"%" + int_float_or_frac, modifiers)
        if match:
            if isinstance(elt, Note):
                elt.stretch(eval(match[1]))
            else:
                elt.gate(eval(match[1]))
            modifiers = modifiers[match.end():]
            continue

        # '^' Transpose modifier
        match = re.match(r"\^(-?\d+)", modifiers)
        if match:
            elt.transpose(int(match[1]))
            modifiers = modifiers[match.end():]
            continue
        
        # 'x' Multiply modifier
        match = re.match(r"x(\d+)", modifiers)
        if match:
            new_sequence = Seq()
            for _ in range(int(match[1])):
                new_sequence.add(elt)
            elt = new_sequence
            modifiers = modifiers[match.end():]
            continue

        # '?' Existence modifier, followed by a float or a fraction
        match = re.match(r"\?" + int_float_or_frac, modifiers)
        if match:
            prob = min(eval(match[1]), 1.0) # limit prob to 1.0
            if prob < random.random():
                elt *= 0
            modifiers = modifiers[match.end():]
            continue
        
        # '/' Arpeggiate up modifiers (only applies to Chords)
        match = re.match(r"/(\d+)?", modifiers)
        if match and isinstance(elt, Chord):
            n = int(match[1]) if match[1] else 1
            elt = elt.arp(n, mode="up")
            modifiers = modifiers[match.end():]
            continue
        
        # '\' (or '\\') Arpeggiate down modifiers (only applies to Chords)
        match = re.match(r"\\(\d+)?", modifiers)
        if match and isinstance(elt, Chord):
            n = int(match[1]) if match[1] else 1
            elt = elt.arp(n, mode="down")
            modifiers = modifiers[match.end():]
            continue
        
        # 's' Stutter modifiers (only applies to Chords)
        # has 2 parameters : "s2,0.2" (2 stutter with 0.2 probability)
        match = re.match(r"s(\d+)(?:," + int_float_or_frac + ")?", modifiers)
        if match:
            if isinstance(elt, Seq):
                elt.stutter(int(match[1]), eval(match[2]) if match[2] else 1.0)
            else:
                if match[2] and random.random() > eval(match[2]):
                    pass
                else:
                    elt = (elt * int(match[1])).stretch(1/int(match[1]))
            modifiers = modifiers[match.end():]
            continue

        # Shuffle sequence
        match = re.match(r"r", modifiers)
        if match:
            if isinstance(elt, Seq):
                elt.shuffle()
            modifiers = modifiers[match.end():]
            continue
        
        modifiers = modifiers[1:]

    return elt


def parse_element(elt_string) -> Element:
    """
    Parse a single element (everything that is not a group).

    Ex:

    
    """

    match = re.match(NOTE_CHORD_PATTERN, elt_string)
    if match:
        pitch = str2pitch(match[0])
        is_chord = match[2][0].isupper()
        if is_chord:
            chord_type = (match[4] or '') + (match[5] or '')
            pitches = ( pitch + i for i in chord_intervals[chord_type] )
            elt = Chord(*pitches)
        else:
            elt = Note(pitch)
        modifiers = elt_string[match.end():]
        elt = apply_modifiers(elt, modifiers)
        elt.string = elt_string
        return elt

    match = re.match(ROMAN_DEGREE_PATTERN, elt_string)
    # match := _match_degree_roman(elt_string)
    if match:
        scl = env.scale if env.scale else Scl("chromatic", 'c')
        degree = roman2num[match[2].lower()]
        # if degree > len(scl.scale):
            #raise ValueError(f"Scale doesn't have a {match[2].upper()}th degree")
        oct_off = _get_octave(match[1]) - env.default_octave
        
        # Single Note
        if match[2].islower():
            elt = Note(scl.getDegree(degree))^(12*oct_off)
        
        # Chords
        elif match[3] == '7':
            elt = scl.seventh(degree)^(12*oct_off)
        
        else:
            elt = scl.triad(degree)^(12*oct_off)
        modifiers = elt_string[match.end():]
        elt = apply_modifiers(elt, modifiers)
        elt.string = elt_string
        return elt
    
    match = re.match(SILENCE_PATTERN, elt_string)
    if match:
        elt = Sil(len(match[0]))
        modifiers = elt_string[match.end():]
        elt = apply_modifiers(elt, modifiers)
        elt.string = elt_string
        return elt

    match = re.match(MIDI_PITCH_PATTERN, elt_string)
    if match:
        pitch = int(match[1])
        elt = Note(pitch)
        modifiers = elt_string[match.end():]
        elt = apply_modifiers(elt, modifiers)
        elt.string = elt_string
        return elt


def _match_degree_roman(string: str) -> str:
    """Match with a roman numeral (scale degree), ignore the case"""
    for pattern in roman2num.keys():
        if match := re.match(pattern, string, flags=re.IGNORECASE):
            return match[1]
    return ""


def _parse_fn_default(seq_string: str, modifiers: str) -> Tuple[Element, str]:
    """
    Add all sub-elements in a single Sequence
    Return a single Sequence

    All _parse_fn_* functions should return a tuple with
    the element or sequence resulting from this function,
    the updated seq_string
    """
    seq = Seq()
    string_elts = []
    for string_elt in split_elements(seq_string):
        elt, updated_string_elt = _parse(string_elt)
        seq.add(elt)
        string_elts.append(updated_string_elt)
    seq = apply_modifiers(seq, modifiers)
    return seq, f"({' '.join(string_elts)}){modifiers}"


def _parse_fn_sync(seq_string: str, modifiers: str) -> Tuple[Element, str]:
    """All elements are played at the same time"""
    seq = Seq()
    string_elts = []
    for string_elt in split_elements(seq_string):
        elt, updated_string_elt = _parse(string_elt)
        seq.merge(elt)
        string_elts.append(updated_string_elt)
    seq = apply_modifiers(seq, modifiers)
    return seq, f"[{' '.join(string_elts)}]{modifiers}"


def _parse_fn_tuplet(seq_string: str) -> Tuple[Element, str]:
    """
    All notes duration are divided by the number of notes in tuplet

    No modifiers should be provided to tuplet groups.
    To apply modifiers to a tuplet group you need to use parentesis :
    Ex: (a_b_c)%2
    """
    string_elts = seq_string.split('_')
    seq = Seq()
    updated_string_elts = []
    for string_elt in string_elts:
        elt, updated_string_elt = _parse(string_elt)
        seq.add(elt)
        updated_string_elts.append(updated_string_elt)
    seq.stretch(1/len(string_elts))
    return seq, '_'.join(updated_string_elts)


def _parse_fn_sequencial(seq_string: str, modifiers: str) -> Tuple[Element, str]:
    """Return the `seq_i`-th element in the group"""
    match_seq_i = re.match(r"#(\d+)", modifiers)
    if match_seq_i:
        seq_i = int(match_seq_i[1])
        modifiers = modifiers[:match_seq_i.start()] + modifiers[match_seq_i.end():]
    else:
        seq_i = 0
    string_elts = split_elements(seq_string)
    elt, updated_substring = _parse(string_elts[seq_i])
    elt = apply_modifiers(elt, modifiers)
    string_elts[seq_i] = updated_substring
    seq_i = (seq_i + 1) % len(string_elts)
    return elt, f"<{' '.join(string_elts)}>#{seq_i}{modifiers}"


def _parse_fn_schroedinger(seq_string: str, modifiers: str) -> Tuple[Element, str]:
    string_elts = split_elements(seq_string)
    prob_weights = []
    for string_elt in string_elts:
        match = re.search(r":(\d*\.?\d+(?:\/\d*\.?\d+)?)$", string_elt)
        prob_weights.append(eval(match[1]) if match else 1)
    sum_weights = sum(prob_weights)
    keeper = None; keeper_idx = -1
    updated_string_elt = ""
    prob = 0
    for i, string_elt in enumerate(string_elts):
        prob += prob_weights[i] / sum_weights
        if random.random() < prob:
            keeper_idx = i
            keeper, updated_string_elt = _parse(string_elt)
            break
    string_elts[keeper_idx] = updated_string_elt
    keeper = apply_modifiers(keeper, modifiers)
    return keeper, f"{{{' '.join(string_elts)}}}{modifiers}"



def _parse(seq_string) -> Tuple[Element, str]:
    # Default group
    match = re.fullmatch(r"\((.+)\)(\S*)", seq_string, re.DOTALL)
    if match:
        return _parse_fn_default(match[1], match[2])

    # Chord group
    match = re.fullmatch(r"\[(.+)\](\S*)", seq_string, re.DOTALL)
    if match:
        return _parse_fn_sync(match[1], match[2])

    # Sequecial group
    match = re.fullmatch(r"<(.+)>(\S*)", seq_string, re.DOTALL)
    if match:
        return _parse_fn_sequencial(match[1], match[2])

    # Schroedinger group
    match = re.fullmatch(r"{(.+)}(\S*)", seq_string, re.DOTALL) # TODO
    if match:
        return _parse_fn_schroedinger(match[1], match[2])

    # Tuplet group
    if '_' in seq_string:
        return _parse_fn_tuplet(seq_string)

    try:
        elt = parse_element(seq_string)
        return elt, seq_string
    except:
        raise ValueError


def parse(seq_string) -> Tuple[Element, str]:
    """Parse a symbolic string sequence"""
    seq_string = seq_string.strip()
    if len(split_elements(seq_string)) > 1:
        # Add explicit append operator
        seq_string = '(' + seq_string + ')'
    seq, updated_string = _parse(seq_string)
    seq.string = updated_string
    return seq, updated_string
