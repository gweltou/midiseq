### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

from typing import Union, List, Generator
import time
import threading

import rtmidi
from rtmidi.midiconstants import (
    NOTE_ON, NOTE_OFF,
    ALL_SOUND_OFF, RESET_ALL_CONTROLLERS,
    CONTROL_CHANGE,
)
import mido
#from mido import MidiFile

import midiseq.env as env
from .elements import Seq, Note, PNote, Chord, Track, Song


# DEBUG = True

_playing_threads = set()

_listening_thread = None
_timeres = 0.01
_must_stop = False
_armed = False              # Ready to record, waiting for the player thread to give the recording trigger
_recording = False
_recording_time = 0.0
_record = None              # Where the recordings from midi in are stored

_active_notes = [ [False]*128 for _ in range(16) ] # Active notes lookup table



past_opened = list()
def getPastOpened():
    return [ (p, p.is_port_open()) for p in past_opened ]

# lock = threading.Lock()

# midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()


# class MidiPort():
#     def __init__(self, port: Union[rtmidi.MidiIn, rtmidi.MidiOut], name:str):
#         self.name = name



def panic(port=env.default_output): # XXX: default param doesn't work
    for channel in range(16):
        port.send_message([CONTROL_CHANGE | channel, ALL_SOUND_OFF, 0])
        port.send_message([CONTROL_CHANGE | channel, RESET_ALL_CONTROLLERS, 0])
        time.sleep(0.05)



def activeNotesOff() -> None:
    # XXX: What about midi ports
    for chan in range(16):
        for note in range(128):
            if _active_notes[chan][note]:
                note_off = [NOTE_OFF | chan, note, 0]
                env.default_output.send_message(note_off)
                _active_notes[chan][note] = False




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
        
        # Build list from tree
        for track in top_priority:
            self.priority_list.append(track)
            for children_track in track._sync_children:
                self.priority_list.extend( children_track._get_priority_list() )
    
    def __iter__(self):
        yield from self.tracks
    
    def __getitem__(self, index):
        return sorted(self.tracks, key=lambda t:t.name)[index]
                



def play(
        what: Union[Track, Note, Seq, Generator, None]=None,
        channel=0, instrument=0,
        loop=False,
        blocking=False):
    """ Play a Track, a Sequence or a single Note.

        Parameters
        ----------
            channel : int
                Midi channel, between 0 and 15 (defaults to 0)
            instrument : int
                Instrument to play with (program change message)
            loop : boolean
                Loop playback
    """   
    # Wait for other playing thread to stop
    global _playing_threads
    global _must_stop
    _must_stop = False
    

    if what:
        # Play solo track, seq or note
        if isinstance(what, str):
            # what = Track(channel=channel, instrument=instrument, loop=loop)._addGen(genStr2seq, what)
            what = Track(channel=channel, instrument=instrument, loop=loop).add(what)
        elif type(what) in (Note, PNote, Chord):
            what = Seq().add(what)
        elif isinstance(what, Generator):
            what = Track(channel=channel, instrument=instrument, loop=loop)._addGen(what)

        track_group = TrackGroup()
        if isinstance(what, Track):
            track_group.addTrack(what)
        else:
            track_group.addTrack(Track(channel, instrument=instrument, loop=loop).add(what))
        
        if blocking:
            return _play(track_group, loop)
        thread = threading.Thread(target=_play, args=(track_group, loop), daemon=True)
    else:
        # Play all tracks
        if blocking:
            return _play(env.tracks, loop)
        thread = threading.Thread(target=_play, args=(env.tracks, loop), daemon=True)
    
    _playing_threads.add(thread)
    thread.start()
    env.is_playing = True



