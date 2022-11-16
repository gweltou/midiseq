### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

import rtmidi
import time
import threading
from sequence import *
from track import Track
from scales import *
from generators import *
from parameters import *


# DEBUG = True

_tempo = 120
_timeres = 0.01
_metronome_click = True
_metronome_div = 4          # Number of divisions in a metronome cycle
_metronome_notes = (75, 85) # Midi click notes
_metronome_pre = 1          # Number of metronome cycle before recording
_playing_thread = None
_listening_thread = None
_must_stop = False
_armed = False              # Ready to record, waiting for the player thread to give the recording trigger
_recording = False
_recording_time = 0.0
_record = None              # Where the recordings from midi in are stored
_verbose = True
_display = True
_display_range = (36, 96)


lock = threading.Lock()

midiout = rtmidi.RtMidiOut()
midiin = rtmidi.RtMidiIn()
t1 = Track()
t2 = Track()
t2.channel = 2
t3 = Track()
t3.channel = 3
t4 = Track()
t4.channel = 4



def panic(channel=1):
    for i in range(16):
        mess = rtmidi.MidiMessage.allNotesOff(i)
        midiout.sendMessage(mess)


def play(seq_or_track=None, channel=1, loop=False):    
    # Wait for other playing thread to stop
    global _playing_thread
    global _must_stop
    if _playing_thread != None:
        _must_stop = True
        _playing_thread.join()
    
    if seq_or_track:
        track = seq_or_track
        if type(seq_or_track) == Note:
            s = Seq()
            s.length=0
            s.add(seq_or_track)
            seq_or_track = s
        if type(seq_or_track) == Seq or type(seq_or_track) == Grid:
            track = Track(channel)
            track.add(seq_or_track)
        _playing_thread = threading.Thread(target=_play, args=(track, channel, loop), daemon=True)
    else:
        tracks = []
        for i in range(16):
            track_name = "t{}".format(i+1)
            if track_name in globals():
                tracks.append(globals()[track_name])
        _playing_thread = threading.Thread(target=_play, args=(tracks[0],), daemon=True)
    
    _must_stop = False
    _playing_thread.start()


def stop():
    global _must_stop
    global _recording
    global _armed
    _must_stop = True
    _recording = False
    _armed = False
    panic()


def _play(track, channel=1, loop=False):
    global _armed
    global _recording
    global _recording_time
    print("++++ PLAYBACK Started")
    midi_seq = []
    t0 = time.time()
    t_prev = 0.0
    metronome_time = 0.0
    metronome_click_count = 0
    seq_i = 0
    track.init()
    track.loop = loop
    active_notes = set()
    clicking = False
    click_note = None
    while True:
        if _must_stop:
            for note in active_notes:
                note_off = rtmidi.MidiMessage.noteOff(channel, note)
                midiout.sendMessage(note_off)
            break
        
        if click_note: # Metronome tick
            note_off = rtmidi.MidiMessage.noteOff(10, click_note)
            midiout.sendMessage(note_off)
            click_note = None

        t = time.time() - t0
        timedelta = t - t_prev
        timedelta *= _tempo / 120   # A time unit (Seq.length=1) is 1 second at 120bpm
        t_prev = t
        assert 0 < timedelta < 99
        metronome_time += timedelta
        if _recording:
            _recording_time += timedelta
        
        if metronome_time > 0.5:
            metronome_click_count += 1
            if metronome_click_count % _metronome_div == 0:
                p = _metronome_notes[0]
                if _armed:
                    print("rec starting")
                    _recording = True
                    _recording_time = 0.0 - _metronome_pre * _metronome_div
                    _armed = False
                    clicking = _metronome_click
            else:
                p = _metronome_notes[1]
            if clicking:
                note_on = rtmidi.MidiMessage.noteOn(10, p, 100)
                midiout.sendMessage(note_on)
                click_note = p
            metronome_time -= 0.5

        if midi_seq and seq_i < len(midi_seq):
            new_noteon = False
            t_norm = t * _tempo / 120
            while t_norm >= midi_seq[seq_i][0]:
                mess = midi_seq[seq_i][1]
                midiout.sendMessage(mess)
                if mess.isNoteOn():
                    active_notes.add(mess.getNoteNumber())
                    new_noteon = True
                elif mess.isNoteOff():
                    active_notes.discard(mess.getNoteNumber())
                
                if _verbose and not _display:
                    print("Sent", mess)
                    
                seq_i += 1
                if seq_i == len(midi_seq):
                    break
            
            if _display and new_noteon:
                # Visualize notes
                line = "{}[".format(_display_range[0])
                for i in range(_display_range[0], _display_range[1]):
                    if i in active_notes:
                        line += 'x'
                    else:
                        line += '.'
                print(line + ']{}'.format(_display_range[1]))

        new_messages = track.update(timedelta)
        if new_messages:
            midi_seq = new_messages
            t0 = time.time()
            t = 0.0
            t_prev = 0.0
            seq_i = 0

        # if track.ended:
        #     break

        t_frame = time.time() - t0 - t
        load = t_frame / _timeres
        if load > 0.2:
            print("++++ PLAYBACK [warning] load:", load, "%")
        time.sleep(min(0.2, max(0, _timeres)))
    print("++++ PLAYBACK Stopped")
    global _playing_thread
    _playing_thread = None


