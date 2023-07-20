# !/usr/bin/env python3

tracks = None

bpm = 120
note_dur = 1/8
scale = None
default_octave = 4

METRONOME_NOTES = (75, 85) # Midi click notes
METRONOME_CLICK = True
METRONOME_DIV = 4          # Number of quarter notes in a metronome cycle
METRONOME_PRE = 1          # Number of metronome cycle before recording
METRONOME_PORT = None      # Midi port for metronome

default_output = None
DISPLAY = False
DISPLAY_RANGE = (36, 96)
VERBOSE = False