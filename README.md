# MidiTool


## Alsa connect

List midi inputs (devices that can recieve midi)

  $ aconnect -i

List midi outputs (devices that can send midi)
  
  $ aconnect -o

Connecting devices together (sender to reciever)

  $ aconnect 132:0 130:0


## Développement futur / idées à explorer

* Micro-tonalité avec le pitch bend

### Méthodes de la classe Seq

* shift(n)
  décallage des notes
* joinNotes()
    Inverse de splitNotes
    Combine les séries de mêmes notes consécutives sans silences
    Ralonge les notes suivies de silences pour recouvrir la totalité des silences de la séquence
* Sort
  organise les notes temporelement par ordre de hauteur (sans cheuvauchement)
* spread
  étale les notes qui se chevauchent de façon à ce qu'il n'y ai pas 2 notes qui se jouent au même moment.
* générateur de la suite de Recaman

### Classe Grid

* beatEvery(pitch, division, offset)
  """
      Parameters
      ----------
          pitch (int)
            midi note [0-127]
          division (int)
            the note will be repeated every division of the grid
          offset (int)
            offset beats in grid
  """

* subdivide(n)
  """ Subdivide grid by multiplying number of cells by n """