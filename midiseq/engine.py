from typing import List, Union, Generator, Optional, Dict
import threading
import time
import heapq

import rtmidi
print(f"Using python-rtmidi V{rtmidi.version.version} and rtmidi V{rtmidi.get_rtmidi_version()}")
from rtmidi.midiutil import (
    list_input_ports, list_output_ports,
    open_midiinput, open_midioutput
)
from rtmidi.midiconstants import (
    NOTE_ON, NOTE_OFF,
    ALL_SOUND_OFF, RESET_ALL_CONTROLLERS,
    CONTROL_CHANGE,
)

import midiseq.env as env
from .elements import Seq, Note, PNote, Chord
from .tracks import Track, tracks




class InputPort:
    """An opened input Midi port"""

    def __init__(self, port_id: Union[int, str]) -> None:
        self.port, self.name = open_midiinput(port_id)

        # Key state lookup table for every note of every midi channel
        # each state is a list of onset time and key velocity
        self._key_states = [ [0.0, 0] for _ in range(16 * 128) ]
        
        self.time = 0.0
        self.events = []
        self.notes = Seq()

        self.forward_ports: List[OutputPort] = []


    def process(self) -> None:
        """Process incoming message by polling, when the engine is started"""
        while in_mess := self.port.get_message():
            if env.display_notes:
                print(f"Midi in: {in_mess}")
            event, time_delta = in_mess
            self.time += time_delta
            self.events.append( (self.time, event) )

            # Forward message to output ports
            for port in self.forward_ports:
                port.send(event)

            status = event[0]
            channel = status & 0xf
            if status & 0xf0 == NOTE_ON:
                note = event[1]
                note_vel = event[2]
                idx = (channel << 7) | note
                if note_vel == 0:
                    note_dur = self.time - self._key_states[idx][0]
                    onset_vel = self._key_states[idx][1]
                    # Save completed note
                    note = Note(note, note_dur / env.note_dur, onset_vel)
                    self.notes.add(note, head=self.time)
                # Register note
                self._key_states[idx][0] = self.time
                self._key_states[idx][1] = note_vel
            elif status & 0xf0 == NOTE_OFF:
                note = event[1]
                idx = (channel << 7) | note
                note_dur = self.time - self._key_states[idx][0]
                note_vel = self._key_states[idx][1]
                # Save completed note
                note = Note(note, note_dur / env.note_dur, note_vel)
                self.notes.add(note, head=self.time)
                # Unregister note
                self._key_states[idx][0] = self.time
                self._key_states[idx][1] = 0
    

    def clear(self) -> None:
        """Clear all events"""
        self.events = []
        self.time = 0.0
        self.notes.clear()


    def isOpen(self) -> bool:
        return self.port.is_port_open()


    def close(self) -> None:
        """Close port"""
        self.port.close_port()



