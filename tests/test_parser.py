#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from midiseq import Seq, Note
from midiseq.elements import parse
import midiseq.env as env




def test_parser():
	strings = [
		("do   re  mi  ", Seq((0.0, Note(48)), (0.125, Note(50)), (0.25, Note(52)))),
		("do .. re", Seq((0.0, Note(48)), (0.375, Note(50)), dur=0.5)),
		("do_re mi_fa_sol", Seq((0.0, Note(48,0.5)), (0.0625, Note(50,0.5)), (0.125, Note(52,1/3)), (0.125 + 1/24, Note(53,1/3)), (0.125 + 2/24, Note(55,1/3)))),
		("[do mi sol]", Seq((0.0, Note(48)), (0.0, Note(52)), (0.0, Note(55)))),
		("[do_re mi_fa]", Seq((0.0, Note(48,0.5)), (0.0, Note(52,0.5)), (0.0625, Note(50,0.5)), (0.0625, Note(53,0.5)))),
		("[do mi sol][mi sol si]", Seq((0.0, Note(48)), (0.0, Note(52)), (0.0, Note(55)), (0.125, Note(52)), (0.125, Note(55)), (0.125, Note(59)))),
		
		# Modifiers
		("[do sol]%4", Seq((0.0, Note(48,4)), (0.0, Note(55,4)), dur=0.5)),
		("[do sol]%.5", Seq((0.0, Note(48,0.5)), (0.0, Note(55,0.5)), dur=0.5)),
		("[do sol]^2", Seq((0.0, Note(50)), (0.0, Note(57)), dur=0.125)),
		("[do sol]^2%4", Seq((0.0, Note(50,4.0)), (0.0, Note(57,4.0)), dur=0.5)),
	]

	for strseq, seq in strings:
		hyp = parse(strseq)
		# print(seq)
		print(hyp)
		assert hyp == seq