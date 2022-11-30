### source: https://eli.thegreenplace.net/2011/12/27/python-threads-communication-and-stopping

import rtmidi
#from mido import MidiFile
import mido
import time
import threading
from sequence import *
from generators import *
import env


# DEBUG = True


_metronome_click = True
_metronome_div = 4          # Number of quarter notes in a metronome cycle
_metronome_pre = 1          # Number of metronome cycle before recording
_metronome_port = None      # Midi port for metronome

_playing_thread = None
_listening_thread = None
_timeres = 0.01
# _tempo = 120
_must_stop = False
_armed = False              # Ready to record, waiting for the player thread to give the recording trigger
_recording = False
_recording_time = 0.0
_record = None              # Where the recordings from midi in are stored



lock = threading.Lock()

# midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()
t1 = Track()
t2 = Track()
t2.channel = 2
t3 = Track()
t3.channel = 3
t4 = Track()
t4.channel = 4



# def panic(channel=1):
#     for i in range(16):
#         mess = rtmidi.MidiMessage.allNotesOff(i)
#         _default_output.sendMessage(mess)

import queue
 
class PeekablePriorityQueue(queue.PriorityQueue):
    def peek(self):
        """Peeks the first element of the queue
         
        Returns
        -------
        item : object
            First item in the queue
         
        Raises
        ------
        queue.Empty
            No items in the queue
        """
        try:
            with self.mutex:
                return self.queue[0]
        except IndexError:
            raise queue.Empty


def play(what=None, channel=1, loop=False):
    """ Play a Song, a Track, a Sequence or a single Note

        Parameters
        ----------
            channel (int):
                Midi channel, between 1 and 16 (defaults to 1)
            loop (boolean):
                Loop playback
    """   
    # Wait for other playing thread to stop
    global _playing_thread
    global _must_stop
    if _playing_thread != None:
        _must_stop = True
        _playing_thread.join()
    
    if what:
        track = what
        if type(what) is Note:
            s = Seq()
            s.length=0
            s.add(what)
            what = s
        if type(what) is Seq:
            track = Track(channel)
            track.add(what)
        _playing_thread = threading.Thread(target=_play, args=([track], channel, loop), daemon=True)
    else:    # Play all tracks
        tracks = []
        for i in range(16):
            track_name = "t{}".format(i+1)
            if track_name in globals():
                tracks.append(globals()[track_name])
        _playing_thread = threading.Thread(target=_play, args=(tracks, channel, loop), daemon=True)
    
    _must_stop = False
    _playing_thread.start()


