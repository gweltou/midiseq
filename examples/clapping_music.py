#! /usr/bin/env python3

# Example from Steve Reich's clapping music
# https://www.youtube.com/watch?v=lzkOFJMI5i8


from midiseq import *


# Copied from generators.py
def genRotate(seq: Seq, dir=-1, repeat: int=1):
    """ Yield the given sequence, rotating it by `dir` steps every `repeat` time
    """
    s = seq.cpy()
    while True:
        for _ in range(repeat):
            yield s
        s.shift(dir, wrap=True)

setBpm(100)

s = pattern("xxx-xx-x-xx-", "do")
play(s, loop=True)
play(genRotate(s^7, dir=-1, repeat=4), loop=True)
wait()