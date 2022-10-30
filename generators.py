import random
from sequence import Seq



def gen_1():
    for _ in range(4):
        s = Seq()
        s.length = 1
        s.setScale("dorian", "g")
        s.fillGaussianWalk()
        s.transpose(-12)
        s.stretch(2.0)
        yield s

 
def gen_sweeps(scale="minor", tonic="a"):
    s = Seq()
    s.setScale(scale, tonic)
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



def gen_arvo_part():
    # Tintinnabuli
    note_dur = 1.0
    s = Seq()
    s.setScale("minor", 54)
    for _ in range(16):
        s.clear()
        pitch = s.getScaleDegree(random.gauss(0, 2.5)) + 12
        pitch2 = 54 + random.choice([0, 3, 7, -12])
        s.addNote(pitch, dur=note_dur)
        s.head=0.0
        s.addNote(pitch2, dur=note_dur)
        s.length = note_dur + abs(random.gauss(0, 3))
        yield s
