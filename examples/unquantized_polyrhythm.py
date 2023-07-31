#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from midiseq import *

s = Chord("Dm").arp(oct=3)
play((s + Sil(8)) * 2.0, blocking=True)

offset = 0
for n in s:
    offset += 0.02
    play(Seq(dur=2+i*offset).add(n) * 2.0, loop=True)

wait()