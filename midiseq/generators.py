import random
from sequence import Note, Sil, Seq, Scale, modes, Chord



####  ALIASES
# n = Note
# s = Sil
# c = Chord
# sq = Seq



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
    while True:
        s = Seq()
        if d%4 == 0:
            scl = random.choice(list(modes.keys()))
            s.scale = Scale(scl)
            print(scl)
        s.clear()
        chord_prog = [ random.choice(list(range(7))) for _ in range(4) ]
        print(chord_prog)
        for i in chord_prog:
            s.add(s.scale.triad(i))
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


# def gen_drums1():
#     g = Grid()
#     g.length = 1.5
#     g.euclid(35, 2)     # Kick
#     g.euclid(38, 2, 4)  # Snare
#     # g.euclid(42, 11, 1) # Hihats
#     g2 = Grid(8)
#     g2.length = 0.5
#     g2.euclid(35, 1)
#     g2.euclid(39, 1, 4)
#     g2.euclid(42, 6, 1)
#     while True:
#         yield g.toSeq() + g2.toSeq()



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
    sc = Scale("japanese")
    while True:
        s=Seq() 
        s.scale=sc
        if random.random() < 0.1:
            sc.tonic = random.randrange(42, 54)
        s.randGauss(dev=2)
        s.stretch(16, False)
        yield s


# def loop1():
#     g = Grid()
#     g.length = 2
#     g.euclid(sit3, 12, 1)
#     g.euclid(sit2, 4, 4)
#     g.euclid(sit1, 2, 0)
#     return g


# def loop_euclidian_sitala():
#     short = [sit3, sit4, sit14, sit16]
#     g = Grid()
#     g.length = 4

#     g.euclid(sit1, random.randint(2, 5), random.randint(0, 3))
#     g.euclid(sit2, random.randint(2, 5), random.randint(1, 5))

#     if random.random() > 0.5:
#         g.euclid(sit12, random.randint(1, 3), random.randint(0, 8))

#     random.shuffle(short)
#     for i in range(random.randint(0, len(short))):
#         n = random.randint(5, 12)
#         g.euclid(short[i], n, random.randint(0, n))

#     return g




###############################################################################
####                            DRUM PATTERNS                              ####
###############################################################################


# Sitala drum sampler mapping to midi pitch
# Clean 808
sit1 = 36 # Kick
sit2 = 37 # Snare
sit3 = 38 # Closed HH
sit4 = 39 # Open HH
sit5 = 40 # Cymbal
sit6 = 41 # Low Tom
sit7 = 42 # Mid Tom
sit8 = 43 # High Tom
sit9 = 44 # Low Conga
sit10 = 45 # Mid Conga
sit11 = 46 # High Conga
sit12 = 47 # Hand Clap
sit13 = 48 # Clave
sit14 = 49 # Maraca
sit15 = 50 # Cowbell
sit16 = 51 # Rim shot

K = sit1    # Kick
Sn = sit2   # Snare
H = sit3    # Closed Hats
OH = sit4   # Open Hats
T = sit8    # Tom
Cl = sit12  # Clap
Cb = sit15  # Cowbell


def gen_drum_8thNoteGrove():
    s = Seq((H, 0) * 4)  # High-hats
    s.merge(Seq((K, 0, 0, 0, Sn, 0, 0, 0)))   # Kick and Snare
    s *= 2
    yield s

def gen_drum_4toTheFloor():
    s = Seq((H, 0) * 4)  # High-hats
    s.merge(Seq( (K, 0, 0, 0) * 2) )   # Kick and Snare
    s.merge(Seq( (0, 0, 0, 0, K, 0, 0, 0) ))
    s *= 2
    yield s

def gen_drum_shuffleGroove():
    s = Seq( (H, 0, H) * 2)   # HH
    s.merge(Seq( (K, 0, 0, Sn, 0, 0) ))    # K & S
    s *= 2
    yield s

def gen_drum_discoGroove():
    s = Seq( ( H, 0, OH, 0) * 2 )
    s.merge( Note(K) + 3 * Sil() + Chord((K, Sn)) + 3 * Sil() )
    s *= 2
    yield s

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
    s =  Seq((K, 0, K, 0, Sn,0, K, Sn,0, Sn,K, Sn,Sn,K, 0, S))
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
