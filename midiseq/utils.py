from typing import Optional, Union
import re
import random

from .elements import Note, Sil, Chord, Seq, Scl, str2pitch, str2elt, str2seq
import midiseq.env as env



def pattern(pat: str, note: Union[int, str, Note, Chord], vel=100) -> Seq:
    """
        Build a Sequence from a Sonic Pi type pattern
        Ex: pattern("x--- --x- --x- -x--", 36)
    """
    seq = Seq()
    if isinstance(note, int):
        note = Note(note)
    elif isinstance(note, str):
        note = str2elt(note)
    if isinstance(note, Note):
        note.vel = vel
    for c in pat:
        if c == 'x':
            seq.add(note)
        elif c == '-':
            seq.add(Sil())
    return seq



def noob2seq(noob: str):
    """ https://noobnotes.net/
        https://www.piano-letters.com/letter-notes
    """

    o = env.default_octave
    s = noob.replace('^', str(o+1)).replace('*', str(o+2)) # Octave transpose, up
    s = s.replace('.', str(o-1)).replace('_', str(o-2)) # Octave transpose, down
    s = s.replace('-', '_') # Tuplets
    s = ' '.join(s.split()).lower()
    return str2seq(s)



###############################################################################
####                       Random sequence generators                      ####
###############################################################################


def rnd(n=4, lo=36, hi=84, silprob=0.0, notedur=1.0, scale:Scl=None) -> Seq:
    """ Generate a sequence of random notes

        Parameters
        ----------
            n : int
                Number of notes to generate
            lo : int
                Minimum MIDI pitch boundary
            hi : int
                Maximum MIDI pitch boundary
            silprob : float
                Silence probability [0.0-1.0]
            scale : Scale
                Constrain generated notes to the given scale
    """
    if not scale:
        scale = env.scale if env.scale else Scl("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = env.scale.getClosest(random.randint(lo, hi))
            s.add(Note(pitch, notedur))
        else:
            s.add(Sil(notedur))
    return s



def rndDur(
        dur=1.0,
        lo=36, hi=84,
        durs=[0.25, 0.5, 1, 2],
        silprob=0.0,
        scale:Scl=None
    ) -> Seq:
    assert dur > max(durs)
    if not scale:
        scale = env.scale if env.scale else Scl("chromatic", 'c')
    durs.sort()
    s = Seq()
    d = random.choice(durs)
    while dur - s.dur > hi(durs):
        if not silprob or random.random() > silprob:
            pitch = env.scale.getClosest(random.randint(lo, hi))
            s.add(Note(pitch, d))
        else:
            s.add(Sil(d))


def rndWalk(
        n=4,
        start: Union[str,int]=60,
        steps=[-3,-2,-1,0,1,2,3],
        silprob=0.0,
        notedur=1.0,
        skip_first=False, scale:Scl=None
    ) -> Seq:
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
                Skip starting note (False by default)
            silprob : float
                Silence probability [0.0-1.0]
            notedur : float
                Duration of generated notes
            scale : Scale
                Constrain generated notes to the given scale
    """
    if not scale:
        scale = env.scale if env.scale else Scl("chromatic", 'c')
    if isinstance(start, str):
        start = str2pitch(start)
    pitch = scale.getClosest(start)
    if skip_first:
        pitch = scale.getDegreeFrom(pitch, random.choice(steps))
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            s.add(Note(pitch, notedur))
            pitch = env.scale.getDegreeFrom(pitch, random.choice(steps))
        else:
            s.add(Sil(notedur))
    return s



def rndGauss(n=4, mean=60, dev=3, silprob=0.0, notedur=1.0, scale:Scl=None) -> Seq:
    """ Generate random notes with a normal distribution around a mean value

        Parameters
        ----------
            n : int
                Number of notes to generate
            mean : int
                Mean pitch value
            dev : float
                Standard deviation
            silprob : float
                Silence probability [0.0-1.0]
            scale : Scale
                Constrain generated notes to the given scale
    """
    if not scale:
        scale = env.scale if env.scale else Scl("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = scale.getDegreeFrom(mean, round(random.gauss(0, dev)))
            s.add(Note(pitch, notedur))
        else:
            s.add(Sil(notedur))
    return s



def rndPick(sequence: Seq, n=4, sil=True) -> Seq:
        """ Pick randomly among previous notes in sequence """
        num_n = len(sequence.notes)
        num_s = len(sequence.silences) if sil else 0
        new_seq = Seq()
        for _ in range(n):
            r = random.randrange(num_n + num_s)
            if r < num_n:
                # Pick a note
                new_seq.add(sequence.notes[r][1])
            else:
                # Pick a silence
                new_seq.add(sequence.silences[r-num_n][1])
        return new_seq



def euclid(note=36, n=4, grid=16, offset=0) -> Seq:
    """ Generate a Euclidian rythm sequence

        Parameters
        ----------
            note : Union[Note, int, str]
                Note to be repeated
            n : int
                Number of notes to generate
            grid : int
                Size of the grid (should be bigger than `n`)
            offset : int
                Number of rests before first note
    """
    if not isinstance(note, Note):
        note = Note(note)
    
    offset = offset % grid
    onsets = [ (offset+round(grid*i/n)) % grid for i in range(n) ]
    s = Seq()
    for i in onsets:
        t = i * env.note_dur
        s.add(note.copy(), head=t)
    return s



def lcm(*seqs):
    """ Combine two or more sequence to build
        the least common multiplier of them all.
        You better use quantized sequences !
    """
    def samelen(seqs):
        first = seqs[0]
        for s in seqs[1:]:
            if s.dur != first.dur:
                return False
        return True

    seqs_init = [ str2seq(s) if isinstance(s, str) else s for s in seqs ]
    seqs = [ s.copy() for s in seqs_init ]
    while not samelen(seqs):
        # Find index of shortest seq:
        shortest = (-1, 9999)
        for i, s in enumerate(seqs):
            if s.dur < shortest[1]:
                shortest = (i, s.dur)
        # Extend shortest seq
        seqs[shortest[0]] += seqs_init[shortest[0]]
    # Merge all sequences
    merged = seqs[0]
    for s in seqs[1:]:
        merged &= s
    return merged