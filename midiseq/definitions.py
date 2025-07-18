scales = {
    "chromatic":        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10], 
    "harmonic_minor":   [0, 2, 3, 5, 7, 8, 11], "hminor": [0, 2, 3, 5, 7, 8, 11],
    # what about the melodic minor (ascending and descending) ?
    "whole_tone":       [0, 2, 4, 6, 8, 10], "whole": [0, 2, 4, 6, 8, 10],
    "pentatonic":       [0, 2, 4, 7, 9], "penta": [0, 2, 4, 7, 9], "majorpenta": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10], "minorpenta": [0, 3, 5, 7, 10],

    "japanese":         [0, 1, 5, 7, 8], "in": [0, 1, 5, 7, 8],
    "hirajoshi":        [0, 4, 6, 7, 11],
    "insen":            [0, 1, 5, 7, 10],
    "iwato":            [0, 1, 5, 6, 10],
    "zelda_ocarina":    [0, 3, 7, 9],

    "vminor": [0, 2, 3, 5, 7, 8, 10],
    "acoustic": [0, 2, 4, 6, 7, 9, 10],
    "algerian": [0, 2, 3, 6, 7, 9, 11, 12, 14, 15, 17],
    "superlocrian": [0, 1, 3, 4, 6, 8, 10],
    "augmented": [0, 3, 4, 7, 8, 11],
    "bebop": [0, 2, 4, 5, 7, 9, 10, 11],
    "blues": [0, 3, 5, 6, 7, 10],
    "doubleharmonic": [0, 1, 4, 5, 8, 11],
    "enigmatic": [0, 1, 4, 6, 8, 10, 11],
    "flamenco": [0, 1, 4, 5, 7, 8, 11],
    "freygish": [0, 1, 4, 5, 7, 8, 10], # Phrygian dominant scale
    "gypsy": [0, 2, 3, 6, 7, 8, 10],
    "halfdim": [0, 2, 3, 5, 6, 8, 10],
    "harmmajor": [0, 2, 4, 5, 7, 8, 11],
    "harmminor": [0, 2, 3, 5, 7, 8, 11],
    "hungarianminor": [0, 2, 3, 6, 7, 8, 11],
    "hungarianmajor": [0, 3, 4, 6, 7, 9, 10],
    "istrian": [0, 1, 3, 4, 6, 7],
    "lydianaug": [0, 2, 4, 6, 8, 9, 11],
    "majorlocrian": [0, 2, 4, 5, 6, 8, 10],
    "melominup": [0, 2, 3, 5, 7, 9, 11],
    "melomindown": [0, 2, 3, 5, 7, 8, 10],
    "neapolitan": [0, 1, 3, 5, 7, 8, 11],
    "octatonic": [0, 2, 3, 5, 6, 8, 9, 11],
    "octatonic2": [0, 1, 3, 4, 6, 7, 9, 10],
    "persian": [0, 1, 4, 5, 6, 8, 11],
    "prometheus": [0, 2, 4, 6, 9, 10],
    "harmonics": [0, 3, 4, 5, 7, 9],
    "tritone": [0, 1, 4, 6, 7, 10],
    "ukrainian": [0, 2, 3, 6, 7, 9, 10],
    "yo": [0, 3, 5, 7, 10],
    "symetrical": [0, 1, 2, 6, 7, 10],
    "symetrical2": [0, 2, 3, 6, 8, 10],
    "messiaen1": [0, 2, 4, 6, 8, 10],
    "messiaen2": [0, 1, 3, 4, 6, 7, 9, 10],
    "messiaen3": [0, 2, 3, 4, 6, 7, 8, 10, 11],
    "messiaen4": [0, 1, 2, 4, 6, 7, 8, 11],
    "messiaen5": [0, 1, 5, 6, 7, 11],
    "messiaen6": [0, 2, 4, 5, 6, 8],
    "messiaen7": [0, 1, 2, 3, 5, 6, 7, 8, 9, 11],
}

