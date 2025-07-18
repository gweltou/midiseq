from typing import List, Union, Generator, Optional, Dict
import threading
import time

import rtmidi
from rtmidi.midiconstants import (
    NOTE_ON, NOTE_OFF,
    ALL_SOUND_OFF, RESET_ALL_CONTROLLERS,
    CONTROL_CHANGE,
)
import rtmidi.midiutil

import midiseq.env as env
from .elements import Seq, Note, PNote, Chord, Track, Song



class TrackGroup:
    """ A group of synchronized Tracks
    """

    def __init__(self):
        self.tracks = set()
        self.priority_list: List[Track] = [] # Must update in this order

    def addTrack(self, track: Track):
        self.tracks.add(track)
        track.setGroup(self)
        for t in track._get_priority_list():
            self.tracks.add(t)
        self._build_priority_list()

    # def stopAll(self):
    #     for t in self.tracks:
    #         t.stopped = True

    def _build_priority_list(self) -> None:
        # Build priority tree
        self.priority_list: List[Track] = []
        top_priority = []
        for track in self.tracks:
            track._sync_children = []
        
        for track in self.tracks:
            if track._sync_from != None:
                track._sync_from._sync_children.append(track)
            else:
                top_priority.append(track)
        top_priority.reverse()
        
        # Build list from tree
        for track in top_priority:
            self.priority_list.append(track)
            for children_track in track._sync_children:
                self.priority_list.extend( children_track._get_priority_list() )
    
    def __iter__(self):
        yield from self.tracks
    
    def __getitem__(self, index):
        return sorted(self.tracks, key=lambda t:t.name)[index]


_midiout_ports: Dict[int, rtmidi.MidiOut] = dict()
_midiin_ports: Dict[int, rtmidi.MidiIn] = dict()

time_res = 0.01
metronome = False
_is_running = False
_thread = None
_active_notes = [0b0000000000000000] * 128 # Active notes lookup table

# Signal triggers to communicate with IO thread
_trigger_play = False
_trigger_stop = False



def listInputs():
    """Print the list of Input MIDI ports"""
    for i, port_name in getInputs():
        print(f"[{i}] {port_name}")


def getInputs():
    midiin = rtmidi.MidiIn()
    return [ (i, midiin.get_port_name(i)) for i in range(midiin.get_port_count()) ]


def getInput(port_i : Union[int, str]):
    """Open and return a MIDI input port or return an already opened one"""
    if isinstance(port_i, str):
        for i, name in getInputs():
            if port_i.lower() in name.lower():
                port_i = i
                break
        else:
            print(f"Can't find '{port_i}', opening default port")
            port_i = 0
    
    if port_i in _midiin_ports and _midiin_ports[port_i].is_port_open():
        port = _midiin_ports[port_i]
    else:
        midiin = rtmidi.MidiIn()
        print(f"Opening port {port_i} [{midiin.get_port_name(port_i)}]")
        midiin.open_port(port_i)
        _midiout_ports[port_i] = midiin
        port = midiin

    env.default_input = port
    print(f"Setting port as env.default_input")

    return port


def listOutputs():
    """Print the list of Output MIDI ports"""
    for i, port_name in getOutputs():
        print(f"[{i}] {port_name}")


def getOutputs():
    midiout = rtmidi.MidiOut()
    return [ (i, midiout.get_port_name(i)) for i in range(midiout.get_port_count()) ]


def getOutput(port_i : Union[int, str]):
    """Open and return a MIDI output port or return an already opened one"""
    if isinstance(port_i, str):
        for i, name in getOutputs():
            if port_i.lower() in name.lower():
                port_i = i
                break
        else:
            print(f"Can't find '{port_i}', opening default port")
            port_i = 0
    
    if port_i in _midiout_ports and _midiout_ports[port_i].is_port_open():
        port = _midiout_ports[port_i]
    else:
        midiout = rtmidi.MidiOut()
        print(f"Opening port {port_i} [{midiout.get_port_name(port_i)}]")
        midiout.open_port(port_i)
        _midiout_ports[port_i] = midiout
        port = midiout

    env.default_output = port
    print(f"Setting port as env.default_output")

    return port


def openInput(port_n):
    if midiin.is_port_open():
        midiin.close_port()
    print("Opening port {} [{}]".format(port_n, midiin.get_port_name(port_n)) )    
    midiin.open_port(port_n)



def start_io():
    global _thread
    global _is_running

    if _is_running:
        return
    _is_running = True
    
    _thread = threading.Thread(target=_run, daemon=True)
    _thread.start()
    print("IO thread started")


def stop_io():
    global _is_running

    _is_running = False
    if _thread != None:
        _thread.join()
    print("IO thread stopped")


