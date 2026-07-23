import heapq

from rtmidi.midiutil import open_midiinput, open_midioutput
from rtmidi.midiconstants import NOTE_ON, NOTE_OFF

import midiseq.env as env
from .elements import Seq, Note
from .definitions import Midi_message


class AbstractPort:
    """Abstract class for both Input and Output ports"""

    def __init__(self) -> None:
        self.port = None
        self.name = "Abstract port"

        # Key state lookup table for every note of every midi channel
        # each state is a list of onset time and key velocity
        self._key_states = [ [0.0, 0] for _ in range(16 * 128) ]
        
        self._time = 0.0
        self._events: list[tuple[int, Midi_message]] = [] # An event is a (timecode, message) tuple

        self._save_notes = False
        self.notes = Seq() # Copy of already played notes
    

    def _get_note_state(self, idx: int) -> tuple[float, int]:
        onset_time = self._key_states[idx][0]
        note_vel = self._key_states[idx][1]
        return onset_time, note_vel


    def _set_note_state(self, idx: int, vel: int) -> None:
        self._key_states[idx][0] = self._time
        self._key_states[idx][1] = vel


    def clear(self) -> None:
        """Clear all events"""
        self._events = []
        self._time = 0.0
        self.notes.clear()


    def isOpen(self) -> bool:
        return self.port.is_port_open()


    def close(self) -> None:
        """Close port"""
        self.port.close_port()



class InputPort(AbstractPort):
    """An opened input Midi port"""

    def __init__(self, port_id: int | str) -> None:
        super().__init__()

        self.port, self.name = open_midiinput(port_id)

        self.forward_ports: list[OutputPort] = []


    def process(self) -> None:
        """Process incoming message by polling, when the engine is started"""
        while in_mess := self.port.get_message():
            if env.display_notes:
                print(f"Midi in: {in_mess}")
            message, time_delta = in_mess
            self._time += time_delta
            self._events.append( (self._time, message) )

            # Forward message to output ports immediatly
            for port in self.forward_ports:
                port.send(message)

            status = message[0]
            channel = status & 0xf
            pitch = message[1]
            
            idx = (channel << 7) | pitch

            if status & 0xf0 == NOTE_ON:
                note_vel = message[2]

                if note_vel == 0:
                    # Actually a note off event
                    onset_time, note_vel = self._get_note_state(idx)
                    note_dur = self._time - onset_time

                    # Save completed note
                    note = Note(pitch, note_dur / env.note_dur, note_vel)
                    self.notes.add(note, head=onset_time)
                
                # Register note
                self._set_note_state(idx, note_vel)

            elif status & 0xf0 == NOTE_OFF:
                onset_time, note_vel = self._get_note_state(idx)
                note_dur = self._time - onset_time

                # Save completed note
                note = Note(pitch, note_dur / env.note_dur, note_vel)
                self.notes.add(note, head=onset_time)

                # Unregister note
                self._set_note_state(idx, 0)
    



class OutputPort(AbstractPort):
    """
    An opened output Midi port.
    
    Attributes:
        transpose (int): Global transposition (in semi-tones)
    """

    def __init__(self, port_id: int | str) -> None:
        super().__init__()

        self.port, self.name = open_midioutput(port_id)

        # Properties
        self.transpose: int = 0


    def process(self, time_delta: float) -> None:
        """
        Send outgoing message to output port.
        This method should be called continuously.
        
        Args:
            time_delta (float): in seconds
        """

        self._time += time_delta

        while (len(self._events) > 0) and (self._events[0][0] <= self._time):
            _, message = heapq.heappop(self._events)
            self.send(message)


    def push(self, time, message: Midi_message) -> None:
        """
        Push an event to be parsed later by this output port.

        Args:
            time (float): relative time of the message
            message (list): A midi message
        """
        time += self._time # Offset by internal port relative time
        heapq.heappush(self._events, (time, message))


    def send(self, message: Midi_message) -> None:
        """Send a note to the output port immediately."""

        if self.transpose != 0:
            message[1] = min(max(message[1] + self.transpose, 0), 127)
        
        # print(f"{self.name[:10]}  {event=}")

        status = message[0]
        channel = status & 0xf
        pitch = message[1]

        idx = (channel << 7) | pitch

        if status & 0xf0 == NOTE_ON:
            note_vel = message[2]

            if self._save_notes and note_vel == 0:
                # Actually a note off event
                onset_time, note_vel = self._get_note_state(idx)
                note_dur = self._time - onset_time

                # Save completed note
                note = Note(pitch, note_dur / env.note_dur, note_vel)
                self.notes.add(note, head=onset_time)
            
            # Register note
            self._set_note_state(idx, note_vel)

        elif status & 0xf0 == NOTE_OFF:
            onset_time, note_vel = self._get_note_state(idx)
            note_dur = self._time - onset_time

            if self._save_notes:
                # Save completed note
                self.notes.add(
                    Note(pitch, note_dur / env.note_dur, note_vel),
                    head=onset_time
                )
            
            # Unregister note
            self._set_note_state(idx, 0)
        
        self.port.send_message(message)


    def allNotesOff(self) -> None:
        for idx in range(16 * 128):
            if self._key_states[idx][1] != 0:
                # This note is still active, send NOTE_OFF message
                channel, pitch = divmod(idx, 128)
                self.port.send_message( [NOTE_OFF | channel, pitch, 0] )