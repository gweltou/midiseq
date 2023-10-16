#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from midiseq import *

setScl("minor", "g")
s = Seq("v ii v i iv") % 0.01
play((s*8).transpose(-12).humanize(0.1, 10) * 64.0)
wait()