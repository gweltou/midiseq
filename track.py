


class Track():
    """ Track where you can add Sequence.
        You can had a silence by adding an empty Sequence with a length.
        You can define a generator callback function by modifing the generator property.
    """

    def __init__(self, channel=1):
        self.generator = None
        self.channel = channel
        self.seqs = []
        self.seq_i = 0
        self._next_timer = 0.0
    

    def add(self, sequence):
        self.seqs.append(sequence)
        self.ended = False
    

    def update(self, timedelta):
        """ Returns MidiMessages when a new sequence just started """
        if self.ended or len(self.seqs) == 0:
            return
        
        self._next_timer -= timedelta

        if self.seq_i < len(self.seqs) and self._next_timer <= 0.0:
            i = self.seq_i
            self.seq_i += 1
            self._next_timer = self.seqs[i].length
            return self.seqs[i].getMidiMessages(self.channel)
        elif self.seq_i == len(self.seqs) and self._next_timer <= 0.0:
            self.ended = True

    

    def init(self):
        self._next_timer = 0.0
        self.seq_i = 0
        self.ended = False