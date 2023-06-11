import time
import threading
### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

#from mido import MidiFile
import mido
import rtmidi

from .sequence import Seq, Chord, Note, Sil, Track, str2elt, str2seq
from .generators import *
from .engine import listOutputs, openOutput, _getOutputs, play, stop
import midiseq.env as env



def setNoteLen(d):
    """ Set default note length """
    env.NOTE_LENGTH = d

def setScale(scale="chromatic", tonic="c"):
    env.SCALE = Scale(scale, tonic)

def setTempo(bpm):
    env.TEMPO = bpm

def clearAllTracks():
    for track in env.TRACKS:
        track.clear()


env.METRONOME_NOTES = (sit13, sit16)
setScale("chromatic")

midi_out = dict()
midi_out["default"] = openOutput(0)
for i, port_name in _getOutputs():
    if "microfreak" in port_name.lower():
        midi_out["microfreak"] = openOutput(i)
        midi_out["mf"] = midi_out["microfreak"]
    if "fluid" in port_name.lower():
        midi_out["fluid"] = openOutput(i)
        midi_out["fl"] = midi_out["fluid"]
    if "amsynth" in port_name.lower():
        midi_out["amsynth"] = openOutput(i)
        midi_out["am"] = midi_out["amsynth"]


env.DEFAULT_OUTPUT = midi_out["default"]
_metronome_port = midi_out["default"]
if "microfreak" in midi_out:
    env.DEFAULT_OUTPUT = midi_out["microfreak"]
elif "fluid" in midi_out:
    env.DEFAULT_OUTPUT = midi_out["fluid"]

t1 = Track(0)
t2 = Track(1)
t3 = Track(2)
t4 = Track(3)

env.TRACKS = [t1, t2, t3, t4]
