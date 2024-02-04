from math import sin, pi
from midiseq import *

# s = rndDur(4, silprob=0.2) * 2.0
s = Seq("c c C c c c C c") * 8.0
print(s.dur)

mod = Mod(lambda t: 0.5*sin(t*pi*2) + 0.5, cycle=0.02)
modseq = ModSeq(s.dur).add(mod, PITCH_BEND, stretch=True)

s.setMod(modseq)

play(s, blocking=True)