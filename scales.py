import re
# from sequence import Note, Seq


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


# def buildScale(scale, tonic):
#     s = Seq()
#     s.scale = Scale(scale, tonic)
#     for i in range(len(s.scale) + 1):
#         s.addNote(s.scale.getDegree(i))
#     return s


def noteToPitch(name):
    """ Returns the midi pitch number giver a spelled note """
    if type(name) != str: raise TypeError('Argument must be a string. Ex: "do", "c#4", "60... ')

    notes = {'c': 0,    'do': 0,
             'c+': 1,   'c#': 1,    'do#': 1,
             'd': 2,    're': 2,
             'd+' : 3,  'd#' : 3,   're#': 3,
             'e': 4,    'mi': 4,
             'f': 5,    'fa': 5,
             'f+': 6,   'f#': 6,    'fa#': 6,
             'g': 7,    'sol': 7,
             'g+': 8,   'g#': 8,    'sol#': 8,
             'a': 9,    'la': 9,
             'a+': 10,  'a#': 10,   'la#': 10,
             'b': 11,   'si': 11,
             }
    p = re.compile(r'([a-z]+[#\-+]?)(\d?)' ,re.IGNORECASE)

    name = name.strip()
    if name.isdecimal():
        return int(name)
    
    m = p.match(name)
    if m:
        tone = m.groups()[0]
        if m.groups()[1] != '':
            oct = int(m.groups()[1])
            return 12*oct + notes[tone]
        else:
            return 12*5 + notes[tone] # Defaults to fifth octave ?
    
    return -1



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
        
    
    def getClosest(self, note):
        """ Find closest note in scale given a pitch.
            Returns a corrected pitch, in range [0-127].
            Lower pitch takes precedence.
        """
        if type(note) == int:
            pitch = min(127, max(0, note))
        elif type(note) == str:
            pitch = noteToPitch(note)
        else:
            raise TypeError("Argument must be a pitch number [0-127] or a valid note name")

        octave, degree = divmod(pitch, 12)
        distances = [s-(degree-self.tonic)%12 for s in self.scale]
        min_dist = 12
        for d in distances:
            if abs(d) < abs(min_dist):
                min_dist = d
        
        return int(12 * octave + degree + min_dist)


    def getDegree(self, n):
        """ get the pitch of the n-th degree note in the current musical scale, relative to the rootnote
        """
        
        nth_oct, nth_degree = divmod(round(n), len(self.scale))

        if n >= 0:
            distances = self.scale
        else:  # Negative number
            distances = [ d-12 for d in self.scale]
            nth_oct += 1

        return self.tonic + 12 * nth_oct + distances[nth_degree]


    def getDegree2(self, pitch, n):
        """ Returns pitch +/- n degrees in the current scale """
        oct, semi = divmod(pitch, 12)
        for i, s in enumerate(self.scale):
            if s >= semi: break
        oct_off, deg = divmod(round(n) + i, len(self.scale))
        return (oct+oct_off)*12 + self.scale[deg]
    

    def triad(self, degree=0):
        """ Returns the notes in the nth degree triad """
        notes = []
        for chord_deg in [0, 2, 4]:
            notes.append( self.getDegree(degree+chord_deg) )

        return notes


    def __str__(self):
        return "{} {}".format(self.scale, self.tonic)


    def __len__(self):
        return len(self.scale)