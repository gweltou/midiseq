from typing import Union
import random

import midiseq.env as env
from .sequence import Note, Sil, Seq, Scale, Chord, str2elt, str2pitch, modes, pattern
from .definitions import *



####  ALIASES
# n = Note
# s = Sil
# c = Chord
# sq = Seq


###############################################################################
####                           Exemple sequences                           ####
###############################################################################

seq_kaini_industries = """
    -g#%1.5 -a#%.5 b_b -g#_b -g#_a# f#_-g# -2b -g#_-f#
    c# -c#%4 f#%2 g#
    -2g#%1.5 -a#_d# -a#_d# -a#_-f# f#_f# -a#_f# g#%.5 g#
    -c# -d#_e# -d# e# b e#_b e#_a# f#
    """
seq_never_gonna_gyu = "a#_+c +c#_a# +f +f +d# . g#_a# +c#_a# +d# +d# +c# +c_a#"
seq_mario = "e_e ._e ._c e_. g . -g"



###############################################################################
####                       Simple sequence generators                      ####
###############################################################################


def rand(n=4, min=36, max=96, silprob=0.0, scale:Scale=None) -> Seq:
    """ Generate a sequence of random notes

        Parameters
        ----------
            n : int
                Number of notes to generate
            min : int
                Minimum midi pitch boundary
            max : int
                Maximum midi pitch boundary
            silprob : float
                Silence probability [0.0-1.0]
            scale : Scale
                Constrain generated notes to the given scale
    """
    if not scale:
        scale = env.SCALE if env.SCALE else Scale("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = env.SCALE.getClosest(random.randint(min, max))
            s.add(Note(pitch))
        else:
            s.add(Sil())
    return s


def randWalk(
        n=4,
        start: Union[str,int]=60,
        steps=[-3,-2,-1,0,1,2,3],
        silprob=0.0,
        skip_first=False, scale:Scale=None
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
            scale : Scale
                Constrain generated notes to the given scale
    """
    if not scale:
        scale = env.SCALE if env.SCALE else Scale("chromatic", 'c')
    if isinstance(start, str):
        start = str2pitch(start)
    pitch = scale.getClosest(start)
    if skip_first:
        pitch = scale.getDegreeFrom(pitch, random.choice(steps))
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            s.add(Note(pitch))
            pitch = env.SCALE.getDegreeFrom(pitch, random.choice(steps))
        else:
            s.add(Sil())
    return s


def randGauss(n=4, mean=60, dev=3, silprob=0.0, scale:Scale=None) -> Seq:
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
        scale = env.SCALE if env.SCALE else Scale("chromatic", 'c')
    s = Seq()
    for _ in range(n):
        if not silprob or random.random() > silprob:
            pitch = scale.getDegreeFrom(mean, round(random.gauss(0, dev)))
            s.add(Note(pitch))
        else:
            s.add(Sil())
    return s

    
def euclid(note=36, n=4, grid=16, offset=0) -> Seq:
    """ Generate a Euclidian rythm sequence

        Parameters
        ----------
            note : Union[Note, int, str]
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
        t = i * env.NOTE_LENGTH
        s.add(note.copy(), head=t)
    return s


def lcm(*seqs):
    """ Combine two or more sequence to build
        the least common multiplier of them all
    """
    def samelen(seqs):
        first = seqs[0]
        for s in seqs[1:]:
            if s.length != first.length:
                return False
        return True

    seqs_init = [ str2elt(s) if isinstance(s, str) else s for s in seqs ]
    seqs = [ s.copy() for s in seqs_init ]
    while not samelen(seqs):
        # Find index of shortest seq:
        shortest = (-1, 9999)
        for i, s in enumerate(seqs):
            if s.length < shortest[1]:
                shortest = (i, s.length)
        # Extend shortest seq
        seqs[shortest[0]] += seqs_init[shortest[0]]
    # Merge all sequences
    merged = seqs[0]
    for s in seqs[1:]:
        merged &= s
    return merged



###############################################################################
####                      Complex sequence generators                      ####
###############################################################################


def gen_pattern(generator, pattern="ABAB"):
    """
        pattern: (str)
            Ex: "ABAB" or "1112"
    """
    while True:
        gen = generator()
        seq = dict()
        for symbol in pattern:
            if not symbol in seq:
                seq[symbol] = next(gen)
            yield seq[symbol]

def gen_chords1():
    d = 0
    while True:
        s = Seq()
        scl = Scale(random.choice(list(modes.keys())))
        s.scale = Scale(scl)
        s.clear()
        for _ in range(4):
            s.add(scl.triad([0, 1, 2, 3][d%3]))
            d+= 1
        s.add(Sil())
        s.stretch(2, False)# *= 2.0
        s.humanize(0.05)
        yield s

def gen_chords2():
    d = 0
    scl = Scale(random.choice(list(modes.keys())))
    while True:
        s = Seq()
        if d%4 == 0:
            scl = Scale(random.choice(list(modes.keys())))
            print(scl)
        chord_prog = [ random.choice(list(range(7))) for _ in range(4) ]
        print(chord_prog)
        for i in chord_prog:
            s.add(scl.triad(i))
        s.add(Sil())
        s.stretch(2, False)# *= 2.0
        d+= 1
        s.humanize(0.01)
        yield s

def gen_chords3():
    # int i = 0
    jumps = [2, 3, 4]
    while True:
        deg = 0
        s = Seq()
        s.scale = Scale("major", "c")
        for _ in range(5):
            off = random.choice(jumps)
            if random.random() < 0.5:
                off = -off
            deg += off
            s.add(s.scale.triad(deg, random.randint(80, 127)), 0.66)
        s.add(s.scale.triad(0, random.randint(80, 120)), 0.66)
        yield s

def gen_tintinnabuli():
    # Tintinnabuli
    note_dur = 1.0
    s = Seq()
    s.scale = Scale("minor", 54)
    for _ in range(16):
        s.clear()
        pitch = s.scale.getDegree(random.gauss(0, 2.5)) + 12
        pitch2 = 54 + random.choice([0, 3, 7, -12])
        s.add(Note(pitch, dur=note_dur))
        s.head=0.0
        s.add(Note(pitch2, dur=note_dur))
        s.length = note_dur + abs(random.gauss(0, 3))
        yield s

def gen_tintinnabuli2():
    note_dur = 0.6
    s = Seq()
    scl = Scale("pentatonic_minor", "e")

    while True:
        s.clear()
        pitch_low = scl.tonic - 12
        pitch_low = scl.getDegreeFrom(pitch_low, random.choice([0, 0, -len(scl), 1, 1, 2, 2]))
        pitch_high = scl.getDegree(random.randrange(len(scl)))
        s.add(Chord((pitch_low, pitch_high)))
        s.length = note_dur + abs(random.gauss(0, 3))
        yield s

def gen_tintinnabuli3():
    note_dur = 0.4
    s = Seq()
    scl = Scale("minor", "e")

    while True:
        s.clear()
        pitch_low = scl.tonic - 12
        pitch_low = scl.getDegreeFrom(pitch_low, random.choice([0, 0, -len(scl), 2, 2, 4, 4]))
        pitch_high = scl.getDegree(random.randrange(len(scl)))
        s.add(Chord((pitch_low, pitch_high)))
        s.length = note_dur + abs(random.gauss(0, 3))
        s.humanize(0.02)
        yield s

def gen_fratres():
    # Tintinnabuli fratres
    # https://www.youtube.com/watch?v=XbykaYwVO0w
    d=2
    main = Scale([0, 1, 3, 4, 6, 8, 9], "do#")
    minor = Scale([0, 3, 7], "la")
    while True:
        s=Seq()
        pitches = ( main.getDegree(0), main.getDegree(2)+24, minor.getClosest(main.getDegree(0)+9) )
        s.add(Chord(pitches), 0.5)
        for i in range(1, d):
            pitches = ( main.getDegree(i), main.getDegree(i+2)+24, minor.getClosest(main.getDegree(i)+9) )
            s.add(Chord(pitches))
        for i in range(-d+1, 0):
            pitches = ( main.getDegree(i), main.getDegree(i+2)+24, minor.getClosest(main.getDegree(i)+9) )
            s.add(Chord(pitches))
        pitches = ( main.getDegree(0), main.getDegree(2)+24, minor.getClosest(main.getDegree(0)+9) )
        s.add(Chord(pitches), 0.5)
        d += 1
        s.stretch(4.0)
        s.humanize()
        yield s
    
def gen_japscale():
    jap = Scale("japanese")
    while True:
        s=Seq() 
        if random.random() < 0.1:
            jap.tonic = random.randrange(42, 54)
        s.add(randGauss(dev=2, scale=jap))
        s.stretch(16, False)
        yield s




###############################################################################
####                            DRUM PATTERNS                              ####
###############################################################################


def drum_8thNoteGrove():
    s = Seq((H, 0) * 4)  # High-hats
    s.merge(Seq((K, 0, 0, 0, Sn, 0, 0, 0)))   # Kick and Snare
    return s*2

def drum_4toTheFloor():
    s = Seq((H, 0) * 4)  # High-hats
    s.merge(Seq( (K, 0, 0, 0) * 2) )   # Kick and Snare
    s.merge(Seq( (0, 0, 0, 0, K, 0, 0, 0) ))
    return s*2

def drum_shuffleGroove():
    s = Seq( (H, 0, H) * 2)   # HH
    s.merge(Seq( (K, 0, 0, Sn, 0, 0) ))    # K & S
    return s*2

def drum_discoGroove():
    s = Seq( ( H, 0, OH, 0) * 2 )
    s.merge( Note(K) + 3 * Sil() + Chord((K, Sn)) + 3 * Sil() )
    return s*2

def drum_halfTimeShuffle():
    s = Seq((H,), length=1)
    s.add(Note(H), 0.72)
    s *= 4
    s.add(Note(K), 0)
    s.add(Note(Sn), 1.27)
    s.add(Note(Sn), 2)
    s.add(Note(Sn), 3.27)
    return s

def drum_funkyDrummer():
    s =  Seq((K, 0, K, 0, Sn,0, K, Sn,0, Sn,K, Sn,Sn,K, 0, Sn))
    s &= Seq((H, H, H, H, H, H, H, OH,H, H, H, H, H, OH,H, H))
    return s

def gen_drum_drunkenDrummer():
    s =     Seq((K, 0, K, 0, 0, 0, K, 0, 0, 0, K, 0, 0, K, 0, 0))
    s.humanize(0.8, 4)
    snares = Seq((0, 0, 0, 0, Sn ,0, 0, Sn, 0, Sn, 0, Sn, Sn, 0, 0, Sn))
    snares.humanize(0.8, 4)
    s.merge(snares)
    hh = Seq((H, H, H, H, H, H, H, 0, H, H, H, H, H, 0, H, H))
    hh.humanize(veldev=20)
    s.merge(hh)
    s.merge(Seq((0, 0, 0, 0, 0, 0, 0,OH,0, 0, 0, 0, 0,OH,0, 0)))
    yield s

def drum_house():
    s =  Seq( (K, 0, 0, 0) * 2 )
    s &= Seq( (H,) * 8)
    s &= Seq( (0, 0, OH, 0, 0, OH, 0, 0) )
    s &= Seq( (0, 0, T) )
    s &= Seq( (0, 0, 0, 0, Sn) )
    return s * 2

def drum_house2():
    s =  Seq((K, 0, OH, 0)*3 + (K, 0, OH, OH))
    s &= Seq((H, 0, 0, H, H, 0, 0, H, H, H, 0, H, H, H, 0, H))


# From Pocket Operations PDF

def drum_good2go():
    s = pattern("x--x --x- --x- ----", K)
    s &= pattern("---- x--- ---- x---", Sn)
    return s

def drum_standard_break_1():
    s = pattern("x--- ---- --x- ----", K)
    s &= pattern("---- x--- ---- x---", Sn)
    s &= pattern("x-x- x-x- xxx- x-x-", H)
    return s

def drum_standard_break_2():
    s = pattern("x--- ---- --x- ----", K)
    s &= pattern("---- x--- ---- x---", Sn)
    s &= pattern("x-x- x-xx x-x- --x-", H)
    return s



def gen_mf_mel1():
    """ 22/11/2022
    """

    s = Seq()
    s.length = 1
    scale = Scale("major", "sol")
    degree = 0
    while True:
        if random.random() > 0.8:
            degree = random.randint(-5, 5)
        degree += random.gauss(0, 4)
        degree = min(5, max(-5, degree))
        chord = scale.triad(degree, dur=1/8)
        s.add(chord)
        if random.random() > 0.8:
            s.add(chord, head=0.87)
        s.humanize()
        yield s
        s.clear()


def drm_djdave1():
    kick = Seq(K,0,0,0, 0,0,K,0, 0,0,K,0, 0,K,0,0)
    clap = Seq(0,0,0,0, Cl,0,0,0) * 2
    hh   = Seq(H,0,H,0, H,0,H,0, H,H,H,0, H,0,H,0)
    ohh  = Seq(0,0,OH,0) * 4
    return kick & clap & hh & ohh

def drm_djdave_easy():
    kick = pattern("x--x--x---x--x--", K)
    clap = pattern("----x---"*2, Cl)
    return kick & clap