# MidiSeq

Polyphonic real-time midi sequencer with Python.
With a strong emphasis on generative composition and live performances.
Clear and short syntax while trying to remain as little esoteric as possible.
Explicit docstrings and error messages.

**Work in progress**

## Setup

    pip install rtmidi

## Usage

### Basic usage

```python
>>> from miditool import *

>>> listOutputs()
[0] Midi Through:Midi Through Port-0 14:0
[1] VCV Rack:VCV Rack input 133:0

>>> openOutput(1)
Opening port 1 [VCV Rack:VCV Rack input 133:0]

>>> setBpm(60)
>>> play("c 5c c d g", loop=True)
>>> stop()
```

### Notes, Silences and Sequences

Here's how you create a note :

```python
Note("c")
```

You can sets its length with the `dur` parameter and add a silence/rest after it :

```python
Note("c", dur=2) + Sil(1.5)
```

Now, the duration of a note is not an absolute value. It's a relative value by which the default length is multiplied to give the note's true length (same for the silence).\
If the default length was set with `setNoteDur(1/4)` (default value), the previous sequence would play as a 'c' half note, followed by a dotted quarter rest.

Sequences are automatically created when you add Notes, Silences or Chords together.

```python
s = Note("c") + Note("e") + Note("g")
s = 2*s + Sil() + 2*s
```

#### Notes with probabilites

Notes can have a trigger probability with the optional `prob` parameter. This parameter can be set at initialisation or later, through the Note's `prob` attribute.

```python
n = Note("c", prob=0.5)
# Same as
n = Note("c")
n.prob = 0.5
```

#### PNotes, a.k.a. Schrödinger's notes

PNotes are a special kind of notes that can randomly resolve to different pitches. You can create them by providing a dictionary, mapping pitches to probability weights, or by providing a list, tuple or a set (each pitch will have an equal probability in this case).

```python
n = PNote({"c": 1, "e": 2})
play(n)
# When playing 'n', playing  a'E' will be twice more likely than playing a 'C' 
```

### Chords

Chords can be created like so, using a capital letter.

```python
Chord("C")
```

Same as `Chord([48, 52, 55])` or `Chord("do mi sol")`

Possible type of chords:

* Triads: "C" or "CM" (major), "Cm" (minor), "C+" (augmented), "C°" (diminished)
* Seventh: "C7" (dominant seventh), "CM7" (major seventh), "Cm7" (minor seventh), "C+7" (augmented seventh)
* Ninth: "C9" (dominant ninth), "CM9" (major ninth)

### String sequences

English notation (c d e f g a b) as well as solfège notation (do re mi fa sol la si) can be used to compose a sequence in a string.

```python
Seq("e b f# e b")
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

#### Tuplets

### Scales

You can constrain all generated notes in newly created sequences to a scale with the `setScale` function.

```python
setScl("minor", "c")
```

This won't affect previously created sequences.

### Sequence modifiers

Method  | Parameters | Description
------- | ---------- | -----------
clear   |            | Clears the sequence
add     | Note, Chord, Sil, other Seq... | Add an element to the sequence
merge   | Other Seq  | Mix the two sequences together
stretch | float     | Stretch or compress the duration of the sequence
reverse |           | Reverse the order of the notes
transpose | int     | Transose the whole sequence by semitones
expandPitch | float | Raise or lower pitches around a mean value
splitNotes | int    | Split all notes (or a single note)
decimate | prob: float    | Remove notes randomly with a given probability
attenuate |         |
humanize |          | Randomize sligthly notes time, duration and velocity
crop    |           | Crop notes (or parts of notes) before and after the sequence duration
strip   |           | Remove silences from both ends of the sequence. Change the sequence duration accordingly
stripHead |         | Remove silences in front of the sequence
stripTail |         | Remove silences at the end of the sequence
shift   | float     | Shift onset of all notes in sequence
mapRhythm | other Seq | Map the rhythm of another sequence to this sequence
mask |  | Keep notes from this sequences only when given sequence has active notes
maskNot | | Keep notes from this sequences only when given sequence is silent

### Generating sequences

Many built-in functions can be use to generate sequences.

#### Random generators

```python
rnd(n)
```

```python
rndWalk(n)
```

```python
rndGauss(n)
```

#### Deterministic generators

```python
euclid(note, n, grid, offset)
```

The `lcm` function will build a sequence combining all given sequences with the "least common multiple" of their lengths.

Use quantized sequences, lest obtaining a memory shortage !

See : https://en.wikipedia.org/wiki/Least_common_multiple

```python
lcm("a ..", "c ...", "e ....")
```

#### Evolving generators

Python generators can be used as sequences factories. Some useful ones are provided with the library.

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

Use the `add` method to add sequences to tracks.

```python
t1.add(rnd(8))
```

### Whistle and Tap

## Recommended IDEs

For a better experience, a full featured interactive shell is recommended.

* [iPython](https://ipython.org/)
* jupyter-qtconsole

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
https://foxdot.org/
https://github.com/Qirky/FoxDot

Sardine
https://github.com/Bubobubobubobubo/sardine

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
