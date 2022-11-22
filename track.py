

class Track():
    """ Track where you can add Sequence.
        You can had a silence by adding an empty Sequence with a length.
        You can define a generator callback function by modifing the generator property.
    """

    def __init__(self, channel=1):
        self.midiport = None
        self.channel = channel
        self.instrument = None
        self.gen_func =  None
        self.gen_args = None
        self.generator = None
        self.seqs = []
        self.loop = False
        self.reset()
    

    def add(self, sequence):
        self.seqs.append(sequence)
        self.ended = False
    

    def clear(self):
        self.seqs.clear()
        self.seq_i = 0
        self.ended = True
        self.gen_func = None
        self.generator = None
        self.gen_args = None
    

    def update(self, timedelta):
        """ Returns MidiMessages when a new sequence just started """
        #TODO: write a function "next" or something instead

        if self.ended:
            return
        self._next_timer -= timedelta

        if self.seq_i < len(self.seqs) and self._next_timer <= 0.0:
            # Send next sequence
            i = self.seq_i
            self.seq_i += 1
            self._next_timer = self.seqs[i].length
            return self.seqs[i].getMidiMessages(self.channel)

        elif self.seq_i == len(self.seqs) and self._next_timer <= 0.0:
            #TODO: allow looping for finished generators
            if self.generator:
                try:
                    new_seq = next(self.generator)
                    self._next_timer = new_seq.length
                    return new_seq.getMidiMessages(self.channel)
                except StopIteration:
                    if self.loop:
                        self.reset()
                    else:
                        self.ended = True
            elif self.loop:
                self.reset()
            else:
                self.ended = True
            

    def reset(self):
        self._next_timer = 0.0
        self.seq_i = 0
        self.ended = False
        if callable(self.gen_func):
            if self.gen_args:
                self.generator = self.gen_func(*self.gen_args)
            else:
                self.generator = self.gen_func()



class Song():

    def __init__(self):
        self.tempo = 120
        self.time_signature = (4, 4)
        self.tracks = []