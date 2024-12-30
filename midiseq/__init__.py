#from mido import MidiFile
# import mido
# import rtmidi

from typing import Optional
from queue import LifoQueue

from rtmidi.midiconstants import (
    PITCH_BEND, MODULATION_WHEEL, PORTAMENTO,
)

VOLUME = 7
POLY_AFTERTOUCH = 160
CHANNEL_AFTERTOUCH = 208

from .definitions import *
from .engine import (
    listOutputs, openOutput, _getOutputs,
    listInputs, openInput,
    # listen, rec,
    # play, stop, panic, playMetro, wait,
    # TrackGroup, getPastOpened
)

from .new_engine import (
    TrackGroup,
    play, stop
)

from .elements import (
    Seq, Chord, Note, Sil, Track, PNote, Element,
    parse, parse_element
)
from .modulation import *
from .utils import (
    pattern, noob2seq, noteRange,
    rnd, rndWalk, rndGauss, rndPick, rndDur,
    euclid, lcm,
)
from .whistle import whistle, whistleDur, tap, tapDur
from .generators import *
# from .seqs import *
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

def clearAllTracks():
    for track in env.tracks:
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


env.METRONOME_NOTES = (sit13, sit16)

setScale("major", "c")


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
    if "preenfm" in port_name.lower():
        midi_out["preenfm"] = openOutput(i)
        midi_out["pfm"] = midi_out["preenfm"]
    if "irig" in port_name.lower():
        midi_out["irig"] = openOutput(i)

# env.default_output = midi_out["default"]
_metronome_port = midi_out["default"]
if "microfreak" in midi_out:
    env.default_output = midi_out["microfreak"]
elif "fluid" in midi_out:
    env.default_output = midi_out["fluid"]
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
t11 = Track(10, name="t11", sync_from=t1)
t12 = Track(11, name="t12", sync_from=t1)
t13 = Track(12, name="t13", sync_from=t1)
t14 = Track(13, name="t14", sync_from=t1)
t15 = Track(14, name="t15", sync_from=t1)
t16 = Track(15, name="t16", sync_from=t1)

env.tracks = TrackGroup()
env.tracks.addTrack(t1)
env.default_track = t1


def _playT(track: Track, seq: Optional[str]=None):
    """ Start a single track """
    track.stopped = False
    if seq:
        track.clearAdd(seq)
    
    if env.is_playing:
        return
    
    # Synchronize all other tracks to this track
    for t in env.tracks:
        if t == track:
            t.reset()
            t.syncFrom(None)
        else:
            t.stopped = True
            t.syncFrom(track)
    play()


history = LifoQueue(512)

def play(*args, **kwargs):
    state = (args, kwargs)
    history.put(state)
    new_engine.play(*args, **kwargs)

def play1(seq : Optional[str]=None):
    _playT(t1, seq)
def play2(seq : Optional[str]=None):
    _playT(t2, seq)
def play3(seq : Optional[str]=None):
    _playT(t3, seq)
def play4(seq : Optional[str]=None):
    _playT(t4, seq)
def play5(seq : Optional[str]=None):
    _playT(t5, seq)
def play6(seq : Optional[str]=None):
    _playT(t6, seq)
def play7(seq : Optional[str]=None):
    _playT(t7, seq)
def play8(seq : Optional[str]=None):
    _playT(t8, seq)


def pushT1(method: callable, *args, **kwargs):
    t1.pushTrans(method, *args, **kwargs)
def pushT2(method: callable, *args, **kwargs):
    t2.pushTrans(method, *args, **kwargs)
def pushT3(method: callable, *args, **kwargs):
    t3.pushTrans(method, *args, **kwargs)
def pushT4(method: callable, *args, **kwargs):
    t4.pushTrans(method, *args, **kwargs)
def pushT5(method: callable, *args, **kwargs):
    t5.pushTrans(method, *args, **kwargs)
def pushT6(method: callable, *args, **kwargs):
    t6.pushTrans(method, *args, **kwargs)
def pushT7(method: callable, *args, **kwargs):
    t7.pushTrans(method, *args, **kwargs)
def pushT8(method: callable, *args, **kwargs):
    t8.pushTrans(method, *args, **kwargs)

def popT1():
    t1.popTrans()
def popT2():
    t2.popTrans()
def popT3():
    t3.popTrans()
def popT4():
    t4.popTrans()
def popT5():
    t5.popTrans()
def popT6():
    t6.popTrans()
def popT7():
    t7.popTrans()
def popT8():
    t8.popTrans()


def _stopT(track: Track):
    track.stopped = True

    still_playing = list(filter(lambda t: not t.stopped, env.tracks))
    if len(still_playing) == 1:
        # Set remaining track as main track
        main_track = still_playing[0]
        for t in env.tracks:
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