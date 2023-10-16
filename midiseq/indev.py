from typing import Union, List, Generator

import rtmidi
from rtmidi.midiconstants import (
    NOTE_ON, NOTE_OFF,
    ALL_SOUND_OFF, RESET_ALL_CONTROLLERS,
    CONTROL_CHANGE, PROGRAM_CHANGE
)

from midiseq import *


class MidiDevice():

    def __init__(self, out_port: rtmidi.MidiOut, in_port: rtmidi.MidiOut):
        self.output = out_port
        self.inpout = in_port
    
    def panic(self):
        for channel in range(16):
            self.output.send_message([CONTROL_CHANGE | channel, ALL_SOUND_OFF, 0])
            self.output.send_message([CONTROL_CHANGE | channel, RESET_ALL_CONTROLLERS, 0])
            #time.sleep(0.05)
    
    def program_change(self, channel, value):
        msg = [PROGRAM_CHANGE | channel, value]
        self.output.send_message(msg)




def test_getActiveMask():
    s = pattern("-xxx-x-xxx-", 48)
    active_mask = getActiveMask(s)
    silence_mask = getNotActiveMask(s)
    assert len(active_mask) == 3
    assert len(silence_mask) == 4


def test_mask():
    s = pattern("xxxx----xxxx----", K)
    o = Note("+do")*16
    mask(o, s)
    assert len(o) == 8



test_mask()