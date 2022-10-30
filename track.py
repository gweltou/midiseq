


class Track():
    """ Track where you can add Sequence.
        You can had a silence by adding an empty Sequence with a length.
        You can define a generator callback function by modifing the generator property.
    """

    def __init__(self, channel=1):
        self.generator =  None
        self._generator = None
        self.gen_args = None
        self.channel = channel
        self.seqs = []
        self.seq_i = 0
        self._next_timer = 0.0
        self.ended = False
    

    def add(self, sequence):
        self.seqs.append(sequence)
        self.ended = False
    

    def clear(self):
        self.seqs.clear()
        self.seq_i = 0
        self.ended = True
        self.generator = None
        self._generator = None
        self.gen_args = None
    

    def update(self, timedelta):
        """ Returns MidiMessages when a new sequence just started """
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
            if self._generator:
                try:
                    new_seq = next(self._generator)
                    self._next_timer = new_seq.length
                    return new_seq.getMidiMessages(self.channel)
                except:
                    self.ended = True
            else:
                self.ended = True
            


    def init(self):
        self._next_timer = 0.0
        self.seq_i = 0
        self.ended = False
        if callable(self.generator):
            if self.gen_args:
                self._generator = self.generator(*self.gen_args)
            else:
                self._generator = self.generator()