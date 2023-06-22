# PyMidiSeq

Polyphonic real-time midi sequencer in Python.
With a strong emphasis on generative composition and live performances.
Clear and short syntax while trying to remain as little esoteric as possible.
Explicit docstrings and error messages.

## Setup

    pip install rtmidi

Pour un environnement de programmation toute options :

    sudo apt install jupyter-qtconsole

## Usage

### Basic usage

```python
>>> from miditool import *

>>> listOutputs()
[0] Midi Through:Midi Through Port-0 14:0
[1] VCV Rack:VCV Rack input 133:0

>>> openOutput(1)
Opening port 1 [VCV Rack:VCV Rack input 133:0]

>>> setTempo(60)
>>> play("c 5c c d g " * 4, loop=True)
>>> stop()
```

### Le temps

Pour changer la durée d'une séquence on modifie sa propriété `length`. On peut aussi la passer en argument au constructeur de la classe `Seq`.

```python
s = Seq(length=4)
# ou bien
s = Seq()
s.length = 4
```

L'unité temporelle est égale à une seconde.

### Notes, Silences and Sequences

Here's a note :

    Note("c")

You can sets its length with the `dur` parameter and add a silence/rest after it :

    Note("c", dur=2) + Sil(1.5)

Now, the duration of a note is not an absolute value. It's a relative value by which the default length is multiplied to give the note's true length (same for the silence).\
If the default length was set with `setNoteLen(1/4)` (default value), the previous sequence would play as a 'c' half note, followed by a dotted quarter rest.


### Chords

Chords can be created like so, using a capital letter. :

    Chord("Cmaj")

Same as `Chord([48, 52, 56])` or `Chord("do mi sol")`

Possible type of chords:
* Triads: "C" or "CM" (major), "Cm" (minor), "C+" (augmented), "C°" (diminished)
* Seventh: "C7" (dominant seventh), "CM7" (major seventh), "Cm7" (minor seventh), "C+7" (augmented seventh)
* Ninth: "C9" (dominant ninth), "CM9" (major ninth)

### String sequences

English notation (c d e f g a b) as well as solfège notation (do re mi fa sol la si) can be used to compose a sequence in a string.

```python
Seq("e b f# eb")
```

Sharp and flats are noted with the symbols `#` and `b` after the note name. Octave transposition is done by prepending the note name by a single number (absolute octave transposition) and with a +/- sign for relative transposition. The number can be omitted for a transposition of just 1 octave up or down.

```python
play("+e d -e +2b") # The play function will automatically convert a string to a Seq
```

Silences can be added in a string sequence with dots `.`. Many silences can be chained by concanetating the dots together.
Thus, `. . . .` is equivalent to `....`.

A note's duration can be subdivided by suffixing it with the `%`, symbol followed by a factor applied to the default duration of the note.

	"c#%.5" divides the note's duration by two
	"d%1/3" divides the note's duration by three

Tuplets

### Scales

You can constrain all generated notes in newly created sequences to a scale with the `setScale` function.

  setScale("minor", "c")

This won't affect previously created sequences.

### Generating sequences

Many built-in functions can be use to generate sequences.

#### Random generators

```python
rand(n)
```

```python
randWalk(n)
```

```python
randGauss(n)
```

#### Deterministic generators

```python
euclid(n)
```

The `lcm` function will build a sequence combining all given sequences with the "least common multiple" of their lengths.

Use quantized sequences, lest obtaining a memory shortage !

See : https://en.wikipedia.org/wiki/Least_common_multiple

```python
lcm("a ..", "c ...", "e ....")
```

### Tracks

Whenever you want to chain sequences or generators, or if you want to play sequences in parallel on different midi channels you can use tracks.

When importing `midiseq`, you will have 16 tracks defined by default, named `t1` to `t16` . Each one set to midi channels 0 to 15.

Tracks lets are set to a single midi channel and instrument :

```python
t1 = Track(channel=0, instrument=23, name="harmonica")

# You can later change channel or instrument
t1.channel = 1
t1.instrument = 59 # tuba
```

## IDE

* [iPython](https://ipython.org/)
* jupyter-qtconsole
* [ptpython](https://github.com/prompt-toolkit/ptpython/)

## Alsa connect

List midi inputs (devices that can recieve midi)

    $ aconnect -i

List midi outputs (devices that can send midi)
  
    $ aconnect -o

Connecting devices together (sender to reciever)

    $ aconnect 132:0 130:0

## Other software / inspiration

Sonic Pi
https://sonic-pi.net/

FoxDot
https://github.com/Qirky/FoxDot

Braid
https://braid.live/

MusicPy
https://github.com/Rainbow-Dreamer/musicpy

SCAMP
https://github.com/MarcTheSpark/scamp

JFugue
https://en.wikipedia.org/wiki/JFugue

pocketrockit
https://projects.om-office.de/frans/pocketrockit

### Hardware

Monome - Teletype (Eurorack module)
https://monome.org/docs/teletype/

## Développement futur / idées à explorer

* Micro-tonalité avec le pitch bend
* Pouvoir associer une fonction de callback à la réception d'un contrôle midi
* Listen() devrait n'avoir à s'appeler qu'une seule fois. Créer une fonction stop_listen().
* Possibilité de jouer des notes d'une séquence se trouvent au delà de la taille (param length) de la séquence.

### Méthodes de la classe Seq

* opérateur XOR (^) -> transpose la séquence de n demi-tons
* Autoriser les pitch négatifs (utile lorsqu'on utilise la transposition)
* map(other:Seq) # Nom à revoir, pas assez explicite
  Calque une mélodie sur un rythme
* monophy()
  supprime la polyphonie
* flatten() # Nom à revoir
  Supprime tous les silences et mets toutes les notes à la suite, sans chevauchement
* joinNotes()
    Inverse de splitNotes
    Combine les séries de mêmes notes consécutives sans silences
    Ralonge les notes suivies de silences pour recouvrir la totalité des silences de la séquence
* sort
  organise les notes temporelement par ordre de hauteur (sans cheuvauchement)
  Paramètre 'reverse'.
* spread
  Étale les notes qui se chevauchent, de façon à ce qu'il n'y ai pas 2 notes qui se jouent au même moment. Proposer un paramètre de façon à décider si les notes démarrant au même instant s'étalent en montant (de grave à aigüe) ou en descendant (aigüe à grave).
* générateur de la suite de Recaman
* Fonction de selection des notes d'après critères. Possibilité d'appliquer une transfo quelconque sur la séléction de notes (transpose, vel, dur)