class OutputPort:
    """
    An opened output Midi port
    
    Attributes:
        transpose (int): Global transposition (in semi-tones)
    """

    def __init__(self, port_id: Union[int, str]) -> None:
        self.port, self.name = open_midioutput(port_id)

        # Key state lookup table for every note of every midi channel
        # each state is a list of onset time and key velocity
        self._key_states = [ [0.0, 0] for _ in range(16 * 128) ]
        
        self.time = 0.0
        self.events = []

        self._save_notes = False
        self.notes = Seq()

        # Properties
        self.transpose: int = 0


    def process(self, time_delta: float) -> None:
        """
        Process incoming message by polling, when the engine is started
        
        Args:
            time_delta: in seconds
        """

        self.time += time_delta

        while (len(self.events) > 0) and (self.events[0] <= self.time):
            event = heapq.heappop(self.events)
            self.send(event)


    def push(self, time, event) -> None:
        """
        Push an event to be parsed by this output port

        Args:
            time:
            event:
        """
        time += self.time # Offset by internal port relative time

        if time <= self.time:
            self.send(event)
        else:
            heapq.heappush(self.events, (time, event))


    def send(self, event) -> None:
        if self.transpose != 0:
            event[1] = min(max(event[1] + self.transpose, 0), 127)
        
        # print(f"{self.name[:10]}  {event=}")

        status = event[0]
        channel = status & 0xf
        note = event[1]

        if status & 0xf0 == NOTE_ON:
            note_vel = event[2]

            # Register note
            idx = (channel << 7) | note
            self._key_states[idx][0] = self.time
            self._key_states[idx][1] = note_vel

            if self._save_notes and note_vel == 0:
                note_dur = self.time - self._key_states[idx][0]
                onset_vel = self._key_states[idx][1]
                # Save completed note
                note = Note(note, note_dur / env.note_dur, onset_vel)
                self.notes.add(note, head=self.time)

        elif status & 0xf0 == NOTE_OFF:
            # Unregister note
            idx = (channel << 7) | note
            note_dur = self.time - self._key_states[idx][0]
            note_vel = self._key_states[idx][1]
            self._key_states[idx][0] = self.time
            self._key_states[idx][1] = 0

            if self._save_notes:
                # Save completed note
                self.notes.add(
                    Note(note, note_dur / env.note_dur, note_vel),
                    head=self.time
                )
        
        self.port.send_message(event)


    def allNotesOff(self) -> None:
        for idx in range(16 * 128):
            if self._key_states[idx][1] != 0:
                # This note is still active, send NOTE_OFF message
                channel, pitch = divmod(idx, 128)
                self.port.send_message( [NOTE_OFF | channel, pitch, 0] )


    def clear(self) -> None:
        """Clear all events"""
        self.events = []
        self.time = 0.0
        self.notes.clear()
    

    def isOpen(self) -> bool:
        return self.port.is_port_open()


    def close(self) -> None:
        """Close port"""
        self.port.close_port()



_midiout_ports: Dict[str, OutputPort] = dict()
_midiin_ports: Dict[str, InputPort] = dict()

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


def getInput(port_id : Union[int, str]) -> Optional[InputPort]:
    """
    Open and return a MIDI input port or return an already opened one.
    
    Args:
        port_id (int | str)
            Port number or name (substring included) to open
    """
    if isinstance(port_id, int):
        # A port number
        for i, port_name in getInputs():
            if port_id == i:
                port_id = port_name
                break
        else:
            print(f"Can't find port '{port_id}'")
            return None
    elif isinstance(port_id, str):
        # A port name (or name substring)
        for i, port_name in getInputs():
            if port_id.lower() in port_name.lower():
                port_id = port_name
                break
        else:
            print(f"Can't find port '{port_id}'")
            return None
    
    if port_id in _midiin_ports and _midiin_ports[port_id].isOpen():
        return _midiin_ports[port_id]

    print(f"Opening port {port_id}")
    port = InputPort(port_id)
    if port:
        assert isinstance(port_id, str)
        _midiin_ports[port_id] = port

    return port


def listOutputs():
    """Print the list of Output MIDI ports"""
    for i, port_name in getOutputs():
        print(f"[{i}] {port_name}")


def getOutputs():
    midiout = rtmidi.MidiOut()
    return [ (i, midiout.get_port_name(i)) for i in range(midiout.get_port_count()) ]


def getOutput(port_id : Union[int, str]) -> Optional[OutputPort]:
    """
    Open and return a MIDI output port or return an already opened one
    
    Args:
        port_id (int | str)
            Port number or name (substring included) to open
    """
    if isinstance(port_id, int):
        # A port number
        for i, port_name in getOutputs():
            if port_id == i:
                port_id = port_name
                break
        else:
            print(f"Can't find port '{port_id}'")
            return None
    elif isinstance(port_id, str):
        # A port name (or name substring)
        for i, port_name in getOutputs():
            if port_id.lower() in port_name.lower():
                port_id = port_name
                break
        else:
            print(f"Can't find port '{port_id}'")
            return None
    
    if port_id in _midiout_ports and _midiout_ports[port_id].isOpen():
        return _midiout_ports[port_id]

    print(f"Opening port {port_id}")
    port = OutputPort(port_id)
    if port:
        assert isinstance(port_id, str)
        _midiout_ports[port_id] = port

    return port


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


