#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from midiseq import *

openOutput("irig")

s = Chord("Dm").arp(oct=3)
play((s + Sil(8)) * 2.0, blocking=True)

offset = 0
for n in s:
    offset += 1/2**5
    play(Seq(dur=2+offset).add(n).attenuate(0.6) * 2.0, loop=True)

wait()