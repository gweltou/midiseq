import random
from sequence import Seq
from scales import Scale, modes



def gen_1():
    for _ in range(4):
        s = Seq()
        s.length = 1
        s.scale = Scale("dorian", "g")
        s.fillGaussianWalk()
        s.transpose(-12)
        s.stretch(2.0)
        yield s

 
def gen_sweeps(scale="minor", tonic="a"):
    s = Seq()
    s.scale = Scale(scale, tonic)
    while True:
        s = s.copy()
        s.clear()
        f, t = 0, 0
        while abs(t-f) < 10:
            f = random.randint(48, 88)
            t = random.randint(48, 88)
        if abs(t-f) > 30:
            s.fillSweep(f, t, 8)
        else:
            s.fillSweep(f, t, 4)
        yield s


def gen_sweeps_pattern(pattern, scale="minor", tonic="a"):
    """
        pattern: (str)
            Ex: "ABAB" or "1112"
    """
    while True:
        gen = gen_sweeps(scale, tonic)
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
            s.addChordNotes(scl.triad([0, 1, 2, 3][d%3]))
            d+= 1
        s.addSil()
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
            s.addChordNotes(s.scale.triad(i))
        s.addSil()
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
            s.addChordNotes(s.scale.triad(deg), 0.66, random.randint(80, 127))
        s.addChordNotes(s.scale.triad(0), 0.66, random.randint(80, 120))
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
        s.addNote(pitch, dur=note_dur)
        s.head=0.0
        s.addNote(pitch2, dur=note_dur)
        s.length = note_dur + abs(random.gauss(0, 3))
        yield s

def gen_tintinnabuli2():
    note_dur = 0.6
    s = Seq()
    s.scale = Scale("pentatonic_minor", "e")

    while True:
        s.clear()
        pitch_low = s.tonic - 12
        pitch_low = s.scale.getDegree2(pitch_low, random.choice([0, 0, -len(s.scale), 1, 1, 2, 2]))
        pitch_high = s.scale.getDegree(random.randrange(len(s.scale)))
        s.addChordNotes((pitch_low, pitch_high))
        s.length = note_dur + abs(random.gauss(0, 3))
        yield s

def gen_tintinnabuli3():
    note_dur = 0.4
    s = Seq()
    s.scale = Scale("minor", "e")

    while True:
        s.clear()
        pitch_low = s.tonic - 12
        pitch_low = s.scale.getDegree2(pitch_low, random.choice([0, 0, -len(s.scale), 2, 2, 4, 4]))
        pitch_high = s.scale.getDegree(random.randrange(len(s.scale)))
        s.addChordNotes((pitch_low, pitch_high))
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
        s.addChordNotes(pitches, 0.5)
        for i in range(1, d):
            pitches = ( main.getDegree(i), main.getDegree(i+2)+24, minor.getClosest(main.getDegree(i)+9) )
            s.addChordNotes(pitches)
        for i in range(-d+1, 0):
            pitches = ( main.getDegree(i), main.getDegree(i+2)+24, minor.getClosest(main.getDegree(i)+9) )
            s.addChordNotes(pitches)
        pitches = ( main.getDegree(0), main.getDegree(2)+24, minor.getClosest(main.getDegree(0)+9) )
        s.addChordNotes(pitches, 0.5)
        d += 1
        s.stretch(4.0)
        s.humanize()
        yield s