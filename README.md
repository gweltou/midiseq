# MidiSeq

Polyphonic real-time midi sequencer with Python.
Emphasizing on generative composition and live performances.
Clear and short syntax while trying to remain as little esoteric as possible.
Explicit docstrings and error messages.

**Work in progress**

## Setup

    pip install -r requirements
    
The PortAudio library must be installed for `sounddevice` to load.

    sudo apt-get install libportaudio2

## Basic usage

```python
>>> from miditool import *

>>> listOutputs()
[0] Midi Through:Midi Through Port-0 14:0
[1] VCV Rack:VCV Rack input 133:0

>>> openOutput(1)
Opening port 1 [VCV Rack:VCV Rack input 133:0]

>>> setBpm(60)
>>> play("c 5c c d g_g", loop=True)
>>> stop()

>>> setScale("minor", "d")
>>> play1("i i .. i . i v")
>>> play2("i .. i +i ..")
>>> stop1()
>>> stop2()
```

## Documentation

### Scales

```python
setScl("minor", "c")
```

### Symbolic string sequences

The most straightforward way to write a sequence.

English notation (c d e f g a b) as well as solfège notation (do re mi fa sol la si) can be used to compose a sequence in a string.

```python
>>> s = Seq("e b f# e +b")
>>> play(s)
>>> print(s)
Seq((0.0, Note(52)), (0.125, Note(59)), (0.25, Note(54)), (0.375, Note(52)), (0.5, Note(71)), dur=0.625)
```

Sharp and flats are noted with the symbols `#` and `b` after the note name. Octave transposition is done by prepending the note name by a single number (absolute octave transposition) and with a `+`/`-` sign for relative transposition. The number can be omitted for a transposition of just 1 octave up or down.

```python
play("+e d -e +2b") # The play function will automatically convert a string to a Seq
```

Silences can be added in a string sequence with dots `.`.
You can coalesce dots together as well : `....`.

A note's duration can be subdivided by suffixing it with the `%`, symbol followed by a factor applied to the default duration of the note.

	"c#%.5" divides the note's duration by two
	"d%1/3" divides the note's duration by three

#### Symbolic strings functions

#### Default function

By default, elements are played one after the other. The default group is implicitely defined.

`e c e g -g` is equal to `(e c e g -g)`

You also explicitely define a default group by surrounding the group with parentesis. This can help to apply a modifier to a whole sequence of notes.

```
(e c e g -g)^-12 # The sequence will be played one octave down
```

##### Tuplet function

```
do_re_mi
```

##### Sync function

Play all elements at the same time.

```
[do mi sol]
```

##### Sequencial function

Return the next element on the list, loop at the end.

```
<mi sol +sol>
```

An iteration number can be provided by prepending the group with `#n` :

```
<mi sol +sol>#2 # Will play 'sol'
```

#### Schroedinger function

Return a randomly picked element, with optional probabilities.

```
{do re mi}
```

```
{do:2 re:1 mi:1} # 'do' is twice as likely to be played than 're' or 'mi'
```

### Element objects sequences

The pythonic OOP way.

#### Notes, Silences and Sequences

A single note :

```python
Note("c") or Note(48)
```

You can sets its length with the `dur` parameter and add a silence/rest after it :

```python
Note("c", dur=2) + Sil(1.5)
```

Sequences are automatically created when you add Notes, Silences or Chords together.

```python
>>> s = Note("c") + Note("e") + Note("g")
>>> s = 2*s + Sil() + 2*s
>>> print(type(s))
<class 'midiseq.elements.Seq'>
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

*Experimental*

PNotes are a special kind of notes that can randomly resolve to different pitches. You can create them by providing a dictionary, mapping pitches to probability weights, or by providing a list, tuple or a set (each pitch will have an equal probability in that case).

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
attenuate | factor=1.0 | Attenuate notes velocity by a given factor
humanize | tfactor=0.01, veldev=5 | Randomize sligthly notes time, duration and velocity
octaveShift | prob_up=0.1, prob_down=0.1 | Transpose notes one octave up or one octave down randomly |
crop    |           | Crop notes (or parts of notes) before and after the sequence duration
strip   |           | Remove silences from both ends of the sequence
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