def _play(tracks, channel=1, loop=False):
    global _armed
    global _recording
    global _recording_time
    print("++++ PLAYBACK Started")
    for track in tracks:
        track.reset()
        track.loop = loop
    midi_messages = []
    active_notes = set()
    metronome_time = 0.0
    metronome_click_count = 0
    t0 = time.time()
    song_time = 0.0
    t_prev = 0.0
    clicking = False
    click_note = None
    while True:
        if _must_stop:
            for note in active_notes:
                note_off = [0x80 + channel-1, note, 0]
                env.DEFAULT_OUTPUT.send_message(note_off)
            break
        
        if click_note: # Metronome click
            note_off = [0x89, click_note, 0]
            env.DEFAULT_OUTPUT.send_message(note_off)
            click_note = None

        t_frame = time.time() - t0
        timedelta = t_frame - t_prev
        timedelta *= env.TEMPO / 120   # A time unit (Seq.length=1) is 1 second at 120bpm
        t_prev = t_frame
        assert 0 < timedelta < 99
        metronome_time += timedelta
        song_time += timedelta
        if _recording:
            _recording_time += timedelta
        
        if metronome_time > 0.5:
            metronome_click_count += 1
            if metronome_click_count % _metronome_div == 0:
                p = env.METRONOME_NOTES[0]
                if _armed:
                    print("rec starting")
                    _recording = True
                    _recording_time = 0.0 - _metronome_pre * _metronome_div
                    _armed = False
                    clicking = _metronome_click
            else:
                p = env.METRONOME_NOTES[1]
            if clicking:
                # note_on = rtmidi.MidiMessage.noteOn(10, p, 100)
                note_on = [0x90, p, 100]
                env.DEFAULT_OUTPUT.send_message(note_on)
                click_note = p
            metronome_time -= 0.5

        must_sort = False
        for track in tracks:
            new_messages = track.update(timedelta)
            if new_messages:
                must_sort = True
                for t, mess in new_messages:
                    midi_messages.append( (t + song_time, mess) )
        if must_sort:
            midi_messages.sort(reverse=True)

        new_noteon = False
        while len(midi_messages) > 0 and midi_messages[-1][0] < song_time:
            mess = midi_messages.pop()[1]
            if mess[0]>>4 == 9: # note on
                active_notes.add(mess[1])
                new_noteon = True
            elif mess[0]>>4 == 8: # note off
                active_notes.discard(mess[1])
            env.DEFAULT_OUTPUT.send_message(mess)
            if env.VERBOSE and not env.DISPLAY:
                print("Sent", mess)
        
        if env.DISPLAY and new_noteon:
            # Visualize notes
            notes_str = ['.'] * (env.DISPLAY_RANGE[1] - env.DISPLAY_RANGE[0] + 1)
            for i in active_notes:
                if i < env.DISPLAY_RANGE[0]: notes_str[0] = '<'
                elif i > env.DISPLAY_RANGE[1]: notes_str[-1] = '>'
                else: notes_str[i - env.DISPLAY_RANGE[0]] = 'x'
            notes_str = "".join(notes_str)
            print(str(env.DISPLAY_RANGE[0]) + '[' + notes_str + ']' + str(env.DISPLAY_RANGE[1]))

        # Check CPU load
        t = time.time() - t0 - t_frame
        load = t / _timeres
        if load > 0.2:
            print("++++ PLAYBACK [warning] load:", load, "%")
        time.sleep(min(0.2, max(0, _timeres)))

    print("++++ PLAYBACK Stopped")
    global _playing_thread
    _playing_thread = None


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
    #XXX Doesn't take tempo into account...
    print("++++ LISTEN to midi all midi channels")

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
            pitch = mess[1]
            if mess.isNoteOn():
                active_notes.add(pitch)
                noteon_time[pitch] = time.time()
                new_noteon = True
                if forward:
                    mess.setChannel(forward_channel)
                    env.DEFAULT_OUTPUT.send_message(mess)
            elif mess.isNoteOff():
                active_notes.discard(pitch)
                if _recording:
                    if pitch in noteon_time:
                        # t = noteon_time[pitch] - t0
                        dur = time.time() - noteon_time[pitch]
                        _record.addNote(pitch, dur, head=_recording_time)
                if forward:
                    mess.setChannel(forward_channel)
                    env.DEFAULT_OUTPUT.send_message(mess)
            if env.VERBOSE and not env.DISPLAY:
                    print("Recieved", mess)
            mess = midiin.get_message()
        
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
    if not _playing_thread:
        print("Call 'play()' to launch a metronome and start recording")

    global _armed
    _armed = True
    print("++++ RECORDING to global var '_record'")


def stop():
    global _must_stop
    global _recording
    global _armed
    _must_stop = True
    _recording = False
    _armed = False
    #panic()


def listInputs():
    for i in range(midiin.get_port_count()):
        print( "[{}] {}".format(i, midiin.getPortName(i)) )


def getInputs():
    return [ (i, midiin.getPortName(i)) for i in range(midiin.get_port_count()) ]


def listOutputs():
    midiout = rtmidi.MidiOut()
    for i in range(midiout.get_port_count()):
        print( "[{}] {}".format(i, midiout.get_port_name(i)) )


def getOutputs():
    midiout = rtmidi.MidiOut()
    return [ (i, midiout.get_port_name(i)) for i in range(midiout.get_port_count()) ]


def openOutput(port_n):
    midiout = rtmidi.MidiOut()
    # if midiout.is_port_open():
    #     midiout.close_port()
    print("Opening port {} [{}]".format(port_n, midiout.get_port_name(port_n)) )    
    midiout.open_port(port_n)
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

    mid = MidiFile(path)
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




env.METRONOME_NOTES = (sit13, sit16)
setScale("chromatic")
    
midi_out = dict()
midi_out["default"] = openOutput(0)
for i, port_name in getOutputs():
    if "microfreak" in port_name.lower():
        midi_out["microfreak"] = openOutput(i)
        midi_out["mf"] = midi_out["microfreak"]
    if "fluid" in port_name.lower():
        midi_out["fluid"] = openOutput(i)
        midi_out["fl"] = midi_out["fluid"]


env.DEFAULT_OUTPUT = midi_out["default"]
_metronome_port = midi_out["default"]
if "microfreak" in midi_out:
    env.DEFAULT_OUTPUT = midi_out["microfreak"]
elif "fluid" in midi_out:
    env.DEFAULT_OUTPUT = midi_out["fluid"]