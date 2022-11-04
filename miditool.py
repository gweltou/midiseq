### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

import rtmidi
import time
import threading
from sequence import Seq, Grid
from track import Track
# from scales import *
from generators import *


# DEBUG = True

_tempo = 120
_timeres = 0.01
_playing_thread = None
_listening_thread = None
_must_stop = False
_recording = False
_record = None              # Where the recordings from midi in are stored
_verbose = True
_display = True
_display_min = 36
_display_max = 96


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
    _must_stop = True
    _recording = False
    panic()


def _play(track, channel=1, loop=False):
    print("++++ PLAYBACK Started")
    midi_seq = []
    t0 = time.time()
    t_prev = 0.0
    seq_i = 0
    track.init()
    track.loop=loop
    active_notes = set()
    while True:
        if _must_stop:
            print("++++ PLAYBACK stopping...")
            break

        t = time.time() - t0
        t_norm = t
        t_norm *= _tempo / 120       # A time unit (Seq.length=1) is 1 second at 120bpm
        timedelta = t - t_prev
        timedelta *= _tempo / 120
        t_prev = t
        assert 0 < timedelta < 99

        if midi_seq and seq_i < len(midi_seq):
            new_noteon = False
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
                line = "{}[".format(_display_min)
                for i in range(_display_min, _display_max):
                    if i in active_notes:
                        line += 'x'
                    else:
                        line += '.'
                print(line + ']{}'.format(_display_max))

        
        new_messages = track.update(timedelta)
        if new_messages:
            midi_seq = new_messages
            t0 = time.time()
            t = 0.0
            t_prev = 0.0
            seq_i = 0

        if track.ended:
            break

        t_frame = time.time() - t0 - t
        load = t_frame / _timeres
        if load > 0.2:
            print("++++ PLAYBACK [warning] load:", load, "%")
        time.sleep(min(0.2, max(0, _timeres)))
    print("++++ PLAYBACK Stopped")


def rec():
    global _recording
    _recording = True
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
    recording = False
    
    while True:
        if _must_stop:
            print("++++ LISTEN stopping...")
            break

        if _recording:
            if not recording:
                global _record
                _record = Seq()
                noteon_time = dict()
                t0 = time.time()
                recording = True
        else:
            if recording:
                recording = False

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
                if recording:
                    if pitch in noteon_time:
                        t = noteon_time[pitch] - t0
                        dur = time.time() - noteon_time[pitch]
                        _record.addNote(pitch, dur, head=t)
                if forward:
                    mess.setChannel(forward_channel)
                    midiout.sendMessage(mess)
            if _verbose and not _display:
                    print("Recieved", mess)
            mess = midiin.getMessage()
        if new_noteon and _display:
            # Visualize notes
            line = "{}[".format(_display_min)
            for i in range(_display_min, _display_max):
                if i in active_notes:
                    line += 'x'
                else:
                    line += '.'
            line += ']{}'.format(_display_max)
            if recording:
                line += "  (*)"
            print(line)
        time.sleep(min(0.2, max(0, _timeres)))
    print("++++ LISTEN Stopped")



def listOutputs():
    for i in range(midiout.getPortCount()):
        print( "[{}] {}".format(i, midiout.getPortName(i)) )


def listInputs():
    for i in range(midiin.getPortCount()):
        print( "[{}] {}".format(i, midiin.getPortName(i)) )


def getOutputs():
    outputs = []
    for i in range(midiout.getPortCount()):
        outputs.append( (i, midiout.getPortName(i)) )
    return outputs


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