from miditool import *


def gen1():
    setScale("mixolidian", "c")
    setNoteLen(1/8)
    A = Seq().randWalk() * 2
    B = Seq().randWalk() * 2
    C = Seq().randWalk() * 2
    D = Seq().randWalk(steps=[-4, -3, 1, 3, 4]) * 2
    return (A+B) * 4 + (C+D) * 4


seq1 = Seq("la do6 mi6 " * 5 + "do6")
seq2 = Seq("la do6 mi6 fa6 la6 fa6 mi6 do6")
seq3 = Seq("la do6 mi6 fa6 la6 si6 do7 mi7")


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


def gen2(n):
    pool = getNotesFromString("la do6 mi6 fa6 la6 si6 do7 mi7")
    while True:
        s = Seq()
        for _ in range(n):
            s.add(random.choice(pool))
        yield s


def glitchify(s, n=3):
    s = s.copy()
    notes = [n.pitch for n in s]
    for _ in range(n):
        i = random.randrange(len(s))
        s[i] = (s[i].pitch, random.choice(notes))
    return s


t1.add(seq1.transpose(-12))
t2.add(seq3)