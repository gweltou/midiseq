# !/usr/bin/env python3

tracks = []
default_track = None
is_playing = False

bpm = 120
note_dur = 1/8
scale = None
default_octave = 4

METRONOME = False
METRONOME_NOTES = (75, 85) # Midi click notes
METRONOME_DIV = 4          # Number of quarter notes in a metronome cycle
METRONOME_PRE = 1          # Number of metronome cycle before recording
METRONOME_DUR = 0.1        # Duration of a click note
METRONOME_PORT = None      # Midi port for metronome
METRONOME_CHAN = 9         # Midi channel for metronome

default_output = None
default_input = None
DISPLAY = False
DISPLAY_RANGE = (36, 96)
verbose = False
default_channel = 0