def _play(track_group: TrackGroup, loop=False):
    global _armed
    global _recording
    global _recording_time

    if env.verbose:
        print("++++ PLAYBACK Started")
    for track in track_group.tracks:
        track.reset()
        track.loop |= loop  # Looping tracks will continue to loop
    midi_events = []
    metronome_time = 0.0
    metronome_click_count = 0
    t0 = time.time()
    song_time = 0.0
    t_prev = 0.0
    clicking = False
    click_note = None
    active_notes_allchan = [False] * 128
    while True:
        if _must_stop:
            activeNotesOff()
            break
        
        if click_note: # Metronome click
            note_off = [0x89, click_note, 0]
            env.default_output.send_message(note_off)
            click_note = None

        t_frame = time.time() - t0
        timedelta = t_frame - t_prev
        timedelta *= env.bpm / 120   # A time unit (Seq.length=1) is 1 second at 120bpm
        t_prev = t_frame
        assert 0 < timedelta < 99
        metronome_time += timedelta
        song_time += timedelta
        if _recording:
            _recording_time += timedelta
        
        if metronome_time > 0.5:
            metronome_click_count += 1
            if metronome_click_count % env.METRONOME_DIV == 0:
                p = env.METRONOME_NOTES[0]
                if _armed:
                    print("rec starting")
                    _recording = True
                    _recording_time = 0.0 - env.METRONOME_PRE * env.METRONOME_DIV
                    _armed = False
                    clicking = env.METRONOME_CLICK
            else:
                p = env.METRONOME_NOTES[1]
            if clicking:
                # note_on = rtmidi.MidiMessage.noteOn(10, p, 100)
                note_on = [0x90, p, 100]
                env.default_output.send_message(note_on)
                click_note = p
            metronome_time -= 0.5

        must_sort = False
        all_ended = True    # Will stay True if all Tracks are ended
        for track in track_group.priority_list:
            new_events = track.update(timedelta)
            if new_events:
                must_sort = True
                for t, mess in new_events:
                    midi_events.append( (t + song_time, mess, track.port) )
            all_ended &= track.ended
        if must_sort:
            # Sort by time first, then midi off precedes midi on messages
            midi_events.sort(key=lambda n: (n[0],n[1][0]), reverse=True)
        if all_ended and len(midi_events) == 0:
            env.is_playing = False
            break

        new_noteon = False
        while midi_events and midi_events[-1][0] < song_time:
            # A midi event is made of : absolute_t, midi_mess, midi_port
            # A midi_mess is made of : status, pitch, vel
            _, mess, port = midi_events.pop()
            if mess[0]>>4 == 9: # note on
                chan = mess[0] & 0xf
                _active_notes[chan][mess[1]] = True
                new_noteon = True
            elif mess[0]>>4 == 8: # note off
                chan = mess[0] & 0xf
                _active_notes[chan][mess[1]] = False
            port = port or env.default_output
            port.send_message(mess)
            if env.verbose and not env.DISPLAY:
                print("Sent", mess)
        
        if env.DISPLAY and new_noteon:
            # Visualize notes

            for note in range(128):
                active_notes_allchan[note] = False
                for chan in range(16):
                    if _active_notes[chan][note]:
                        active_notes_allchan[note] = True
                        break
            
            notes_str = ['.'] * (env.DISPLAY_RANGE[1] - env.DISPLAY_RANGE[0] + 1)
            for i, n in enumerate(active_notes_allchan):
                if not n:
                    continue
                if i < env.DISPLAY_RANGE[0]: notes_str[0] = '<'
                elif i > env.DISPLAY_RANGE[1]: notes_str[-1] = '>'
                else: notes_str[i - env.DISPLAY_RANGE[0]] = 'x'
            
            notes_str = ''.join(notes_str)
            print(str(env.DISPLAY_RANGE[0]) + '[' + notes_str + ']' + str(env.DISPLAY_RANGE[1]))

        # Check CPU load
        t = time.time() - t0 - t_frame
        load = t / _timeres
        if env.verbose and load > 0.2:
            print("++++ PLAYBACK [warning] load:", load, "%")
        time.sleep(min(max(_timeres, 0), 0.2))

    if env.verbose:
        print("++++ Playing thread ended")



def playMetro(beats=4, cycles=1):
    """ Play metronome """
    _lo, _hi = env.METRONOME_NOTES
    clicks = [_hi] + [_lo] * (beats-1)
    metr = Seq(clicks) * (0.5/env.note_dur)
    metr *= int(cycles)
    play(metr, blocking=True)



def listen(forward=True, forward_channel=1):
    # Wait for other playing thread to stop
    global _listening_thread
    global _must_stop
    if _listening_thread != None:
        _must_stop = True
        _listening_thread.join()
    _must_stop = False

    _listening_thread = threading.Thread(target=_listen, args=(forward, forward_channel,), daemon=True)    
    _listening_thread.start()



def _listen(forward=True, forward_channel=1):
    #XXX Doesn't take tempo into account...
    print("++++ LISTEN to midi on all midi channels")

    active_notes = set()
    noteon_time = dict()
    t0 = time.time()
    # t_prev = t0    
    while True:
        if _must_stop:
            break

        # t = time.time()
        # t_prev = t

        new_noteon = False
        mess = midiin.get_message()
        while mess:
            (status, data1, data2), _ = mess
            if status & NOTE_ON == NOTE_ON and data2 > 0:
                active_notes.add(data1)
                noteon_time[data1] = time.time()
                new_noteon = True
                if forward:
                    mess = [(status & 0xf0) | forward_channel, data1, data2]
                    env.default_output.send_message(mess)
            elif status & NOTE_OFF == NOTE_OFF or (status & NOTE_OFF == NOTE_OFF and data2 == 0):
                active_notes.discard(data1)
                if _recording:
                    if data1 in noteon_time:
                        # t = noteon_time[pitch] - t0
                        dur = time.time() - noteon_time[data1]
                        _record.addNote(data1, dur, head=_recording_time)
                if forward:
                    mess = [(status & 0xf0) | forward_channel, data1, data2]
                    env.default_output.send_message(mess)
            if env.verbose and not env.DISPLAY:
                    print("Recieved", mess)
            # mess = midiin.get_message()
        
        if env.DISPLAY and new_noteon:
            # Visualize notes
            notes_str = ['.'] * (env.DISPLAY_RANGE[1] - env.DISPLAY_RANGE[0] + 1)
            for i in active_notes:
                if i < env.DISPLAY_RANGE[0]: notes_str[0] = '<'
                elif i > env.DISPLAY_RANGE[1]: notes_str[-1] = '>'
                else: notes_str[i - env.DISPLAY_RANGE[0]] = 'x'
            notes_str = "".join(notes_str)
            print(str(env.DISPLAY_RANGE[0]) + '[' + notes_str + ']' + str(env.DISPLAY_RANGE[1]))
        
        time.sleep(min(0.2, max(0, _timeres)))
    
    print("++++ LISTEN Stopped")
    global _listening_thread
    _listening_thread = None



