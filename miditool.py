### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

import rtmidi
# import random
import time
import threading
from sequence import Note, Seq
from track import Track
from scales import *
from generators import *


DEBUG = True



# class PlayOnce(threading.Thread):
#     def __init__(self, rec, outport):
#         super(PlayOnce, self).__init__()
#         self.rec = rec
#         self.outport = outport
#         if DEBUG: print("New PlayOnce Thread")
    
#     def run(self):
#         print("notes in thread", self.rec)
#         for msg in self.rec:
#             time.sleep(msg.time)
#             self.outport.send(msg)
#         print("note played", msg)



_timeres = 0.01

def _play(track_or_seq, channel=1):
    track = track_or_seq
    if type(track_or_seq) == Seq:
        track = Track(channel)
        track.add(track_or_seq)

    print("++++ PLAYBACK Started")
    midi_seq = []
    t0 = time.time()
    t_prev = 0.0
    seq_i = 0
    track.init()
    while True:
        if _must_stop:
            print("++++ PLAYBACK stopping...")
            break

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
            break

        t = time.time() - t0 - t_prev
        load = t / _timeres
        if load > 0.1:
            print("++++ PLAYBACK [warning] load:", load, "%")
        time.sleep(min(0.2, max(0, _timeres)))
    print("++++ PLAYBACK Stopped")



def panic(channel=1):
    for i in range(16):
        mess = rtmidi.MidiMessage.allNotesOff(i)
        midiout.sendMessage(mess)


def listOutputs(midiout):
    for i in range(midiout.getPortCount()):
        print( "[{}] {}".format(i, midiout.getPortName(i)) )

def getOutputs(midiout):
    outputs = []
    for i in range(midiout.getPortCount()):
        outputs.append( (i, midiout.getPortName(i)) )
    return outputs


_playing_thread = None
_must_stop = False

def play():
    tracks = []
    for i in range(16):
        track_name = "t{}".format(i+1)
        if track_name in globals():
            tracks.append(globals()[track_name])
        
    global _playing_thread
    global _must_stop
    if _playing_thread != None:
        _must_stop = True
        _playing_thread.join()
    
    _must_stop = False
    _playing_thread = threading.Thread(target=_play, args=(tracks[0],))
    _playing_thread.start()


def stop():
    global _must_stop
    _must_stop = True
    panic()


def openPort(midiout, port_n):
    # midiout = rtmidi.RtMidiOut()
    print("Opening port {} [{}]".format(port_n, midiout.getPortName(port_n)) )    
    midiout.openPort(port_n)


if __name__ == "__main__":
    midiout = rtmidi.RtMidiOut()

    listOutputs(midiout)
    openPort(midiout, len(getOutputs(midiout)) - 1)
        
    t1 = Track()
    t2 = Track()
    t2.channel = 2
    t3 = Track()
    t3.channel = 3
    t4 = Track()
    t4.channel = 4
