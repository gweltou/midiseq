#from rtmidi import Message
import random
import re
from scales import noteToPitch, Scale



note_length = 1/4

def setNoteLen(d):
    global note_length
    """ Set default note length """
    note_length = d




class Note():

    def __init__(self, pitch, dur=1, vel=127, prob=1):
        if type(pitch) == str:
            pitch = noteToPitch(pitch)
        elif type(pitch) != int:
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        elif type(pitch) == int and (pitch < 0 or pitch > 127):
            raise TypeError("Pitch must be an integer in range [0, 127], got {}".format(pitch))
        self.pitch = min(127, max(0, pitch))
        self.dur = dur * note_length
        self.vel = vel
        self.prob = prob
    

    def __add__(self, other):
        s = Seq()
        s.add(self)
        s.add(other)
        s.length = self.dur + other.dur
        return s


    def __mul__(self, number):
        if type(number) != int:
            raise TypeError
        s = Seq()
        for _ in range(number):
            s.add(self.copy())
        s.length = self.dur * number
        return s
        

    def copy(self):
        n = Note(self.pitch, self.dur, self.vel, self.prob)
        n.dur = self.dur # Overrides the note_length multiplier
        return n


    def __str__(self):
        return "{} {} {}".format(self.pitch, self.dur, self.vel)
    
    def __repr__(self):
        args = "{},{}".format(self.pitch, self.dur)
        if self.vel != 127:
            args += ",{}".format(self.vel)
        if self.prob != 1:
            args += ",{}".format(self.prob)
        return "Note({})".format(args)




class Grid():
    """
        General Midi drums note mapping :
        35 Bass Drum 2
        36 Bass Drum 1
        37 Side Stick
        38 Snare Drum 1 *
        39 Hand Clap    *
        40 Snare Drum 2 *
        41 Low Tom 2
        42 Closed Hi-hat *
        43 Low Tom 1
        44 Pedal Hi-hat
        45 Mid Tom 2
        46 Open Hi-hat
        47 Mid Tom 1
        48 High Tom 2
        49 Crash Cymbal 1
        50 High Tom 1
        51 Ride Cymbal 1
    """
    
    def __init__(self, nsub=16, length=1):
        self.grid = [ set() for _ in range(nsub) ]
        self.length = length


    #def gridRepeat(self, pattern, )

    def repeat(self, note, div, offset=0, preserve=False):
        """
            Repeats a note at regular intervals

            Parameters
            ----------
                note (int/Note)
                    midi note [0-127] or Note instance
                division (int)
                    the note will be repeated every division of the grid
                offset (int)
                    offset beats in grid
                preserve (bool)
                    if True, will not overwrite if there's already a note registered for this beat
        """
        assert div > 0
        assert offset < len(self.grid)
        if type(note) != Note:
            note = Note(note, 0.1)

        i = offset
        while i < len(self.grid):
            if not preserve:
                self.grid[i].add(note.copy())
            i += div
    

    def clear(self):
        self.grid = [ set() for _ in range(len(self.grid)) ]


    def resize(self, new_size):
        new_grid = [ set() for _ in range(new_size) ]

        for i, col in enumerate(self.grid):
            new_i = round(new_size * i/len(self.grid))
            for note in col:
                new_grid[new_i].add(note)
        
        self.grid = new_grid


    def euclid(self, note, k, offset=0):
        """ Euclidian rythm """
        if type(note) != Note:
            note = Note(note, dur=0.1)
        n = len(self.grid)
        offset = offset % n
        onsets = [(offset+round(n*i/k))%n for i in range(k)]
        # print(onsets)
        for i in onsets:
            self.grid[i].add(note.copy())

        # grid = [ 'x' if i in onsets else '.' for i in range(n) ]
        # print(grid)


    def toSeq(self):
        s = Seq()
        s.length = self.length
        step = self.length / len(self.grid)
        head = 0.0
        for col in self.grid:
            for note in col:
                s.add(note, head)
            head += step
        return s


    def getMidiMessages(self, channel=1):
        return self.toSeq().getMidiMessages(channel)


    def __str__(self):
        s = '[ '
        for b in [str(len(c)) if c else '.' for c in self.grid]:
            s += b + ' '
        s += ']'
        return s
    

    def __len__(self):
        return len(self.grid)




