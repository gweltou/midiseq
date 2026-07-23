from __future__ import annotations
from typing import List, Union, Generator, Optional, Callable, Tuple

from rtmidi.midiconstants import (
    PROGRAM_CHANGE,
)

from .elements import Seq, parse
from .ports import OutputPort



# class Track_old():
#     """
#     Track where you can add Sequence.
    
#     You can had a silence by adding an empty Sequence with a non-zero duration.
#     You can define a generator callback function by modifing the generator property.

#     Args:
#         channel (int): Midi channel [0-15]
#     """

#     def __init__(self,
#                 channel=0, instrument=None,
#                 name=None, loop=False,
#                 sync_from: Optional["Track"] = None
#                 ):
#         self.name = name #or f"Track{len(Track._all_tracks)+1}"
#         self.port = None
#         self.channel = channel
#         self.instrument = instrument or 0
#         self.seqs: List[Union[Seq, str, int]] = []
#         self.generators = dict()  # Dictionary of generators and their args
#         self.muted = False
#         self.stopped = True
#         self.transpose = 0
#         self.loop = loop
#         self.loop_type = "all" # "last" / "all"
#         # self.shuffle = False
#         self.offset = 0.0        
#         self.send_program_change = True

#         self._sync_children: List[Track] = []
#         self._sync_from: Optional[Track] = sync_from
#         if sync_from != None:
#             sync_from._sync_children.append(self)
        
#         self.transforms = []


#     def add(self, sequence: Union[str, Seq, Callable, Generator], *args, **kwargs) -> Track:
#         """
#             Add a sequence or a generator to this track.
#         """

#         # if isinstance(sequence, str):
#         #     sequence = parse(sequence)
#         if callable(sequence) or isinstance(sequence, Generator):
#             return self._addGen(sequence, *args, **kwargs)
        
#         self.seqs.append(sequence)
#         return self


#     def _addGen(self, func: Union[Generator, Callable], *args, **kwargs) -> Track:
#         """
#             Add a sequence generator to this track.
#             A callable should be provided, not the generator itself.
#             When a callable is provided, the generator can be resetted.
#         """

#         if isinstance(func, Generator):
#             generator = func
#         else:
#             generator = func(*args, **kwargs)
#         gen_id = id(generator)
#         self.generators[gen_id] = {
#             "func": func if callable(func) else None,
#             "args": args, "kwargs": kwargs,
#             "generator": generator,
#             # "seqs": [],
#             }
#         self.seqs.append(gen_id)
#         return self


#     def delLast(self):
#         if self.seqs:
#             self.seqs = self.seqs[:-1]

#     def delAdd(self, sequence: Union[str, Seq, Callable, Generator], *args, **kwargs) -> Track:
#         if self.seqs:
#             self.seqs.pop()

#         return self.add(sequence)


#     def clearAdd(self, sequence: Union[str, Seq, Callable, Generator], *args, **kwargs) -> Track:
#         self.clear()
#         self.add(sequence, *args, **kwargs)

#     def clear(self):
#         self.seqs.clear()
#         self.generators.clear()
#         self.seq_i = 0
    

#     def getParam(self, other: Track):
#         self.port = other.port
#         self.channel = other.channel
#         self.instrument = other.instrument
    

#     def start(self, loop:Optional[bool] = None):
#         self.reset()
#         self.stopped = False
#         if loop is not None:
#             self.loop = loop
    
#     def startSync(self, loop:Optional[bool] = None):
#         """Start this track synchronized with the currently playing tracks"""
#         raise NotImplementedError


#     def stop(self):
#         self.stopped = True


#     def reset(self):
#         self._next_timer = self.offset
#         self.seq_i = 0
    

#     def mute(self):
#         self.muted = True
    
#     def unmute(self):
#         self.muted = False


#     def setGroup(self, track_group):
#         self._sync_group = track_group
#         for t in self._sync_children:
#             t.setGroup(track_group)


#     def syncFrom(self, other: Optional[Track]) -> None:
#         if self._sync_from != None:
#             # Unsync first
#             self._sync_from._sync_children.remove(self)
#         self._sync_from = other
#         if other != None:
#             other._sync_children.append(self)
    
#     def _sync(self) -> None:
#         if self.stopped:
#             self.start()
    

#     def _get_priority_list(self) -> List[Track]:
#         pl = [self]
#         for t in self._sync_children:
#             pl.extend(t._get_priority_list())
#         return pl


