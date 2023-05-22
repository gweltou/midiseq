# MidiTool

D'autres programmes dans le genre:

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

Hardware:

Monome - Teletype (module Eurorack)
https://monome.org/docs/teletype/


## Features

Polyphonic real-time midi sequencer in Python.
With a strong emphasis on generative composition and live performances.
Clear and short syntax while trying to remain as little esoteric as possible.
Explicit docstrings and error messages.


## Setup

 pip install rtmidi
 
Pour un environnement de programmation toute options :
 
 sudo apt install jupyter-qtconsole


## Usage

### Démarrage

```python

>>> from miditool import *

>>> listOutputs()
[0] Midi Through:Midi Through Port-0 14:0
[1] VCV Rack:VCV Rack input 133:0

>>> openOutput(1)
Opening port 1 [VCV Rack:VCV Rack input 133:0]

>>> setTempo(60)
>>> play(Seq("do do6 do re sol") * 4, loop=True)
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

### Notes, Chords and Silences

### Sequences

Create a random sequence of four notes:

  s = Seq().rand(4)

### Scales

You can constrain all generated notes in newly created sequences to a scale with the `setScale` function.

  setScale("minor", "c")

This won't affect previously created sequences.

### Generators

### Tracks

Whenever you want to chain sequences or generators, or if you want to play sequences in parallel on different midi channels you can use tracks.


## Alsa connect

List midi inputs (devices that can recieve midi)

  $ aconnect -i

List midi outputs (devices that can send midi)
  
  $ aconnect -o

Connecting devices together (sender to reciever)

  $ aconnect 132:0 130:0


## Développement futur / idées à explorer

* Micro-tonalité avec le pitch bend
* Classe Chord, additions Note-Note (=Seq), Chord-Note (=Seq), Seq-Note...
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
