from typing import Union, Generator
import random

import midiseq.env as env
from .elements import Note, Sil, Seq, Scl, Chord, parse_seq


####  ALIASES
# n = Note
# s = Sil
# c = Chord
# sq = Seq



###############################################################################
####                      Complex sequence generators                      ####
###############################################################################


def genStr2seq(string: str):
    while True:
        yield parse_seq(string)[0]


def genFunc(func: callable, repeat=1, max_iter=0, *args, **kwargs):
    """ Make a generator from a function.
        Arguments to the function can be passed as well.

        Ex: genFun(rndWalk, steps=[-1,0,1])
        
        Arguments
        ---------
            repeat : (int)
                Number of time the same sequence is repeated
            
            max_iter: (int)
                Maximum number of sequence generated
                Set to 0 to loop forever
    """
    n = 0
    if repeat > 0:
        while max_iter == 0 or n < max_iter:
            s = func(*args, **kwargs)
            for _ in range(repeat):
                yield s.copy()
                n += 1
    else:
        while max_iter == 0 or n < max_iter:
            yield func(*args, **kwargs)
            n += 1
            


def genPattern(func: callable, pattern="ABAB", repeat: int=1, *args, **kwargs):
    """ Yield sequences from a function, following a given pattern.
        Arguments to the function can be passed as well.

        Parameters
        ----------
            func : callable
                A function returning a sequence
            pattern : str
                A pattern string, ex: "ABAB" or "1112"
            repeat : int
                Number of repeats for the whole pattern
    """
    pattern = pattern.replace(" ", "")
    seqs = dict()
    for symb in set(pattern):
        seqs[symb] = func(**kwargs)

    for _ in range(repeat):
        for symb in pattern:
            yield seqs[symb]


def genMapRhythm(mel: Seq, rhy: Seq):
    """ Map a rhythm on a melody
        Yield sequences of same duration as the rhythmic sequences
        Yiels sequences utils the lcm is reached between both sequences
    """
    mel_idx = 0
    while True:
        s = Seq(dur=rhy.dur)
        for t, nr in rhy.notes:
            nm = mel[mel_idx]
            dur = nr.dur / env.note_dur
            s.add(Note(nm.pitch, dur=dur, vel=nr.vel), t)
            mel_idx = (mel_idx + 1) % len(mel)
        yield s
        if mel_idx == 0:
            break


def genRotate(seq: Seq, dir=-1, repeat: int=1):
    """ Yield the given sequence, rotating it by `dir` steps every `repeat` time
    """
    s = seq.copy()
    while True:
        for _ in range(repeat):
            yield s
        s.shift(dir, wrap=True)


def genSil(durs=[1, 2]):
    d = random.choice(durs)
    yield Seq(dur=d)



#### other ####


def gen_mf_mel1():
    """ 22/11/2022
    """
    s = Seq()
    s.dur = 1
    scale = Scl("major", "sol")
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
