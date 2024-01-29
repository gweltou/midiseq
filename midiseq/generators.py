from typing import Union, Generator
import random

import midiseq.env as env
from .elements import Note, Sil, Seq, Scl, Chord, parse
# from .definitions import *



####  ALIASES
# n = Note
# s = Sil
# c = Chord
# sq = Seq




###############################################################################
####                      Complex sequence generators                      ####
###############################################################################


def genStr2seq(string: str) -> Seq:
    while True:
        yield parse(string)


def genFunc(func: callable, repeat=0, *args, **kwargs):
    if repeat > 0:
        for _ in range(repeat):
            yield func(*args, **kwargs)
    else:
        while True:
            yield func(*args, **kwargs)


def genPattern(func: callable, pattern="ABAB", repeat: int=1, *args, **kwargs):
    """ Yield sequences from a function, following a given pattern

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
