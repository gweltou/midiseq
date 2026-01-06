#from mido import MidiFile
# import mido
# import rtmidi

from typing import Optional, Callable
from queue import LifoQueue

from rtmidi.midiconstants import (
    PITCH_BEND, MODULATION_WHEEL, PORTAMENTO,
)

VOLUME = 7
POLY_AFTERTOUCH = 160
CHANNEL_AFTERTOUCH = 208

from .definitions import *
# from .engine import (
    # listOutputs, openOutput, _getOutputs,
    # listInputs, openInput,
    # listen, rec,
    # play, stop, panic, playMetro, wait,
    # TrackGroup, getPastOpened
# )

from .engine import (
    listOutputs, getOutput, getOutputs,
    listInputs, getInput, getInputs,
    play, stop
)
from .tracks import Track, TrackGroup, tracks

from .elements import (
    Seq, Chord, Note, Sil, PNote, Element,
    parse, parse_element
)
from .modulation import *
from .utils import (
    rnd, rndWalk, rndGauss, rndPick, rndDur,
    euclid, lcm,
    noteRange,
    noob2seq,
    pattern,
    morse,
)
# from .whistle import whistle, whistleDur, tap, tapDur
from .generators import *
from .seqs import *
import midiseq.env as env

###### Generative Neural Network #######
# from .nn import nnFeed, nnGet, nnReset


def setNoteDur(d):
    """ Set default note length, relative to a full note """
    env.note_dur = d

def setScale(scale="chromatic", tonic="c"):
    env.scale = Scl(scale, tonic)

def setBpm(bpm):
    env.bpm = bpm

def clearAll():
    for track in tracks:
        track.clear()

def mute(*tracks) -> None:
    for t in tracks:
        t.muted = True

def unmute(*tracks) -> None:
    for t in tracks:
        t.muted = False

def mutesw(*tracks) -> None:
    for t in tracks:
        t.muted = not t.muted


env.METRONOME_NOTES = (36, 38)

setScale("major", "c")


midi_out = dict()
midi_out["default"] = getOutput(0)
for port_idx, port_name in getOutputs():
    if "microfreak" in port_name.lower():
        midi_out["microfreak"] = getOutput(port_idx)
    if "fluid" in port_name.lower():
        midi_out["fluidsynth"] = getOutput(port_idx)
    if "amsynth" in port_name.lower():
        midi_out["amsynth"] = getOutput(port_idx)
    if "preenfm" in port_name.lower():
        midi_out["preenfm"] = getOutput(port_idx)
    if "irig" in port_name.lower():
        midi_out["irig"] = getOutput(port_idx)

env.default_output = midi_out["default"]
_metronome_port = midi_out["default"]

# Prefered output ports
if "microfreak" in midi_out:
    env.default_output = midi_out["microfreak"]
elif "fluidsynth" in midi_out:
    env.default_output = midi_out["fluidsynth"]
elif "irig" in midi_out:
    env.default_output = midi_out["irig"]


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
t11 = Track(9, name="t11", sync_from=t10)
t12 = Track(9, name="t12", sync_from=t10)
t13 = Track(9, name="t13", sync_from=t10)
t14 = Track(9, name="t14", sync_from=t10)
t15 = Track(9, name="t15", sync_from=t10)
t16 = Track(9, name="t16", sync_from=t10)

tracks.add_track(t1)
env.default_track = t1


def _playT(track: Track, *args, **kwargs):
    """ Start a single track """
    if args:
        track.clearAdd(*args)
    
    if not tracks.all_stopped():
        print("not all stopped")
        return
    
    track.stopped = False
    
    # Synchronize all other tracks to this track
    # if it is the first one to start
    for t in tracks:
        if t == track:
            t.reset()
            t.syncFrom(None)
        else:
            t.stopped = True
            t.syncFrom(track)
    
    play(track, **kwargs)


history = LifoQueue(512)


def play(*args, **kwargs):
    print(f"main play({args=}, {kwargs=}")
    state = (args, kwargs)
    history.put(state)
    engine.play(*args, **kwargs)


def play1(*args, **kwargs):
    _playT(t1, *args, **kwargs)
def play2(*args, **kwargs):
    _playT(t2, *args, **kwargs)
def play3(*args, **kwargs):
    _playT(t3, *args, **kwargs)
def play4(*args, **kwargs):
    _playT(t4, *args, **kwargs)
def play5(*args, **kwargs):
    _playT(t5, *args, **kwargs)
def play6(*args, **kwargs):
    _playT(t6, *args, **kwargs)
def play7(*args, **kwargs):
    _playT(t7, *args, **kwargs)
def play8(*args, **kwargs):
    _playT(t8, *args, **kwargs)
def play9(*args, **kwargs):
    _playT(t9, *args, **kwargs)
def play10(*args, **kwargs):
    _playT(t10, *args, **kwargs)
def play11(*args, **kwargs):
    _playT(t11, *args, **kwargs)
def play12(*args, **kwargs):
    _playT(t12, *args, **kwargs)
def play13(*args, **kwargs):
    _playT(t13, *args, **kwargs)
def play14(*args, **kwargs):
    _playT(t14, *args, **kwargs)
def play15(*args, **kwargs):
    _playT(t15, *args, **kwargs)
def play16(*args, **kwargs):
    _playT(t16, *args, **kwargs)


def pushT1(method: Callable, *args, **kwargs):
    t1.push(method, *args, **kwargs)
def pushT2(method: Callable, *args, **kwargs):
    t2.push(method, *args, **kwargs)
def pushT3(method: Callable, *args, **kwargs):
    t3.push(method, *args, **kwargs)
def pushT4(method: Callable, *args, **kwargs):
    t4.push(method, *args, **kwargs)
def pushT5(method: Callable, *args, **kwargs):
    t5.push(method, *args, **kwargs)
def pushT6(method: Callable, *args, **kwargs):
    t6.push(method, *args, **kwargs)
def pushT7(method: Callable, *args, **kwargs):
    t7.push(method, *args, **kwargs)
def pushT8(method: Callable, *args, **kwargs):
    t8.push(method, *args, **kwargs)

def popT1():
    t1.pop()
def popT2():
    t2.pop()
def popT3():
    t3.pop()
def popT4():
    t4.pop()
def popT5():
    t5.pop()
def popT6():
    t6.pop()
def popT7():
    t7.pop()
def popT8():
    t8.pop()


def _stopT(track: Track):
    track.stopped = True

    still_playing = list(filter(lambda t: not t.stopped, tracks))
    if len(still_playing) == 1:
        # Set remaining track as main track
        main_track = still_playing[0]
        for t in tracks:
            if t == main_track:
                t.syncFrom(None)
            else:
                t.syncFrom(main_track)

def stop1():
    _stopT(t1)
def stop2():
    _stopT(t2)
def stop3():
    _stopT(t3)
def stop4():
    _stopT(t4)
def stop5():
    _stopT(t5)
def stop6():
    _stopT(t6)
def stop7():
    _stopT(t7)
def stop8():
    _stopT(t8)


def display(status=True):
    env.DISPLAY = status