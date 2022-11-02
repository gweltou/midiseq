scales = {
    "chromatic":        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10],
    #"harmonic_minor":   [0, 2, 3, 5, 7, 8, 10],
    "whole_tone":       [0, 2, 4, 6, 8, 10],
    "pentatonic":       [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "japanese":         [0, 1, 5, 7, 8],
    "zelda_ocarnia":    [0, 3, 7, 9],
}

modes = {
    "ionian":       [0, 2, 4, 5, 7, 9, 11],
    "dorian":       [0, 2, 3, 5, 7, 9, 10],
    "phrygian":     [0, 1, 3, 5, 7, 8, 10],
    "lydian":       [0, 2, 4, 6, 7, 9, 11],
    "mixolidian":   [0, 2, 4, 5, 7, 9, 10],
    "aeolian":      [0, 2, 3, 5, 7, 8, 10],
    "locrian":      [0, 1, 3, 5, 6, 8, 10],
}


class Scale():

    def __init__(self, scale="major", tonic=60):
        if type(tonic) == int:
            self.tonic = min(127, max(0, tonic))
        elif type(tonic) == str:
            self.tonic = noteToPitch(tonic)
        else:
            raise TypeError("rootnote must be a pitch number [0-127] or a valid note name")

        if type(scale) == str:
            if scale in scales:
                self.scale = scales[scale]
            elif scale in modes:
                self.scale = modes[scale]
            else:
                raise TypeError('scale "{}" is unknown'.format(scale))
        elif type(scale) == list:
            self.scale = scale