modes = {
    "ionian":       [0, 2, 4, 5, 7, 9, 11],
    "dorian":       [0, 2, 3, 5, 7, 9, 10],
    "phrygian":     [0, 1, 3, 5, 7, 8, 10],
    "lydian":       [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":   [0, 2, 4, 5, 7, 9, 10],
    "aeolian":      [0, 2, 3, 5, 7, 8, 10],
    "locrian":      [0, 1, 3, 5, 6, 8, 10],
}


# General Midi 1 instrument mapping
gm_piano1 = 0
gm_piano2 = 1
gm_piano3 = 2
gm_piano_honkytonk = 3
gm_piano_electric1 = 4
gm_piano_electric2 = 5
gm_harpsichord = 6
gm_clavinet = 7
gm_celesta = 8
gm_glockenspiel = 9
gm_musicbox = 10
gm_vibraphone = 11
gm_marimba = 12
gm_xylophone = 13
gm_tubular_bells = 14
gm_dulcimer = 15
gm_organ_drawbar = 16
gm_organ_percussive = 17
gm_organ_rock = 18
gm_organ_church = 19
gm_organ_reed = 20
gm_accordion = 21
gm_harmonica = 22
gm_bandoneon = 23
gm_guitar_nylon = 24
gm_guitar_steel = 25
gm_guitar_electric_jazz = 26
gm_guitar_electric_clean = 27
gm_guitar_electric_muted = 28
gm_guitar_electric_od = 29
gm_guitar_electric_disto = 30
gm_guitar_electric_harm = 31
gm_bass_acoustic = 32
gm_bass_electric_finger = 33
gm_bass_electric_picked = 34
gm_bass_electric_fretless = 35

gm_tuba = 58

# Synth Leads
gm_synth_lead1 = 80
gm_synth_lead2 = 81
gm_synth_lead3 = 82
gm_synth_lead4 = 83
gm_synth_lead5 = 84
gm_synth_lead6 = 85
gm_synth_lead7 = 86
gm_synth_lead8 = 87
# Synth Pads
gm_synth_pad1 = 88
gm_synth_pad2 = 89
gm_synth_pad3 = 90
gm_synth_pad4 = 91
gm_synth_pad5 = 92
gm_synth_pad6 = 93
gm_synth_pad7 = 94
gm_synth_pad8 = 95

gm_bass_drum_acoustic = 35
gm_bass_drum_electric = 36
gm_side_stick = 37
gm_snare_acoustic = 38
gm_hand_clap = 39
gm_snare_electric = 40
gm_tom_low_floor = 41
gm_hh_closed = 42
gm_tom_high_floor = 43
gm_hh_pedal = 44
gm_tom_low = 45
gm_hh_open = 46
gm_tom_low_mid = 47
gm_tom_hi_mid = 48
gm_cymbal_crash_1 = 49
gm_tom_high = 50
gm_cymbal_ride_1 = 51
gm_cymbal_chinese = 52
gm_bell_ride = 53
gm_tambourine = 54
gm_cymbal_splash = 55
gm_cowbell = 56
gm_cymbal_crash_2 = 57
gm_vibraslap = 58
gm_cymbal_ride_2 = 59
gm_bongo_hi = 60
gm_bongo_low = 61
gm_conga_hi_mute = 62
gm_conga_hi_open = 63
gm_conga_low = 64
gm_timbale_high = 65
gm_timbale_low = 66
gm_agogo_high = 67
gm_agogo_low = 68
gm_cabasa = 69
gm_maracas = 70
gm_whistle_short = 71
gm_whistle_long = 72
gm_guiro_short = 73
gm_guiro_long = 74
gm_claves = 75
gm_wood_block_hi = 76
gm_wood_block_low = 77
gm_cuica_mute = 78
gm_cuica_open = 79
gm_triangle_mute = 80
gm_triangle_open = 81


# For Roland TR-6S
BD = 36
SD = 38
LT = 43
HC = 39
CH = 42
OH = 46