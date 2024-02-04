from math import sin, pi
from midiseq import *

mod = Mod(lambda t: 0.5*sin(t*pi*4) + 0.5, cycle=0.02)
mod2 = Mod(lambda t: 0.5*sin(t*pi*6) + 0.5, cycle=0.02)

n = Note("c", dur=32).aftertouch(mod)
n2 = Note("e", dur=32).aftertouch(mod2)
s = n * 4
s2 = n2 * 4

print(s.dur)

# modseq = ModSeq(s.dur).add(mod, PITCH_BEND, stretch=True)
# s.setMod(modseq)

play(s&(s2>>0.5), blocking=True)