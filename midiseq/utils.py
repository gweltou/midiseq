from typing import Union, Optional
import random

from .elements import Note, Sil, Chord, Seq, Scl, str2pitch, parse, parse_element
import midiseq.env as env



def pattern(
        pat: str,
        note: Union[int, str, Note, Chord],
        vel: Optional[int]=None) -> Seq:
    """
        Build a Sequence from a Sonic Pi type pattern
        Ex: pattern("x--- --X- --x- -X--", 36)
    """
    seq = Seq()
    if isinstance(note, int):
        note = Note(note)
    elif isinstance(note, str):
        note = parse_element(note)
    if vel:
        note.vel = vel
    for c in pat:
        if c == 'x':
            seq.add(note.copy())
        elif c == 'X':
            n = note.copy()
            n.vel = 127
            seq.add(n)
        elif c == '-':
            seq.add(Sil())
    return seq


def noteRange(note_from=36, note_to=60, dur=1):
    s = Seq()
    for pitch in range(note_from, note_to):
        s.add(Note(pitch, dur=dur))
    return s



def noob2seq(noob: str):
    """ https://noobnotes.net/
        https://www.piano-letters.com/letter-notes
    """

    o = env.default_octave
    s = noob.replace('^', str(o+1)).replace('*', str(o+2)) # Octave transpose, up
    s = s.replace('.', str(o-1)).replace('_', str(o-2)) # Octave transpose, down
    s = s.replace('-', '_') # Tuplets
    s = ' '.join(s.split()).lower()
    return parse(s)[0]



###############################################################################
####                       Random sequence generators                      ####
###############################################################################


def rnd(n=8, lo=36, hi=84, silprob=0.0, notedur=1.0, scl:Scl=None) -> Seq:
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
            scl : Scl (Scale)
                Constrain generated notes to the given scale
    """
    if not scl:
        scl = env.scale or Scl("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = scl.getClosest(random.randint(lo, hi))
            s.add(Note(pitch, notedur))
        else:
            s.add(Sil(notedur))
    return s



def rndDur(
        dur=1.0,
        lo=36, hi=84,
        durs=[0.5, 1, 2],
        silprob=0.0,
        scl:Scl=None
    ) -> Seq:
    """
    """
    assert dur > max(durs) * env.note_dur
    if not scl:
        scl = env.scale or Scl("chromatic", 'c')
    durs = [d * env.note_dur for d in durs]

    picks = []
    while len(durs) > 0 and sum(picks) < dur:
        pick = random.choice(durs)
        if sum(picks) + pick > dur:
            durs.remove(pick)
        else:
            picks.append(pick)
    s = Seq()

    picks = [d / env.note_dur for d in picks]
    for pick in picks:
        if not silprob or random.random() > silprob:
            pitch = scl.getClosest(random.randint(lo, hi))
            s.add(Note(pitch, dur=pick))
        else:
            s.add(Sil(pick))
    if s.dur < dur:
        s.dur = dur
        s.head = dur
    return s



def rndWalk(
        n=8,
        start: Union[str,int]=None,
        steps=[-2,-1,0,1,2],
        silprob=0.0,
        notedur=1.0,
        skip_first=False,
        scl:Scl=None
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
            scl : Scl (Scale)
                Constrain generated notes to the given scale
    """
    if scl:
        old_scl = env.scale
        env.scale = scl
    
    if not start:
        start = env.scale.tonic
    if isinstance(start, str):
        start = parse_element(start).pitch
    pitch = env.scale.getClosest(start)
    if skip_first:
        pitch = env.scale.getDegreeFrom(pitch, random.choice(steps))
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            s.add(Note(pitch, notedur))
            pitch = env.scale.getDegreeFrom(pitch, random.choice(steps))
        else:
            s.add(Sil(notedur))
    
    if scl:
        env.scale = old_scl
    return s



def rndGauss(n=8, mean=60, dev=3, silprob=0.0, notedur=1.0, scl:Scl=None) -> Seq:
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
            scl : Scl (Scale)
                Constrain generated notes to the given scale
    """
    if not scl:
        scl = env.scale or Scl("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = scl.getDegreeFrom(mean, round(random.gauss(0, dev)))
            s.add(Note(pitch, notedur))
        else:
            s.add(Sil(notedur))
    return s



def rndPick(sequence: Seq, n=8, sil=True) -> Seq:
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



def rndGrid(note=36, n=4, grid=16) -> Seq:
    """
        Fill a sequence randomly with a given number of the same note
    """
    elts = [Note(note)] * n + [Sil() * (grid-n)]
    random.shuffle(elts)
    s = Seq()
    for e in elts:
        s.add(e)
    return s



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
    s = Seq(dur=grid*env.note_dur)
    for i in onsets:
        t = i * env.note_dur
        s.add(note.copy(), head=t)
    s.head = s.dur
    return s



def lcm(*seqs, tolerance=0.0001):
    """ Combine two or more sequence to build
        the least common multiplier of them all.
        You better use quantized sequences !
    """
    def samelen(seqs):
        first = seqs[0]
        for s in seqs[1:]:
            if abs(s.dur - first.dur) > tolerance:
                return False
        return True

    seqs_init = [ parse(s)[0] if isinstance(s, str) else s for s in seqs ]
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