#     def push(self, method: Callable, *args, **kwargs):
#         """
#         Add a transform operation to the pile (a method from Seq class)
#         Sequences from the Track will go through the pile of modifiers
#         """
#         self.transforms.append((method, args, kwargs))
    
#     def pop(self):
#         del self.transforms[-1]
    
#     def popPush(self, method: Callable, *args, **kwargs):
#         self.pop()
#         self.push(method, *args, **kwargs)
    

#     def clearTrans(self):
#         self.transforms.clear()


#     def update(self, timedelta) -> Optional[List[tuple]]:
#         """Returns MidiMessages when a new sequence just started"""

#         # TODO: allow looping for finished generators

#         if self.stopped:
#             return

#         if not self.seqs:
#             self.stopped = True
#             return
        
#         # Let time flow, until next event
#         self._next_timer -= timedelta
#         if self._next_timer > 0.0:
#             return
        
#         for t in self._sync_children:
#             t._sync()

#         if self.seq_i < len(self.seqs):
#             # Send next sequence
#             sequence = self.seqs[self.seq_i]
#             if isinstance(sequence, int):
#                 # It's a generator !
#                 gen_id = sequence
#                 gen_data = self.generators[gen_id]
#                 try:
#                     # Generator is still generating
#                     sequence = next(self.generators[gen_id]["generator"])
#                     # Add generated sequence to cache
#                     # self.generators[gen_id]["seqs"].append(sequence)
#                 except StopIteration:
#                     if gen_data["func"]:
#                         # Reload generator
#                         args = gen_data["args"]
#                         kwargs = gen_data["kwargs"]
#                         new_gen = gen_data["func"](*args, **kwargs)
#                         gen_data["generator"] = new_gen
#                         sequence = next(new_gen)
#                     else:
#                         # Skip
#                         self.seq_i += 1
#                         return self.update(0.0)
#                 # else:
#                      # sequence index won't increment until generator finishes
#                 #     self.seq_i -= 1
#             elif isinstance(sequence, str):
#                 # A symbolic string sequence
#                 sequence, updated_sequence = self.parse_seq(sequence)
#                 # Update string sequence state
#                 self.seqs[self.seq_i] = updated_sequence
            
#             self.seq_i += 1

#             if self.muted:
#                 messages = None
#             else:
#                 # Modifiers
#                 if self.transforms:
#                     sequence = sequence.copy()
#                     for mod, args, kwargs in self.transforms:
#                         try:
#                             sequence = mod(sequence, *args, **kwargs)
#                         except TypeError:
#                             pass

#                 messages = (sequence^self.transpose).getMidiMessages(self.channel)
#                 # Add midi modulation sequence
#                 if sequence.modseq is not None:
#                     messages.extend(sequence.modseq.getMidiMessages(self.channel))

#                 # MIDI messages don't need to be sorted at this point
#                 messages = [ (t + self._next_timer, mess) for t, mess in messages ]
            
#             if self.instrument and self.send_program_change:
#                 program_change = [PROGRAM_CHANGE | self.channel, self.instrument]
#                 # Make sure the instrument change precedes the notes
#                 return [ (self._next_timer - 0.0001, program_change) ] + messages

#             self._next_timer += sequence.dur
#             return messages

#         elif self.seq_i >= len(self.seqs):
#             # End of track reached
#             if not self.loop:
#                 self.stopped = True
#                 return
            
#             # Looping
#             if self.loop_type == "all":
#                 self.seq_i = 0
#             elif self.loop_type == "last":
#                 self.seq_i -= 1
#             else:
#                 raise Exception(f"'loop_type' property should be set to 'all' or 'last', but got '{self.loop_type}' instead")


#     def parse_seq(self, seq_string) -> Tuple[Seq, str]:
#         """Parse a symbolic string sequence and return a Seq"""
#         element, updated_string = parse(seq_string)
#         if not isinstance(element, Seq):
#             element = Seq(element)
#         return element, updated_string

#     def __getitem__(self, index):
#         return self.seqs[index]
    
#     def __len__(self):
#         return len(self.seqs)
    
#     def __repr__(self):
#         if self._sync_from != None:
#             return f"Track(channel={self.channel}, loop={self.loop}, name={self.name}, sync_from={self._sync_from.name})"
#         return f"Track(channel={self.channel}, loop={self.loop}, name={self.name})"