def is_started():
    """Returns True if the engine is running"""
    return _is_running


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
        time_delta = t_frame - t_prev
        t_prev = t_frame

        time_delta *= env.bpm / 120   # A time unit (Seq.length=1) is 1 second at 120bpm
        rel_time += time_delta

        # Check for trigger signals
        if _trigger_play:
            is_playing = True
            out_events.clear()
            # all_notes_off()
            _trigger_play = False # Unset signal
        if _trigger_stop:
            is_playing = False
            out_events.clear()
            # all_notes_off()
            _trigger_stop = False # Unset signal
        
        # Process incoming messages
        for input_port in _midiin_ports.values():
            input_port.process()

        if is_playing:
            _must_sort = False

            # Run metronome
            metronome_time += time_delta
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
                    out_events.append( (rel_time + env.METRONOME_DUR, note_off, env.default_output) )
                    _must_sort = True

            # Get midi messages from tracks
            for track in tracks.priority_list:
                if new_events := track.update(time_delta):
                    for t, mess in new_events:
                        out_events.append( (t + rel_time, mess, track.port) )
                    _must_sort = True
            
            if _must_sort:
                # Sort by time first, then midi off precedes midi on messages
                heapq.heapify(out_events)
                # out_events.sort(key=lambda n: (n[0],n[1][0]), reverse=True)
                _must_sort = False

            # Process outgoing messages
            _new_noteon = False # Used to display notes in terminal
            while out_events and out_events[0][0] < rel_time:
                # A midi event is made of : absolute_t, midi_mess, midi_port
                # A midi_mess is made of : status, pitch, vel
                t_pos, mess, port = heapq.heappop(out_events)
                if mess[0]>>4 == 9: # note on
                    chan = mess[0] & 0xf
                    _active_notes[mess[1]] |= (1 << chan)
                    _new_noteon = True
                elif mess[0]>>4 == 8: # note off
                    chan = mess[0] & 0xf
                    _active_notes[mess[1]] &= (65535 ^ (1 << chan))
                
                port: Optional[OutputPort] = port or env.default_output
                if port:
                    port.push(t_pos - rel_time, mess)  # Play immediately
                
                if env.verbose and not env.display_notes:
                    print("Sent", mess)
        
        # Process output ports
        for output_port in _midiout_ports.values():
            output_port.process(time_delta)

        if env.display_notes and _new_noteon:
            notes_str = ['.'] * (env.display_range[1] - env.display_range[0] + 1)
            for i, n in enumerate(_active_notes):
                if n == 0:
                    continue
                if i < env.display_range[0]: notes_str[0] = '<'
                elif i > env.display_range[1]: notes_str[-1] = '>'
                else: notes_str[i - env.display_range[0]] = 'x'
            
            notes_str = ''.join(notes_str)
            print(str(env.display_range[0]) + '[' + notes_str + ']' + str(env.display_range[1]))
        
        time.sleep(min(max(time_res, 0), 0.2))


def play(
    what: Union[Track, str, Note, Seq, Generator, None] = None,
    channel: Optional[int] = None,
    instrument: Optional[int] = None,
    loop: Optional[bool] = None
):
    """
    Play a Track, a Sequence or a single Note.

    Args:
        channel: int
            Midi channel, between 0 and 15 (defaults to 0)
        instrument: int
            Instrument to play with (program change message)
        loop: boolean
            Loop playback):
    """
    # print(f"play({what=}, {loop=})")
    global _trigger_play
    _trigger_play = True
    start_io()
    
    if what:
        # Play solo track, seq or note
        if isinstance(what, Track):
            if loop is not None:
                what.loop = loop
                print("loop set", what.loop)
            if channel is not None:
                what.channel = channel
            if instrument is not None:
                what.instrument = instrument
            what.start()
            return
        
        track: Track = env.default_track
        if loop is not None:
            track.loop = loop
        if channel is not None:
            track.channel = channel
        if instrument is not None:
            track.instrument = instrument
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
        for track in tracks:
            if loop is not None:
                track.loop = loop
            track.start()


def stop() -> None:
    global _trigger_stop
    _trigger_stop = True

    for track in tracks:
        track.stop()


def panic() -> None:
    """Stop all active notes on all channel and on all opened ports"""
    for output_port in _midiout_ports.values():
        output_port.allNotesOff()



def rec(self, bars=1, beats=4, metro=2) -> Seq:
    """Records every incoming midi messages until stop() is called
    
    Parameters:
        bars (int):
            Duration of the recording, in bars
        beats (int):
            Number of beats in a bar
        metra (int):
            Number of metronome cycles before recording
    """
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