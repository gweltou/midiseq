### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

# import threading
import rtmidi
# import random
import time
from sequence import Note, Seq
from track import Track
from scales import *


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



def panic(channel=1):
        mess = rtmidi.MidiMessage.allNotesOff(channel)
        midiout.sendMessage(mess)


def listOutputs(midiout):
    for i in range(midiout.getPortCount()):
        print( "[{}] {}".format(i, midiout.getPortName(i)) )

def getOutputs(midiout):
    outputs = []
    for i in range(midiout.getPortCount()):
        outputs.append( (i, midiout.getPortName(i)) )
    return outputs


def openPort(midiout, port_n):
    # midiout = rtmidi.RtMidiOut()
    print("Opening port {} [{}]".format(port_n, midiout.getPortName(port_n)) )    
    midiout.openPort(port_n)


if __name__ == "__main__":
    midiout = rtmidi.RtMidiOut()

    listOutputs(midiout)
    openPort(midiout, len(getOutputs(midiout)) - 1)    
        
    #test_note(midiout)