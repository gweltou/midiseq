#!/usr/bin/env python3

import random
import rtmidi
import time

from sequence import *
import generators


"""
def ex_04(midiout):
    print(("EX 04: Generator with args"))

    t = Track()
    t.gen_func = gen_sweeps_pattern
    t.gen_args = ("AbbCbbAddCdd", "pentatonic_minor", "e4")
    _play(t)
"""



def test_basic_opps():
    s = rand(4)
    assert len(s) == 4

    assert len(s+s) == 2 * len(s)
    assert (s+s).length == 2 * s.length
    assert len(s*2) == 2 * len(s)
    assert (s*2).length == 2 * s.length

    s = Seq()
    s.addNotes("do si la sol fa mi2 re# c")
    assert len(s) == 8

    s = Note(35) + Note(36) + Sil()
    assert len(s) == 2
    assert s.length == 0.75

    s = 2*Note(30) + Sil() + Note(33)*3 + 2*Sil() + Note(39)
    assert s.length == 2.25
    assert len(s) == 6

    print("test_basic_opps", "pass")


def test_midimessage_truncate():
    s = Seq()
    s.rand(4)

    s.length = 0.8
    mm = s.getMidiMessages() 
    assert len(mm) == 2*4
    assert mm[-1][0] == 0.8

    print("test_truncate", "pass")


# def test_gaussian_walk():
#     s = Seq()
#     s.length = 1
#     s.fillGaussianWalk()
#     assert len(s) == 4
#     s.clear()
#     s.fillGaussianWalk()
#     assert len(s) == 4
#     s.head = 0.0
#     s.tonic += 12
#     s.fillGaussianWalk()
#     assert len(s) == 8

#     print("test_gaussian_walk", "pass")


def test_track():
    s = Seq()
    s.rand(4)

    t = Track()
    t.add(s)
    mess = t.update(0.1)
    assert len(mess) == 8
    mess = t.update(1.0)
    assert t.ended == True
    t.reset()
    assert t.ended == False

    print("test_track", "pass")


def test_map():
    s = Seq()
    s.length = 1
    s.map([60, 54, 54, 54, 69, 54, 54, 54])
    assert len(s) == 8

    print("test_map", "pass")


def test_generator():
    t1 = Track()
    
    def gen():
        for _ in range(4):
            s = Seq().rand()
            # s.transpose(-12)
            yield s
    
    t1.gen_func = gen
    t1.reset()
    assert len(t1.seqs) == 0
    t1.update(0.01)
    assert t1._next_timer == 0.99
    assert t1.ended == False

    print("test_generator", "pass")


def test_getNotesFromString():
    n = getNotesFromString("60 62 64", dur=2)
    assert len(n) == 3
    assert n[0].pitch == 60
    assert n[0].dur == 0.5
    n = getNotesFromString("do re mi fa sol")
    assert len(n) == 5

    s = Seq()
    s.addNotes("do si la sol")
    assert len(s) == 4

    print("test_getNotesFromString", "pass")



# def test_grid():
#     g = Grid(8)
#     assert len(g) == 8
#     g.repeat("do", 2, 1)
#     s = g.toSeq()
#     assert len(s) == 4
#     g.clear()
#     g.euclid("38", 5)
#     assert len(g.toSeq()) == 5

#     print("test_grid", "pass")


def test_scale():
    s = Scale()
    assert len(s) == 7
    assert s.getDegree(0) == 60
    assert s.getDegree(1) == 62
    assert s.getDegree(7) == 72
    assert s.getDegree(-7) == 48
    assert s.getDegree(12) == 81

    assert s.getClosest(60) == 60
    assert s.getClosest(61) == 60
    assert s.getClosest(62) == 62
    s.tonic += 1
    assert s.getDegree(0) == 61
    assert s.getClosest(60)
    print("test_scale", "pass")


def test_crop():
    s = Seq()
    s.head = -0.35
    s.rand(6)
    s.add(Note(66))
    s.length = 1
    assert len(s) == 7
    assert s.notes[0][0] == -0.35
    s.crop()
    assert len(s) == 5
    print("test_crop", "pass")


def test_merge():
    s = Seq("50 50 0 50")
    s.merge(Seq("0 60 60 0"))
    assert len(s) == 5
    s = Seq("1 2 3 4")
    s &= Seq("5 6 7 8")
    assert len(s) == 8
    print("test_merge", "pass")



def test_select():
    s = Seq("8 9 10 11 12 13")
    selection = s.selectNotes(lambda x: x.pitch <= 10)
    assert len(selection) == 3
    print("test_select", "pass")


def test_index_slice():
    s = Seq("60 61 62 63 64 65")
    assert s[0] == Note(60)
    assert len(s[0:3]) == 3
    assert len(s[:3]) == 3
    s = s[0.0:1.0]
    assert len(s) == 4
    assert s.length == 1.0
    print("test_index_slice", "pass")


def test_filter():
    s = Seq("60 61 62 63 64 65")
    assert(len(s.filter(lambda n: n.pitch<=62)) == 3)
    print("test_filter", "pass")


def test_selectnotes():
    s = Seq("60 61 62 63 64 65")
    assert(len(s.selectNotes(lambda n: n.pitch<=62)) == 3)
    print("test_selectnote", "pass")



if __name__ == "__main__":
    test_basic_opps()
    test_midimessage_truncate()
    # test_gaussian_walk()
    test_track()
    test_map()
    test_generator()
    test_getNotesFromString()
    test_addchord()
    # test_grid()
    test_scale()
    test_crop()
    test_merge()
    test_select()
    test_index_slice()
    test_filter()
    test_selectnotes()

    print("Generators")
    for i in dir(generators):
        if i.startswith("gen_") and not i == "gen_pattern":
            gen = getattr(generators, i)
            print(i)
            next(gen())

    print("All good")