def rec():
    if not _listening_thread:
        print("Listening thread is not started")
        return
    # if not _playing_thread:
    #     print("Call 'play()' to launch a metronome and start recording")

    global _armed
    _armed = True
    print("++++ RECORDING to global var '_record'")



def stop():
    global _must_stop
    global _recording
    global _armed

    _must_stop = True
    for th in _playing_threads:
        th.join()
    _playing_threads.clear()
    
    if env.verbose:
        print("++++ PLAYBACK Stopped")

    _recording = False
    _armed = False
    env.is_playing = False
    #panic()



def wait():
    print("Waiting...")
    while True:
        all_ended = True
        for th in _playing_threads:
            all_ended &= not th.is_alive()
        
        if all_ended:
            print("Stopped")
            break
        
        time.sleep(0.2)



def listInputs():
    for i in range(midiin.get_port_count()):
        print( "[{}] {}".format(i, midiin.get_port_name(i)) )


def _getInputs():
    return [ (i, midiin.get_port_name(i)) for i in range(midiin.get_port_count()) ]


def listOutputs():
    midiout = rtmidi.MidiOut()
    for i in range(midiout.get_port_count()):
        print( "[{}] {}".format(i, midiout.get_port_name(i)) )

def _getOutputs():
    midiout = rtmidi.MidiOut()
    return [ (i, midiout.get_port_name(i)) for i in range(midiout.get_port_count()) ]



def openOutput(port_n : Union[int, str]):
    if isinstance(port_n, str):
        for i, name in _getOutputs():
            if port_n.lower() in name.lower():
                port_n = i
                break
        else:
            print(f"Can't find '{port_n}'")
            port_n = 0

    midiout = rtmidi.MidiOut()
    # if midiout.is_port_open():
    #     midiout.close_port()
    print(f"Opening port {port_n} [{midiout.get_port_name(port_n)}], setting as env.default_output")    
    midiout.open_port(port_n)
    env.default_output = midiout
    past_opened.append(midiout)
    return midiout


def openInput(port_n):
    if midiin.is_port_open():
        midiin.close_port()
    print("Opening port {} [{}]".format(port_n, midiin.get_port_name(port_n)) )    
    midiin.open_port(port_n)



def openFile(path, track=1):
    """
        Open a midi file with mido

        Inside a track, delta time is in midi ticks
        A beat is the same as a 1/4 note == metronome click
        ticks per beat == pulse per quarter note (PPQ)
        midi tempo is in msec per beat
        Rate of midi clock is 24 PPQ
    """

    mid = mido.MidiFile(path)
    print("Midi file type", mid.type)
    print("ticks per beat:", mid.ticks_per_beat)
    print("number of tracks:", len(mid.tracks))
    print("track0:", mid.tracks[0])
    m, s = divmod(mid.length, 60)
    print("Song length: {}'{}".format(int(m), int(s)))
    divisor = mid.ticks_per_beat * 2

    song = Song()

    # Get tempo
    # https://mido.readthedocs.io/en/latest/midi_files.html#tempo-and-beat-resolution
    for mess in mid.tracks[0]:
        if mess.is_meta and mess.type == "set_tempo":
            tempo = round(60 * 1_000_000 / mess.tempo, 3)
            print("Found tempo:", tempo)
            song.tempo = tempo
        if mess.is_meta and mess.type == "time_signature":
            num = mess.numerator
            den = 2 ** mess.denominator
            song.time_signature = (num, den)
            print("Found time signature: {}/{}".format(num, den))


    # Get first track:
    active_notes = dict()
    s = Seq()
    time = 0

    for msg in mid.tracks[track]:
        if msg.is_meta:
            print(msg)        

        time += msg.time
        if msg.type == 'note_on':
            active_notes[msg.note] = (time, msg.velocity)
        elif msg.type == 'note_off' and msg.note in active_notes:
            t0, vel = active_notes.pop(msg.note)
            d = time - t0
            n = Note(msg.note, d/divisor, vel)
            s.add(n, head=t0/divisor)
    song.tracks.append(s)

    return song