class Track():
    """
    Track where you can add sequences.
    
    You can add silences by adding empty sequences with a non-zero duration.
    You can define a generator callback function by modifying the generator's property.

    Args:
        channel (int): Midi channel [0-15]
    """

    def __init__(self,
                port=None,
                channel=0, instrument=None,
                name=None, loop=False,
                sync_from: Track | None = None
                ):
        self.name = name #or f"Track{len(Track._all_tracks)+1}"
        self.port: OutputPort | None = port
        self.channel = channel
        self.instrument = instrument or 0
        self.sequences: list[Seq | str | int] = []
        self.generators = dict()  # Dictionary of generators and their args
        self.muted = False
        self.stopped = True
        self.transpose = 0
        self.loop = loop
        self.loop_type = "all" # "last" / "all"
        # self.shuffle = False
        self.offset = 0.0        
        self.send_program_change = True

        self._sync_children: list[Track] = []
        self._sync_from: Track | None = sync_from
        if sync_from != None:
            sync_from._sync_children.append(self)
        
        self.transforms = []

        self._sequence_idx = 0
        self._sequence_timer = 0.0
        self._sequence_dur = 0.0
        self._messages = []
        self._message_idx = 0
    

    def setPort(self, port: OutputPort) -> None:
        self.port = port


    def add(self, sequence: str | Seq | Callable | Generator, *args, **kwargs) -> Track:
        """Add a sequence or a generator to this track"""

        # if isinstance(sequence, str):
        #     sequence = parse(sequence)
        if callable(sequence) or isinstance(sequence, Generator):
            return self._addGen(sequence, *args, **kwargs)
        
        self.sequences.append(sequence)
        return self


    def _addGen(self, func: Generator | Callable, *args, **kwargs) -> Track:
        """
            Add a sequence generator to this track.
            A callable should be provided, not the generator itself.
            When a callable is provided, the generator can be resetted.
        """

        if isinstance(func, Generator):
            generator = func
        else:
            generator = func(*args, **kwargs)
        gen_id = id(generator)
        self.generators[gen_id] = {
            "func": func if callable(func) else None,
            "args": args, "kwargs": kwargs,
            "generator": generator,
            # "seqs": [],
            }
        self.sequences.append(gen_id)
        return self


    def delLast(self):
        if self.sequences:
            self.sequences = self.sequences[:-1]

    def delAdd(self, sequence: str | Seq | Callable | Generator, *args, **kwargs) -> "Track":
        if self.sequences:
            self.sequences.pop()
        return self.add(sequence)


    def clearAdd(self, sequence: str | Seq | Callable | Generator, *args, **kwargs) -> "Track":
        self.clear()
        return self.add(sequence, *args, **kwargs)

    def clear(self):
        self.sequences.clear()
        self.generators.clear()
        self._sequence_idx = 0
    

    def getParams(self, other: "Track"):
        self.port = other.port
        self.channel = other.channel
        self.instrument = other.instrument
    

    def start(self, loop: bool | None = None):
        self.reset()
        self.stopped = False
        if loop is not None:
            self.loop = loop
    
    def startSync(self, loop: bool | None = None):
        """Start this track synchronized with the currently playing tracks"""
        raise NotImplementedError


    def stop(self):
        self.stopped = True


    def reset(self):
        self._sequence_timer = self.offset
        self._sequence_idx = 0
    

    def mute(self):
        self.muted = True
    
    def unmute(self):
        self.muted = False


    def setGroup(self, track_group):
        self._sync_group = track_group
        for t in self._sync_children:
            t.setGroup(track_group)


    def syncFrom(self, other: "Track" | None) -> None:
        if self._sync_from != None:
            # Unsync first
            self._sync_from._sync_children.remove(self)
        self._sync_from = other
        if other != None:
            other._sync_children.append(self)
    
    def _sync(self) -> None:
        if self.stopped:
            self.start()
    

    def _get_priority_list(self) -> list["Track"]:
        pl = [self]
        for t in self._sync_children:
            pl.extend(t._get_priority_list())
        return pl


    def push(self, method: Callable, *args, **kwargs):
        """
        Add a transform operation to the pile (a method from Seq class).
        Sequences from the Track will go through the pile of modifiers.
        """
        self.transforms.append((method, args, kwargs))
    
    def pop(self):
        del self.transforms[-1]
    
    def popPush(self, method: Callable, *args, **kwargs):
        self.pop()
        self.push(method, *args, **kwargs)
    

    def clearTrans(self):
        self.transforms.clear()


    def _parse_seq(self, seq_string) -> Tuple[Seq, str]:
        """Parse a symbolic string sequence and return a Seq"""
        element, updated_string = parse(seq_string)
        if not isinstance(element, Seq):
            element = Seq(element)
        return element, updated_string
    

    def _get_next_sequence(self) -> Seq | None:
        """Gets the next sequence in track.
        Generates the sequence if the next element is a generator.
        Apply track modifiers to the sequence.
        """
        assert self._sequence_idx < len(self.sequences)
        
        sequence = self.sequences[self._sequence_idx]
        
        if isinstance(sequence, int):
            # It's a generator !
            gen_id = sequence
            gen_data = self.generators[gen_id]
            try:
                # Generator is still generating
                sequence = next(self.generators[gen_id]["generator"])
                # Add generated sequence to cache
            except StopIteration:
                if gen_data["func"]:
                    # Reload generator
                    args = gen_data["args"]
                    kwargs = gen_data["kwargs"]
                    new_gen = gen_data["func"](*args, **kwargs)
                    gen_data["generator"] = new_gen
                    sequence = next(new_gen)
                else:
                    # Skip
                    return None
                
        elif isinstance(sequence, str):
            # A symbolic string sequence
            sequence, updated_sequence = self._parse_seq(sequence)
            # Update string sequence state
            self.sequences[self._sequence_idx] = updated_sequence
        
        # Apply modifiers
        if self.transforms:
            sequence = sequence.copy()
            for mod, args, kwargs in self.transforms:
                try:
                    sequence = mod(sequence, *args, **kwargs)
                except TypeError:
                    pass

        return sequence.transposed(self.transpose)
    

    def _load_next_sequence(self):
        """Sets the track to the next sequence"""
        next_sequence = self._get_next_sequence()
        assert next_sequence is not None

        # Account for the offshot time from the previous sequence
        self._sequence_timer -= self._sequence_dur 

        self._sequence_dur = next_sequence.dur
        self._messages = next_sequence.getMidiMessages()
        self._message_idx = 0
        self._sequence_idx += 1


    def process(self, timedelta) -> list[tuple]:
        """
        Call this method continuously to send the notes to the output port.
        """
        # TODO: allow looping for finished generators

        if self.stopped:
            return

        if not self.sequences:
            self.stopped = True
            return
        
        self._sequence_timer += timedelta

        # End of current sequence, step to next sequence
        if self._sequence_timer >= self._sequence_dur:
            # Check if we arrived at the end of the track
            if self._sequence_idx >= len(self.sequences):
                # Should we loop the track ?
                if not self.loop:
                    self.stopped = True
                    return
                
                # Looping
                if self.loop_type == "all":
                    self._sequence_idx = 0
                elif self.loop_type == "last":
                    self._sequence_idx -= 1
                else:
                    raise Exception(f"'loop_type' property should be set to 'all' or 'last', but got '{self.loop_type}' instead")
            
            self._load_next_sequence()

            # Send a sync signal to linked tracks
            for t in self._sync_children:
                t._sync()

        # Process notes to play
        while self._message_idx < len(self._messages):
            onset_time, message = self._messages[self._message_idx]
            rel_time = onset_time - self._sequence_timer
            if rel_time <= 0.0:
                # Send the note to be played
                self.port.push(rel_time, message)
                self._message_idx += 1
            else:
                break


    def __getitem__(self, index):
        return self.sequences[index]
    

    def __len__(self):
        return len(self.sequences)
    

    def __repr__(self):
        if self._sync_from != None:
            return f"Track(channel={self.channel}, loop={self.loop}, name={self.name}, sync_from={self._sync_from.name})"
        return f"Track(channel={self.channel}, loop={self.loop}, name={self.name})"




class TrackGroup:
    """A group of synchronized Tracks"""

    def __init__(self):
        self.tracks = set()
        self.priority_list: List[Track] = [] # Must update in this order


    def add_track(self, track: Track):
        self.tracks.add(track)
        track.setGroup(self)
        for t in track._get_priority_list():
            self.tracks.add(t)
        self._update_priority_list()


    def stop_all(self):
        for t in self.tracks:
            t.stopped = True


    def all_stopped(self) -> bool:
        """ Returns True if all tracks are stopped"""
        return all([t.stopped for t in tracks])
    

    def clear_all(self) -> None:
        for t in self.tracks:
            t.clear()
            t.stopped = True
            t.loop = False


    def _update_priority_list(self) -> None:
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


tracks = TrackGroup()