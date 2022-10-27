import rtmidi
import random
from scales import *
from utils import noteToPitch




class Note():

    def __init__(self, pitch, dur=1, vel=127, prob=1):
        if type(pitch) == str:
            pitch = noteToPitch(pitch)
        elif type(pitch) != int:
            raise TypeError("Pitch must be an integer in range [0, 127]")
        self.pitch = min(127, max(0, pitch))
        self.dur = dur
        self.vel = vel
        self.prob = prob
    
    def copy(self):
        return Note(self.pitch, self.dur, self.vel, self.prob)

    def __str__(self):
        return "{} {} {}".format(self.pitch, self.dur, self.vel)
    
    def __repr__(self):
        args = "{},{}".format(self.pitch, self.dur)
        if self.vel != 127:
            args += ",{}".format(self.vel)
        if self.prob != 1:
            args += ",{}".format(self.prob)
        return "Note({})".format(args)




class Seq():

    def __init__(self):
        self.notes = []
        self.head = 0.0     # Recording head
        self.length = 0.0
        self.rootnote = 0
        self.scale = scales["chromatic"]
        # self.transpose = 0
        self._dirty = True


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
            other = other.copy().freeze()
            for (t, note) in other.notes:
                self.notes.append( (self.head + t, note) )
            self.head += other.length
            self.length = max(self.length, self.head)
            self._dirty = True
        else:
            raise TypeError("Only notes or sequences can be added to a sequence")
        

    def insert(self, other):
        """ Insert a note or a sequence in the sequence at a given position,
            moving all notes coming after.
            This will grow the sequence's length if necessary.
        """
        pass

    def addNote(self, pitch, dur=0.25, vel=127):
        """ Add a single note to the sequence, growing its length if necessary.
        """
        self.add(Note(pitch, dur, vel))
        

    def addSilence(self, dur=0.25):
        """ Add a silence to the sequence, growing its length if necessary.
        """
        self.head += dur
        self.length = max(self.length, self.head)


    def addChord(self, name, pitch, dur=0.25, vel=127):
        chords = {
            "maj": [0, 4, 7],
            "min": [0, 3, 7],
        }

        if name in chords:
            for semi in chords[name]:
                note = Note(pitch + semi, dur, vel)
                self.notes.append( (self.head, note) )

        self.head += dur
        self.length = max(self.length, self.head)
        self._dirty = True


    def fillRandom(self, dur=0.25):
        """ Fill the sequence with random notes, starting from head position.
            The generated notes will be choosen from the current musical scale.
            This will not change the sequence's length.
        """
        while self.head < self.length:
            pitch = random.randint(40, 90)
            self.notes.append( (self.head, Note(pitch, dur)) )
            self.head += dur
        self._dirty = True
    

    def fillGaussianWalk(self, dur=0.25, dev=2):
        """ Fill the sequence with random notes, starting from head position.
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
        
        self.notes.append( (self.head, Note(self.rootnote, dur)) )
        self.head += dur
        prev = 0
        while self.head < self.length:
            prev_degree = prev + round(random.gauss(0, dev))
            pitch = self.getScaleDegree(prev_degree)
            prev = prev_degree
            self.notes.append( (self.head, Note(pitch, dur)) )
            self.head += dur
        self._dirty = True
    

    def stretch(self, factor):
        """ Stretch sequence in time """
        for i in range(len(self.notes)):
            t, note = self.notes[i]
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


    def setScale(self, scale, rootnote=-1):
        if type(rootnote) == int:
            self.rootnote = min(127, max(0, rootnote))
        elif type(rootnote) == str:
            self.rootnote = noteToPitch(rootnote)
        else:
            raise TypeError("rootnote must be a pitch number [0-127] or a valid note name")

        if type(scale) == str:
            if scale in scales:
                self.scale = scales[scale]
            elif scale in modes:
                self.scale = modes[scale]
            else:
                raise TypeError('scale "{}" is unknown'.format(scale))
        elif type(scale) == list:
            self.scale = scale


    def getScaleDegree(self, n):
        """ get the n-th degree note in the current musical scale, relative to the rootnote
        """
        
        nth_oct, nth_degree = divmod(n, len(self.scale))

        if n >= 0:
            distances = self.scale
        else:  # Negative number
            distances = [ d-12 for d in self.scale]
            nth_oct += 1

        return self.rootnote + 12 * nth_oct + distances[nth_degree]


    # def getClosestNoteInScale(self, pitch):
    #     """ Find closest note in scale.
    #         Lower pitch takes precedence.
    #     """
    #     octave, degree = divmod(pitch, 12)
    #     distances = [s-(degree+self.rootnote)%12 for s in self.scale]
    #     min_dist = 12
    #     for d in distances:
    #         if abs(d) < abs(min_dist):
    #             min_dist = d
        
    #     return 12 * octave + degree + min_dist
    def getClosestNoteInScale(self, pitch):
        """ Find closest note in scale.
            Lower pitch takes precedence.
        """
        octave, degree = divmod(pitch, 12)
        distances = [s-(degree-self.rootnote)%12 for s in self.scale]
        min_dist = 12
        for d in distances:
            if abs(d) < abs(min_dist):
                min_dist = d
        
        return 12 * octave + degree + min_dist


    def clear(self):
        self.notes.clear()
        self.head = 0.0
    

    def copy(self):
        new = Seq()
        new.notes = [ (t, note.copy()) for t, note in self.notes ]
        new.length = self.length
        new.head = self.head
        new.rootnote = self.rootnote
        new.scale = self.scale
        # new.transpose = self.transpose
        new._dirty = self._dirty
        return new


    def freeze(self):
        new_notes = []
        for pos, note in self.notes:
            # End of sequence
            if pos >= self.length:
                break
            # Truncate last note if necesary
            if pos + note.dur > self.length:
                note = note.copy()
                note.dur = self.length - pos
            new_note = note.copy()
            new_note.pitch = self.getClosestNoteInScale(note.pitch)
            new_notes.append( (pos, new_note) )
        self.notes = new_notes
        # self.transpose = 0
        return self


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
            
            pitch = self.getClosestNoteInScale(note.pitch)

            note_on = rtmidi.MidiMessage.noteOn(channel, pitch, note.vel)
            note_off = rtmidi.MidiMessage.noteOff(channel, pitch)
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


    def __str__(self):
        return str(self.notes)
    
    def __len__(self):
        return len(self.notes)