class Seq():
    """ 
        (61, 15, 12, 0, (0, 0, 0, 54), 60)

    """

    def __init__(self, notes=None, length=1):
        self.head = 0.0     # Recording head
        self.length = length
        self.scale = None
        self.tonic = 60
        self._dirty = True
        self.notes = []
        if notes:
            self.addNotes(notes)
        # self.next = None    # Plug a sequence to be played after this one


    def add(self, other, head=-1):
        """ Add notes or whole sequences starting from head position
            This will grow the sequence's length if necessary
        """
        if head >= 0:
            self.head = head
        if type(other) == Note:
            self.notes.append( (self.head, other) )
            self.head += other.dur
            self.length = max(self.length, self.head)
            self._dirty = True
        elif type(other) == type(self):
            other = other.copy()
            for (t, note) in other.notes:
                self.notes.append( (self.head + t, note) )
            self.head += other.length
            self.length = max(self.length, self.head)
            self._dirty = True
        else:
            raise TypeError("Only notes or sequences can be added to a sequence")
    

    def addNotes(self, notes, dur=1, vel=127):
        """
            Add many notes sequencially

            Parameters
            ----------
                notes:
                    A list of note pitches, can be a string or an iterable
                    Ex: "c# d f2 do re mi" or (61, 62, 29, 60, 62, 64)
        """
        if type(notes) == str:
            for note in getNotesFromString(notes, dur, vel):
                self.add(note)
        elif hasattr(notes, '__iter__'):
            # notes = [Note(pitch, dur, vel) for pitch in notes]
            for pitch in notes:
                if type(pitch) in (tuple, list):
                    self.addNotes(pitch, dur/len(pitch), vel)
                elif pitch == 0:
                    self.addSil(dur)
                else:
                    self.add(Note(pitch, dur, vel))
        else:
            raise TypeError("argument `notes` must be a string or an iterable")


    def addSil(self, dur=0.25):
        """ Add a silence to the sequence, growing its length if necessary.
        """
        self.head += dur
        self.length = max(self.length, self.head)


    def addChordNotes(self, notes, dur=0.25, vel=127):
        """ Add a chord with the list of given notes/pitches """
        if type(notes) == str:
            notes = getNotesFromString(notes)
        elif hasattr(notes, '__iter__'):
            notes = [Note(pitch, dur, vel) for pitch in notes]
        head = self.head
        for n in notes:
            if type(n) != Note:
                n = Note(n, dur, vel)
            self.add(n, head)


    def fillSweep(self, from_pitch=42, to_pitch=64, num=4):
        if type(from_pitch) == str:
            from_pitch = noteToPitch(from_pitch)
        if type(to_pitch) == str:
            to_pitch = noteToPitch(to_pitch)
        if type(self.scale) == Scale:
            from_pitch = self.scale.getClosest(from_pitch)
        pitch_step = int((to_pitch - from_pitch) / num)
        time_step = (self.length - self.head) / num
        head = self.head
        for i in range(num):
            pitch = from_pitch + i*pitch_step
            if type(self.scale) == Scale:
                pitch = self.scale.getClosest(pitch)
            self.add( Note(pitch, time_step), head )
            head += time_step

        self.head = self.length


    def fillRandom(self, dur=0.25, min=36, max=90):
        """ Fill the sequence with random notes, starting from head position.
            The generated notes will be choosen from the current musical scale.
            This will not change the sequence's length.
        """
        while self.head + 0.001 < self.length:
            if type(self.scale) == Scale:
                pitch = self.scale.getClosest(random.randint(min, max))
            else:
                pitch = random.randint(min, max)
            self.add( Note(pitch, dur) )
    

    def fillGaussianWalk(self, dur=0.25, dev=2):
        """ 
            Fill the sequence with random notes, starting from head position.
            In a random walk, each new note can go up, down or keep the same pitch as the previous note.
            The generated notes will be choosen from the current musical scale, starting with the root note.
            This will not change the sequence's length.

            Parameters
            ----------
                start_note : int [0-127]
                    The random walk will start with this note
                dur : float
                    Duration of the notes
                dev : float
                    Standard deviation
        """
        if self.head + dur > self.length:
            return
        
        # self.notes.append( (self.head, Note(self.tonic, dur)) )
        # self.head += dur
        self.add(Note(self.tonic, dur))
        prev = 0
        while self.head + 0.001 < self.length:
            prev_degree = prev + round(random.gauss(0, dev))
            if type(self.scale) == Scale:
                pitch = self.scale.getDegree(prev_degree)
            else:
                pitch = 60 + prev_degree
            prev = prev_degree
            # self.notes.append( (self.head, Note(pitch, dur)) )
            # self.head += dur
            self.add(Note(pitch, dur))
    

    def replacePitch(self, old, new):
        """ Replace notes with given pitch to a new pitch """
        if type(old) == str:
            old = noteToPitch(old)
        if type(new) == str:
            new = noteToPitch(new)
        for note in self.notes:
            if note.pitch == old:
                note.pitch == new


    def map(self, grid, duty_cycle=0.2):
        # XXX: Not usefull right now
        beat_len = (self.length - self.head) / len(grid)
        note_dur = duty_cycle * beat_len
        for pitch in grid:
            if 0 < pitch <= 127:
                self.add(Note(pitch, note_dur))
                self.head += beat_len - note_dur
            else:
                self.head += beat_len


    def stretch(self, factor, stretch_notes_dur=True):
        """ Stretch sequence in time """
        for i in range(len(self.notes)):
            t, note = self.notes[i]
            if stretch_notes_dur:
                note.dur *= factor
            self.notes[i] = t * factor, note
        self.length *= factor


    def transpose(self, semitones):
        """ Transpose all notes in sequence by semitones. """
        for _, note in self.notes:
            note.pitch += semitones


    def expand(self, factor):
        """ Expand or compress notes pitches around the mean value of the whole sequence
        """
        # XXX: Should it preserve scale ?
        sum = 0
        for _, note in self.notes:
            sum += note.pitch
        mean = sum / len(self.notes)

        for _, note in self.notes:
            diff = note.pitch - mean
            note.pitch = round(mean + diff * factor)
            note.pitch = min(255, max(0, note.pitch))
    

    def splitNotes(self, n=2):
        if type(n) != int or n <= 0:
            raise TypeError("number of splits should be equal to 2 or greater ")
        
        orig = self.notes[:]
        self.clear()
        for t, note in orig:
            split_dur = note.dur / n
            for i in range(n):
                self.notes.append( (t + i * split_dur, Note(note.pitch, split_dur, note.vel, note.prob)) )


    def decimate(self, prob=0.2):
        """ Erase notes randomly based on the given probability
        """
        orig = self.notes[:]
        self.clear()
        for t, note in orig:
            if random.random() > prob:
                self.notes.append( (t, note) )
    

    def humanize(self, tfactor=0.02, veldev=10):
        """ Randomly changes the notes time and duration """
        new_notes = []
        for t, note in self.notes:
            t = t + 2 * (random.random()-0.5) * tfactor
            note.dur = note.dur + random.random() * tfactor
            note.vel = int(100 + random.gauss(0, veldev))
            note.vel = min(127, max(0, note.vel))
            new_notes.append( (t, note) )
        self.notes = new_notes
        self._dirty = True


    def clear(self):
        self.notes.clear()
        self.head = 0.0
    

    def copy(self):
        new = Seq()
        new.notes = [ (t, note.copy()) for t, note in self.notes ]
        new.length = self.length
        new.head = self.head
        new.tonic = self.tonic
        new.scale = self.scale
        # new.transpose = self.transpose
        new._dirty = self._dirty
        return new


    # def freeze(self):
    #     new_notes = []
    #     for pos, note in self.notes:
    #         # End of sequence
    #         if pos >= self.length:
    #             break
    #         # Truncate last note if necesary
    #         if pos + note.dur > self.length:
    #             note = note.copy()
    #             note.dur = self.length - pos
    #         new_note = note.copy()
    #         new_note.pitch = self.getClosestNoteInScale(note.pitch)
    #         new_notes.append( (pos, new_note) )
    #     self.notes = new_notes
    #     # self.transpose = 0
    #     return self


    def crop(self):
        """ Shorten or delete notes before time 0 and after the sequence's length """
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


    def shift(self, dt, loop=False):
        """ Shift note onset times by a given delta time

            Parameters
            ----------
                loop:
                    if True, notes that were pushed out of the sequence get appendend to the other side
        """
        new_notes = []
        for t, n in self.notes:
            new_notes.append( (t+dt, n) )
        self.notes = new_notes


    def getMidiMessages(self, channel=1):
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
            note_on = [0x90, note.pitch, note.vel]
            note_off = [0x80, note.pitch, 0]
            midi_seq.append( (pos, note_on) )
            midi_seq.append( (pos + note.dur, note_off) )

        midi_seq.sort(key=lambda x: x[0])
        return midi_seq
    

    def __add__(self, other):
        if not type(other) in (type(self), Note):
            raise TypeError("Can only add sequences together or notes to sequences")
        
        new_seq = self.copy()
        new_seq.add(other)
        return new_seq
    

    def __mul__(self, n):
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

    
    def __rshift__(self, other):
        if isinstance(other, float):
            copy = self.copy()
            copy.shift(other)
            return copy


    def __lshift__(self, other):
        if isinstance(other, float):
            return self.__rshift__(-other)


    def __str__(self):
        return str(self.notes)
    
    def __len__(self):
        return len(self.notes)



####  ALIASES

n = Note
s = Seq


###########
## UTILS ##
###########


def getNotesFromString(s, dur=1, vel=127):
    if type(s) != str: raise TypeError('Argument must be a string. Ex: "do re mi" or "60 62 64"')
    
    notes = []
    for t in s.split():
        pitch = noteToPitch(t)
        if pitch >= 0:
            notes.append( Note(pitch, dur, vel) )

    return notes
