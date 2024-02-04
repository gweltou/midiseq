from math import sin, pi
from midiseq import *

openOutput("irig")

mod = Mod(lambda t: 0.5*sin(t*pi*2) + 0.5)

s = Seq("do%64")

s.addMod(mod, MODULATION_WHEEL)
print(s.modseq)

play(s, instrument=gm_accordion, blocking=True)