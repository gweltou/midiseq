# !/usr/bin/env python3

TRACKS = []

TEMPO = 120
NOTE_LENGTH = 1/4
SCALE = None
DEFAULT_OCTAVE = 4

METRONOME_NOTES = (75, 85) # Midi click notes
METRONOME_CLICK = True
METRONOME_DIV = 4          # Number of quarter notes in a metronome cycle
METRONOME_PRE = 1          # Number of metronome cycle before recording
METRONOME_PORT = None      # Midi port for metronome

DEFAULT_OUTPUT = None
DISPLAY = True
DISPLAY_RANGE = (36, 96)
VERBOSE = False