def rec():
    if not _listening_thread:
        print("Listening thread is not started")
        return
    if not _playing_thread:
        print("Call 'play()' to launch a metronome and start recording")

    # global _recording
    # _recording = True
    global _armed
    _armed = True
    print("++++ RECORDING to global var '_record'")


def listen(forward=True, forward_channel=1):
    # Wait for other playing thread to stop
    global _listening_thread
    global _must_stop
    if _listening_thread != None:
        _must_stop = True
        _listening_thread.join()

    _listening_thread = threading.Thread(target=_listen, args=(forward, forward_channel,), daemon=True)
    
    _must_stop = False
    _listening_thread.start()


def _listen(forward=True, forward_channel=1):
    print("++++ LISTEN to midi all midi channels")

    active_notes = set()
    noteon_time = dict()
    # recording = False
    # recording_time = 0.0
    # metronome_ticks = 0
    # metronome_cumul = 0.0
    t0 = time.time()
    t_prev = t0
    # ticking = None
    
    while True:
        if _must_stop:
            break

        t = time.time()
        t_prev = t

        new_noteon = False
        mess = midiin.getMessage()
        while mess:
            pitch = mess.getNoteNumber()
            if mess.isNoteOn():
                active_notes.add(pitch)
                noteon_time[pitch] = time.time()
                new_noteon = True
                if forward:
                    mess.setChannel(forward_channel)
                    midiout.sendMessage(mess)
            elif mess.isNoteOff():
                active_notes.discard(pitch)
                if _recording:
                    if pitch in noteon_time:
                        t = noteon_time[pitch] - t0
                        dur = time.time() - noteon_time[pitch]
                        _record.addNote(pitch, dur, head=_recording_time)
                if forward:
                    mess.setChannel(forward_channel)
                    midiout.sendMessage(mess)
            if _verbose and not _display:
                    print("Recieved", mess)
            mess = midiin.getMessage()
        
        if new_noteon and _display:
            # Visualize notes
            line = "{}[".format(_display_range[0])
            for i in range(_display_range[0], _display_range[1]):
                if i in active_notes:
                    line += 'x'
                else:
                    line += '.'
            line += ']{}'.format(_display_range[1])
            if _recording:
                line += "  (*)"
            print(line)
        
        time.sleep(min(0.2, max(0, _timeres)))
    print("++++ LISTEN Stopped")
    global _listening_thread
    _listening_thread = None


def listInputs():
    for i in range(midiin.getPortCount()):
        print( "[{}] {}".format(i, midiin.getPortName(i)) )


def getInputs():
    return [ (i, midiin.getPortName(i)) for i in range(midiin.getPortCount()) ]


def listOutputs():
    for i in range(midiout.getPortCount()):
        print( "[{}] {}".format(i, midiout.getPortName(i)) )


def getOutputs():
    return [ (i, midiout.getPortName(i)) for i in range(midiout.getPortCount()) ]


def openOutput(port_n):
    if midiout.isPortOpen():
        midiout.closePort()
    print("Opening port {} [{}]".format(port_n, midiout.getPortName(port_n)) )    
    midiout.openPort(port_n)


def openInput(port_n):
    if midiin.isPortOpen():
        midiin.closePort()
    print("Opening port {} [{}]".format(port_n, midiin.getPortName(port_n)) )    
    midiin.openPort(port_n)




if __name__ == "__main__":
    # midiout = rtmidi.RtMidiOut()

    

    listOutputs()
    openOutput(len(getOutputs()) - 1)


    # g=Grid()
    # g.euclid(36, 4)
    # _play(g.toSeq(), 10, True)