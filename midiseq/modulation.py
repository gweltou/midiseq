from typing import Optional, Union, List, Tuple, Generator
from random import random

from rtmidi.midiconstants import (
    CONTROL_CHANGE, PROGRAM_CHANGE,
    PITCH_BEND, MODULATION_WHEEL,
    CHANNEL_AFTERTOUCH,
)

import midiseq.env as env


__all__ = ['Mod', 'ModSeq', 'modRnd']


def val2bytes(val: float) -> Tuple:
    """ Return (msb, lsb) values for a float between 0.0 and 1.0 """
    fourteenb = int(val * 16384)
    val = min(max(val, 0), 16383)
    msb = fourteenb >> 7
    lsb = fourteenb & 127
    return msb, lsb


modRnd = lambda x: random()


class Mod():

    def __init__(self,
                 fn: Union[callable, float, List, Tuple],
                 cycle: float=0.02,
                 interp=True
                ):
        """
            Create a modulation curve
            from a lambda function, a list of points or a Sequence

            Parameters
            ----------
                fn : float
                    An single held value
                fn : lambda function
                    ex: `lambda t : sin(2*t*pi)`
                fn : List[Tuple[float, float]]
                    List of normalized 2D coordinates
                    ex: `[(0.0, 0.25), (0.5, 0.1), (1.0, 0.8)]`
                fn : List[float]
                    1D values, evenly spaced
                    ex: `[0, 1, 0]`
                    values inbetween are interpolated
                interp : Boolean
                    If True, interpolate values for list of coordinates
        """

        self.cycle = cycle # Time resolution for the lambda function
        self.fn = None
        self.scalar = None
        self.coords = None
        self.interp = interp

        if callable(fn):
            self.fn = fn

        elif isinstance(fn, float):
            self.scalar = fn

        elif isinstance(fn, (list, tuple)):
            if isinstance(fn[0], (float, int)):
                # Add the t coordinate
                # t = [i * 1.0/(len(fn)-1) for i in range(len(fn))]
                # self.coords = zip(t, fn)
                self.coords = [ (i/(len(fn)-1), val) for i, val in enumerate(fn) ]
        
            elif isinstance(fn[0], (list, tuple)):
                self.coords = fn


    def getValues(self, start=0.0, dur=1.0, fn_start=0.0, fn_end=1.0):
        """
            Calculate values of mod function in given range
        """
        # We could store the last X states for caching

        # Check if requested state has been seen in last X states
        assert fn_start < fn_end, f"{fn_start=} {fn_end=}"

        if self.scalar:
            return [(start, self.scalar)]

        if self.coords:
            assert fn_start >= self.coords[0][0]

            if self.interp:
                assert fn_end <= self.coords[-1][0]

                values = []
                num_samples = dur / self.cycle
                step = (fn_end-fn_start) / num_samples
                pos = fn_start
                t = start
                p_idx = 0
                while pos <= fn_end + 0.0001:
                    while pos > self.coords[p_idx+1][0]:
                        p_idx += 1
                        if p_idx + 1 >= len(self.coords):
                            # Out of bounds
                            values.append( (start + dur, self.coords[-1][1]) )
                            return values
                    t_frac = (pos-self.coords[p_idx][0]) / (self.coords[p_idx+1][0]-self.coords[p_idx][0])
                    val = self.coords[p_idx][1] + t_frac * (self.coords[p_idx+1][1]-self.coords[p_idx][1])
                    values.append( (t, val) )
                    pos += step
                    t += self.cycle

                return values
            else:
                values = []
                p_idx = 0
                # pos = fn_start
                while fn_start > self.coords[p_idx+1][0]:
                    # Find left value
                    p_idx += 1
                    if p_idx + 1 >= len(self.coords):
                        return values
                # pos = fn_start
                t_factor = dur / (fn_end-fn_start)
                while p_idx < len(self.coords) and self.coords[p_idx][0] < fn_end + 0.0001:
                    pos = max(fn_start, self.coords[p_idx][0])
                    t = start + (pos-fn_start) * t_factor
                    values.append( (t, self.coords[p_idx][1]) )
                    p_idx += 1
                
                return values
        
        if self.fn != None:
            values = []
            num_samples = dur / self.cycle
            step = (fn_end-fn_start) / num_samples
            pos = fn_start
            t = start
            while pos <= fn_end + 0.0001:
                values.append( (t, self.fn(pos)) )
                pos += step
                t += self.cycle
            
            return values
    
    
    # def plot(self, start=0.0, end=1.0):
    #     pass




class ModSeq():
    """ Modulation sequence """

    def __init__(self, dur=0):
        self.dur = dur
        self.modulators = []
        self.values = []


    def add(self,
            mod: Mod,
            controler: int,
            start=0.0,
            dur:Optional[float]=None,
            fn_start=0.0,
            fn_end=1.0
            ):
        """
            Add a time function

            Parameters
            ----------
                mod : Mod
                    Modulator
                controler : int
                    MIDI controler number
                start : float
                    Start time of modulation
                dur : float
                    Duration of modulation
                fn_start : float
                    Start sample value in function
                fn_end : float
                    End sample value in function
        """
        if dur == None:
            dur = self.dur

        # TODO
        # If a modulator set to the same controler is already present,
        # Overwrite the previous modulator's range
        self.modulators.append( (mod, controler, start, dur, fn_end, fn_end) )
        self.values.append( mod.getValues(start, dur, fn_start, fn_end) )

        return self
    

    def getMidiMessages(self, channel=0):
        messages = []
        for i in range(len(self.modulators)):
            # mod = self.modulators[i][0]
            controler = self.modulators[i][1]
            values = self.values[i]
            # Only MSB is used for now
            if controler <= 0x7F:
                messages.extend( [ (pos,
                                        [CONTROL_CHANGE|channel,
                                        controler,
                                        min(127, val2bytes(val)[0])]
                                    )
                                   for pos, val in values ] )
            elif controler == CHANNEL_AFTERTOUCH: # Status 0xD0
                messages.extend( [ (pos,
                                        [CHANNEL_AFTERTOUCH|channel,
                                        val2bytes(val)[0],
                                        0]
                                    )
                                    for pos, val in values ] )
            elif controler == PITCH_BEND: # Status 0xE0
                messages.extend( [ (pos,
                                        [PITCH_BEND|channel,
                                        0,
                                        min(127, val2bytes(val)[0])]
                                    )
                                    for pos, val in values ] )
        return messages