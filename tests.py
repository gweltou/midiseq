

import random
import rtmidi
import time

from miditool import listOutputs, openPort, getOutputs
from scales import *
from utils import *
from sequence import Seq, Note
from track import Track


def ex_03(midiout):
    print("EX 03")

    s = Seq()
    s.setScale("aeolian", "e")
    s.length = 1
    s.fillGaussianWalk()
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk()

    t = Track()
    t.add(s)
    t.add(s2)
    
    play(t)


def ex_02(midiout):
    s = Seq()
    s.setScale("aeolian")
    s.length = 1
    s.fillGaussianWalk(60)
    cp = s.copy()
    cp.transpose = -12
    cp.expand(0.8)
    s.add(cp, 0.0)
    
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk(60, 0.25, 4)
    cp = s2.copy()
    cp.transpose = -12
    cp.expand(0.8)
    s2.add(cp, 0.0)

    p1 = (s + s2) * 2
    p2 = p1.copy()
    p2.expand(1.4)
    p2.setScale("locrian")
    p2.rootnote = 2

    play(p1)
    play(p2)
    play(p1)
    play(p2)


def ex_01(midiout):
    s = Seq()
    s.setScale("aeolian")
    s.length = 1
    s.fillGaussianWalk(60)
    s.head = 0.0
    s.fillGaussianWalk(72)
    
    s2 = s.copy()
    s2.clear()
    s2.fillGaussianWalk(60)
    s2.head = 0.0
    s2.fillGaussianWalk(72)

    p1 = (s + s2) * 2
    p1 *= 0.9
    p2 = p1.copy()
    p2.expand(1.2)
    #p2.setScale("aeolian")
    p2.rootnote = 2

    playSeq(p1)
    playSeq(p2)
    playSeq(p1)
    playSeq(p2)



def buildSeq():
    s1 = Seq()
    s1.length = 1
    s1.fillRandom()

    s2 = Seq()
    s2.length = 1
    s2.fillRandom()

    s = s1 * 2 + s2 * 2
    return s


# def playSeq(pattern, channel=1):
#     midi_seq = pattern.getMidiMessages(channel)
#     seq_i = 0
#     t0 = time.time()
#     while True:
#         if seq_i >= len(midi_seq):
#             print("end")
#             break
#         t = time.time() - t0
#         while midi_seq[seq_i][0] < t:
#             midiout.sendMessage(midi_seq[seq_i][1])
#             print("[{}] sending".format(round(t,2)), midi_seq[seq_i][1])
#             seq_i += 1
#             if seq_i == len(midi_seq):
#                 break
#         time.sleep(0.01)
def play(track, channel=1):
    if type(track) == Seq:
        track = Track(channel)
        track.add(track)

    midi_seq = []
    t0 = time.time()
    t_prev = 0.0
    seq_i = 0
    track.init()
    while True:
        t = time.time() - t0
        timedelta = t - t_prev
        t_prev = t
        assert 0 < timedelta < 99

        if midi_seq and seq_i < len(midi_seq):
            while t >= midi_seq[seq_i][0]:
                midiout.sendMessage(midi_seq[seq_i][1])
                print("sending", midi_seq[seq_i][1])
                seq_i += 1
                if seq_i == len(midi_seq):
                    break
        
        new_messages = track.update(timedelta)
        if new_messages:
            midi_seq = new_messages
            t0 = time.time()
            t = 0.0
            t_prev = 0.0
            seq_i = 0

        if track.ended:
            print("end")
            break

        time.sleep(0.01)



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
    s.rootnote += 12
    s.fillGaussianWalk()
    assert len(s) == 8

    print("test_gaussian_walk", "pass")


def test_track():
    s = Seq()
    s.setScale("aeolian", "e")
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


if __name__ == "__main__":
    
    test_adding()
    test_truncate()
    test_gaussian_walk()
    test_track()

    midiout = rtmidi.RtMidiOut()

    listOutputs(midiout)
    openPort(midiout, len(getOutputs(midiout)) - 1)    

    ex_03(midiout)
