from typing import Union
import random

import midiseq.env as env
from .elements import Note, Sil, Seq, Scale, Chord
from .utils import str2elt, str2pitch, pattern, randGauss
from .definitions import *



####  ALIASES
# n = Note
# s = Sil
# c = Chord
# sq = Seq


###############################################################################
####                           Exemple sequences                           ####
###############################################################################

seq_kaini_industries = Seq("""
    -g#%1.5 -a#%.5 b_b -g#_b -g#_a# f#_-g# -2b -g#_-f#
    c# -c#%4 f#%2 g#
    -2g#%1.5 -a#_d# -a#_d# -a#_-f# f#_f# -a#_f# g#%.5 g#
    -c# -d#_e# -d# e# b e#_b e#_a# f#
    """)
seq_never_gonna_gyu = "a#_+c +c#_a# +f +f +d# . g#_a# +c#_a# +d# +d# +c# +c_a#"
seq_mario = "e_e ._e ._c e_. g . -g"

seq_sunburn = Seq("""
    -b b g e b g e g
    -a b e c b e c e
    c +c g e +c g e g
    -a b e c b e c e
    """)^12
seq_sunburn2 = Seq("""
    e +e b g +e b g b  
    -a +e +c +a +f# +e +c +e 
    c +f# +e +c +a +g +f# +e 
    -a +e +c a +f# +e +c +e 
    """)^12




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
        #s.scale = Scale(scl)
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
    kick = pattern("x--- --x- --x- -x--", K)
    clap = pattern("---- x---", Cl) * 2
    hh = pattern("x-x- x-x- xxx- x-x-", H)
    ohh = pattern("--x-", OH) * 4
    return kick & clap & hh & ohh

def drm_djdave_easy():
    kick = pattern("x--x --x- --x- -x--", K)
    clap = pattern("---- x---", Cl) * 2
    return kick & clap