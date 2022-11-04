import random
import rtmidi
import time

from miditool import listOutputs, openOutput, getOutputs, _play
from sequence import Seq, Grid, getNotesFromString
from track import Track
from generators import *



def ex_04(midiout):
    print(("EX 04: Generator with args"))

    t = Track()
    t.gen_func = gen_sweeps_pattern
    t.gen_args = ("AbbCbbAddCdd", "pentatonic_minor", "e4")
    _play(t)


def ex_03(midiout):
    print("EX 03")

    s = Seq()
    s.scale = Scale("aeolian", "e")
    s.length = 1
    s.fillGaussianWalk()
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk()

    s3 = s.copy()
    s3.clear()
    s3.fillGaussianWalk()

    t = Track()
    t.add(s)
    t.add(s2)
    t.add(s)
    t.add(s3)
    
    _play(t)


def ex_02(midiout):
    print("EX 02")

    s = Seq()
    s.scale = Scale("aeolian")
    s.length = 1
    s.fillGaussianWalk()
    cp = s.copy()
    cp.transpose(-12)
    cp.expand(0.8)
    s.add(cp, 0.0)
    
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk()
    cp = s2.copy()
    cp.transpose(-12)
    cp.expand(0.8)
    s2.add(cp, 0.0)

    p1 = (s + s2) * 2
    p2 = p1.copy()
    p2.expand(1.4)
    p2.setScale("locrian")
    p2.tonic = 62

    _play(p1)
    _play(p2)
    _play(p1)
    _play(p2)


def ex_01(midiout):
    s = Seq()
    s.scale = Scale("aeolian")
    s.length = 1
    s.fillGaussianWalk()
    s.head = 0.0
    s.fillGaussianWalk()
    
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk()
    s2.head = 0.0
    s2.fillGaussianWalk()

    p1 = (s + s2) * 2
    p1 *= 0.9
    p2 = p1.copy()
    p2.expand(1.2)
    #p2.setScale("aeolian")
    p2.tonic = 2

    _play(p1)
    _play(p2)
    _play(p1)
    _play(p2)



def buildSeq():
    s1 = Seq()
    s1.length = 1
    s1.fillRandom()

    s2 = Seq()
    s2.length = 1
    s2.fillRandom()

    s = s1 * 2 + s2 * 2
    return s


# def play(track_or_seq, channel=1):
#     track = track_or_seq
#     if type(track_or_seq) == Seq:
#         track = Track(channel)
#         track.add(track_or_seq)

#     midi_seq = []
#     t0 = time.time()
#     t_prev = 0.0
#     seq_i = 0
#     track.init()
#     while True:
#         t = time.time() - t0
#         timedelta = t - t_prev
#         t_prev = t
#         assert 0 < timedelta < 99

#         if midi_seq and seq_i < len(midi_seq):
#             while t >= midi_seq[seq_i][0]:
#                 midiout.sendMessage(midi_seq[seq_i][1])
#                 print("sending", midi_seq[seq_i][1])
#                 seq_i += 1
#                 if seq_i == len(midi_seq):
#                     break
        
#         new_messages = track.update(timedelta)
#         if new_messages:
#             midi_seq = new_messages
#             t0 = time.time()
#             t = 0.0
#             t_prev = 0.0
#             seq_i = 0

#         if track.ended:
#             print("end")
#             break

#         time.sleep(0.01)





def test_adding():
    s = Seq()
    s.length = 1
    s.fillRandom(dur=0.25)

    assert len(s+s) == 2 * len(s)
    assert (s+s).length == 2 * s.length
    assert len(s*2) == 2 * len(s)
    assert (s*2).length == 2 * s.length

    print("test_adding", "pass")


def test_truncate():
    s = Seq()
    s.length = 1
    s.fillRandom()

    s.length = 0.8
    mm = s.getMidiMessages() 
    assert len(mm) == 2*4
    assert mm[-1][0] == 0.8

    print("test_truncate", "pass")


def test_gaussian_walk():
    s = Seq()
    s.length = 1
    s.fillGaussianWalk()
    assert len(s) == 4
    s.clear()
    s.fillGaussianWalk()
    assert len(s) == 4
    s.head = 0.0
    s.tonic += 12
    s.fillGaussianWalk()
    assert len(s) == 8

    print("test_gaussian_walk", "pass")


def test_track():
    s = Seq()
    s.scale = Scale("aeolian", "e")
    s.length = 1
    s.fillGaussianWalk()

    t = Track()
    t.add(s)
    mess = t.update(0.1)
    assert len(mess) == 8
    mess = t.update(1.0)
    assert t.ended == True
    t.init()
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
            s = Seq()
            s.length = 1
            s.scale = Scale("dorian", "a")
            s.fillGaussianWalk(dev=4)
            # s.transpose(-12)
            yield s
    
    t1.gen_func = gen
    t1.init()
    assert len(t1.seqs) == 0
    t1.update(0.01)
    assert t1._next_timer == 1.0
    assert t1.ended == False

    print("test_generator", "pass")


def test_getNotesFromString():
    n = getNotesFromString("60 62 64", dur=0.5)
    assert len(n) == 3
    assert n[0].pitch == 60
    assert n[0].dur == 0.5
    n = getNotesFromString("do re mi fa sol")
    assert len(n) == 5

    s = Seq()
    s.addNotes("do si la sol")
    assert len(s) == 4

    print("test_getNotesFromString", "pass")


def test_addchord():
    s = Seq()
    s.addChordNotes((48, 50, 64,))
    assert len(s) == 3
    s.clear()
    s.addChordNotes("do re mi fa# sol3")
    assert len(s) == 5
    assert s.length == 1

    print("test_addchord", "pass")


def test_grid():
    g = Grid(8)
    assert len(g) == 8
    g.repeat("do", 2, 1)
    s = g.toSeq()
    assert len(s) == 4
    g.clear()
    g.euclid("38", 5)
    assert len(g.toSeq()) == 5

    print("test_grid", "pass")


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



if __name__ == "__main__":
    
    test_adding()
    test_truncate()
    test_gaussian_walk()
    test_track()
    test_map()
    test_generator()
    test_getNotesFromString()
    test_addchord()
    test_grid()
    test_scale()

    print("Generators")
    next(gen_1())
    next(gen_chords1())
    next(gen_chords2())
    next(gen_chords3())
    next(gen_sweeps())
    next(gen_sweeps_pattern("ABAB"))
    next(gen_tintinnabuli())
    next(gen_tintinnabuli2())
    next(gen_tintinnabuli3())
    next(gen_fratres())
    print("All good")


    # listOutputs()
    # openOutput(len(getOutputs()) - 1)    

    # ex_04(midiout)
