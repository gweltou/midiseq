import time
import threading
### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

#from mido import MidiFile
import mido
import rtmidi

from .engine import listOutputs, openOutput, _getOutputs, play, stop, TrackGroup, getPastOpened
from .elements import Seq, Chord, Note, Sil, Track
from .utils import pattern, noob2seq, rnd, rndWalk, rndGauss, rndPick, euclid, lcm
from .definitions import *
from .generators import *
import midiseq.env as env



def setNoteDur(d):
    """ Set default note length """
    env.note_dur = d

def setScl(scale="chromatic", tonic="c"):
    env.scale = Scl(scale, tonic)

def setBpm(bpm):
    env.bpm = bpm

def clearAllTracks():
    for track in env.tracks:
        track.clear()


env.METRONOME_NOTES = (sit13, sit16)
setScl("chromatic")

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

t1 = Track(0, name="t1")
t2 = Track(1, name="t2", sync_from=t1)
t3 = Track(2, name="t3", sync_from=t1)
t4 = Track(3, name="t4", sync_from=t1)
t5 = Track(4, name="t5", sync_from=t1)
t6 = Track(5, name="t6", sync_from=t1)
t7 = Track(6, name="t7", sync_from=t1)
t8 = Track(7, name="t8", sync_from=t1)
t9 = Track(8, name="t9", sync_from=t1)
t10 = Track(9, name="t10", sync_from=t1)
t11 = Track(10, name="t11", sync_from=t1)
t12 = Track(11, name="t12", sync_from=t1)
t13 = Track(12, name="t13", sync_from=t1)
t14 = Track(13, name="t14", sync_from=t1)
t15 = Track(14, name="t15", sync_from=t1)
t16 = Track(15, name="t16", sync_from=t1)

env.tracks = TrackGroup()
env.tracks.addTrack(t1)

setScl("major", "c")


# setBpm(110)
# play((
#     lcm("d%3 a%2 .", "+a%2 +f%2")*4 +
#     lcm("c%3 a%2 .", "+a%2|+2e%2 +e%2")*4 +
#     lcm("-a#%3 a%2 .", "+a%2|+2d%2 +d%2")*4 +
#     lcm("g%3 +d%2 .", "+a#%2|+2d%2 +g%2")*4).humanize().attenuate(0.7),
#     loop=True)