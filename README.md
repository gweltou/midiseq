# MidiTool

D'autres programmes dans le genre:
WarpSeq:
https://bitbucket.org/laserllama/warpseq/src/master/

Braid:
https://braid.live/

MusicPy
https://github.com/Rainbow-Dreamer/musicpy


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

### Le temps

Pour changer la durée d'une séquence on modifie sa propriété `length`. On peut aussi la passer en argument au constructeur de la classe `Seq`.
```python
s = Seq(4)
# ou bien
s = Seq()
s.length = 4
```

L'unité temporelle est égale à une seconde.

### Notes, Chords and Silences

### Sequences

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
* Fonction de selection des notes d'après critères. Possibilité d'appliquer une transfo quelconque sur la séléction de notes (transpose, vel, dur)