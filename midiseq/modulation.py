from typing import Optional, Union, List, Tuple, Generator

from rtmidi.midiconstants import (
    CONTROL_CHANGE, PROGRAM_CHANGE,
    PITCH_BEND, MODULATION_WHEEL,
    POLY_AFTERTOUCH, CHANNEL_AFTERTOUCH,
)

import midiseq.env as env



def val2bytes(val: float) -> Tuple:
    """ Return (msb, lsb) values for a float between 0.0 and 1.0 """
    fourteenb = int(val * 16384)
    val = min(max(val, 0), 16383)
    msb = fourteenb >> 7
    lsb = fourteenb & 127
    return msb, lsb



class Mod():

    def __init__(self,
                 fn: Union[callable, float],
                 cycle: float=0.02,
                 interp=True
                ):
        """ Create a modulation curve
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
        self.fn = None
        self.cycle = cycle # Time resolution for the lambda function
        self.scalar = None
        self.coords = None

        if callable(fn):
            self.fn = fn

        elif isinstance(fn, float):
            self.scalar = fn

        elif isinstance(fn, list):
            if isinstance(fn[0], float):
                # Add the t coordinate
                t = [i * 1.0/len(fn) for i in range(len(fn))]
                self.coords = zip(t, fn)
                print(self.coords)
        
            elif isinstance(fn[0], tuple):
                self.coords = fn


    def getValues(self, start=0.0, dur=1.0, stretch=1.0):
        # We could store the last X states for caching

        # Check if requested state has been seen in last X states
        if self.scalar != None:
            return [self.scalar]

        if self.coords != None:
            if self.interp:
                print("interp")
                return
            else:
                if self.interp:
                    print("interp")
                    return
                else:
                    return [(self.stretch * t, v) for t, v in self.coords]
        
        if self.fn != None:
            values = []
            offset = 0.0
            while offset < dur*stretch - 0.000001: # Avoid rounding errors
                values.append( (start+offset, self.fn(start+(offset/stretch))) )
                offset += self.cycle * stretch

            return values
    
    
    def plot(self, start=0.0, end=1.0):
        pass




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
            stretch=False):
        """ Add a time function

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
                autostretch : boolean
                    If True, the modulation will stretch to the requested duration
                    If False, the modulation will keep an absolute timing
        """
        if dur == None:
            dur = self.dur

        # TODO
        # If a modulator set to the same controler is already present,
        # Overwrite the previous modulator's range
        self.modulators.append( (mod, controler, start, dur) )
        self.values.append( mod.getValues(start, dur, stretch=dur if stretch else 1.0) )

        return self
    

    def getMidiMessages(self, channel=0):
        messages = []
        for i in range(len(self.modulators)):
            mod = self.modulators[i][0]
            controler = self.modulators[i][1]
            values = self.values[i]
            # Only MSB is used for now
            if controler <= 0x7F:
                messages.extend( [ (pos,
                                        [CONTROL_CHANGE|channel,
                                        controler,
                                        val2bytes(val)[0]]
                                    )
                                   for pos, val in values ] )
            elif controler == PITCH_BEND: # Status 0xE0
                messages.extend( [ (pos,
                                        [PITCH_BEND|channel,
                                        0,
                                        val2bytes(val)[0]]
                                    )
                                    for pos, val in values ] )
            elif controler == CHANNEL_AFTERTOUCH: # Status 0xD0
                messages.extend( [ (pos,
                                        [CHANNEL_AFTERTOUCH|channel,
                                        val2bytes(val)[0],
                                        0]
                                    )
                                    for pos, val in values ] )
            # elif controler == POLY_AFTERTOUCH:
            #     note = self.modulators[i][4]
            #     messages.extend( [ (pos,
            #                             [POLY_AFTERTOUCH|channel,
            #                             note,
            #                             val2bytes(val)[0]]
            #                         )
            #                         for pos, val in values ] )
        return messages