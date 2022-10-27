def noteToPitch(note):
    """ Returns the midi pitch number giver a spelled note """
    notes = {'c': 0,    'do': 0,
             'c+': 1, 'c#': 1,
             'd': 2,    're': 2,
             'd+' : 3, 'd#' : 3,
             'e': 4,    'mi': 4,
             'f': 5,    'fa': 5,
             'f+': 6, 'f#': 6,
             'g': 7,    'sol': 7,
             'g+': 8, 'g#': 8,
             'a': 9,    'la': 8,
             'a+': 10, 'a#': 10,
             'b': 11,   'si': 11,
             }
    return 60 + notes[note]