def _run():
    global _trigger_play, _trigger_stop

    t_prev = time.time()
    rel_time = 0.0
    metronome_time = 0.0
    metronome_click_count = 0
    is_playing = _trigger_play
    out_events = []

    while _is_running:
        t_frame = time.time()
        timedelta = t_frame - t_prev
        timedelta *= env.bpm / 120   # A time unit (Seq.length=1) is 1 second at 120bpm
        t_prev = t_frame
        rel_time += timedelta

        # Check for trigger signals
        if _trigger_play:
            is_playing = True
            out_events.clear()
            all_notes_off()
            _trigger_play = False
        if _trigger_stop:
            is_playing = False
            out_events.clear()
            all_notes_off()
            _trigger_stop = False
        

        # Process incoming messages
        while in_mess := midiin.get_message():
           print(in_mess)

        if is_playing:
            sort_events = False

            # Process Metronome
            metronome_time += timedelta
            if metronome_time > 0.5:
                metronome_click_count += 1
                metronome_time -= 0.5
                if env.METRONOME:
                    if metronome_click_count % env.METRONOME_DIV == 0:
                        metro_pitch = env.METRONOME_NOTES[0]
                        # if _armed:
                        #     print("rec starting")
                        #     _recording = True
                        #     _recording_time = 0.0 - env.METRONOME_PRE * env.METRONOME_DIV
                        #     _armed = False
                        #     clicking = env.METRONOME_CLICK
                    else:
                        metro_pitch = env.METRONOME_NOTES[1]
                    note_on = [NOTE_ON | env.METRONOME_CHAN, metro_pitch, 100]
                    out_events.append( (rel_time, note_on, env.default_output) )
                    note_off = [NOTE_OFF | env.METRONOME_CHAN, metro_pitch, 0]
                    out_events.append((rel_time+env.METRONOME_DUR, note_off, env.default_output))
                    sort_events = True

            # Get midi messages from tracks
            for track in env.tracks.priority_list:
                new_events = track.update(timedelta)
                if new_events:
                    sort_events = True
                    for t, mess in new_events:
                        out_events.append( (t + rel_time, mess, track.port) )
            if sort_events:
                # Sort by time first, then midi off precedes midi on messages
                out_events.sort(key=lambda n: (n[0],n[1][0]), reverse=True)

            # Process outgoing messages
            new_noteon = False
            while out_events and out_events[-1][0] < rel_time:
                # A midi event is made of : absolute_t, midi_mess, midi_port
                # A midi_mess is made of : status, pitch, vel
                _, mess, port = out_events.pop()
                if mess[0]>>4 == 9: # note on
                    chan = mess[0] & 0xf
                    _active_notes[mess[1]] |= (1 << chan)
                    new_noteon = True
                elif mess[0]>>4 == 8: # note off
                    chan = mess[0] & 0xf
                    _active_notes[mess[1]] &= (65535 ^ (1 << chan))
                port = port or env.default_output
                port.send_message(mess)
                if env.verbose and not env.DISPLAY:
                    print("Sent", mess)
        
        if env.DISPLAY and new_noteon:
            notes_str = ['.'] * (env.DISPLAY_RANGE[1] - env.DISPLAY_RANGE[0] + 1)
            for i, n in enumerate(_active_notes):
                if n == 0:
                    continue
                if i < env.DISPLAY_RANGE[0]: notes_str[0] = '<'
                elif i > env.DISPLAY_RANGE[1]: notes_str[-1] = '>'
                else: notes_str[i - env.DISPLAY_RANGE[0]] = 'x'
            
            notes_str = ''.join(notes_str)
            print(str(env.DISPLAY_RANGE[0]) + '[' + notes_str + ']' + str(env.DISPLAY_RANGE[1]))
        
        
        time.sleep(min(max(time_res, 0), 0.2))



def play(
    what: Union[Track, str, Note, Seq, Generator, None]=None,
    channel: Optional[int]=None,
    instrument: Optional[int]=None,
    loop: Optional[bool]=None):
    """Play a Track, a Sequence or a single Note.

    Parameters
    ----------
        channel : int
            Midi channel, between 0 and 15 (defaults to 0)
        instrument : int
            Instrument to play with (program change message)
        loop : boolean
            Loop playback):
    """
    global _trigger_play
    _trigger_play = True
    start_io()
    
    if not channel:
        channel = env.default_channel
    
    if what:
        # Play solo track, seq or note
        if isinstance(what, Track):
            what.start()
            return
        
        track : Track = env.default_track
        if loop != None:
            track.loop = loop
        track.clear()
        track.start()
        
        if isinstance(what, (str, Seq)):
            # what = Track(channel=channel, instrument=instrument, loop=loop)._addGen(genStr2seq, what)
            track.add(what)
        elif type(what) in (Note, PNote, Chord):
            track.add(Seq(what))
        elif isinstance(what, Generator):
            track._addGen(what)
        
    else:
        # Play all tracks
        for track in env.tracks:
            if loop != None:
                track.loop = loop
            track.start()


def stop():
    global _trigger_stop
    _trigger_stop = True

    for track in env.tracks:
        track.stop()


def all_notes_off():
    # XXX: What about midi ports ?
    for pitch, status in enumerate(_active_notes):
        if status == 0:
            continue
        for chan in range(16):
            if status & 2**chan: # This note is active on this channel
                note_off = [NOTE_OFF | chan, pitch, 0]
                env.default_output.send_message(note_off)
        _active_notes[pitch] = 0




def rec(bars=1, beats=4, metro=2) -> Seq:
    """Records every incoming midi messages until stop() is called"""
    start_io()
        
    self.accumulated_time = 0.0
    dur = bars * beats * 60 / env.bpm
    while self.accumulated_time < dur:
        pass
    # close unfinished notes

def recWith(self, seq: Seq) -> Seq:
    """Record while playing an accompanying sequence"""
    self.run()

def recOver(self, seq: Seq) -> Seq:
    """Record over a given sequence"""
    self.run()