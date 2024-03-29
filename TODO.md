# TODO

- [ ] Iteration sur la classe Chord
- [ ] Synchronisation du bpm depuis un signal extérieur
- [ ] Émission de messages de tempo
- [ ] Permettre des enregistrements midi live silencieux
- [ ] Méthodes __mul__ et __rmull__ à la classe Chord

# Changelog

* New `octaveShift` method for Seq.
* Simple interface : playX/stopX/pushTx/popTx.
* New `parse` function for convert a string sequence to a Seq.
* New `PNote` class, a type of Note that can resolve to different pitches with probabilities.
* `openOutput` accepts a `str` argument, with is matched against ports descriptions.
* New Seq methods : `mask` and `maskNot`.

## Développement futur / idées à explorer

Devrait-on supprimer les paramètres "silprob" des fonctions rnd, runDur, rndWalk, rndGauss & co ?
(Redondance avec la transformation "decimate". Différence: silprob ajoute des Sil à la séquence)

### Parser

* Sequencial group (ex: "<do re mi>"), but that would need storing and passing a state
* Repeat modifier, (ex: "(do re mi)*4")
* Ratcheting modifier, "note__n"
* Existence modifier, with prob ("do?0.1")

#### Aliases

  Les alias auraient la précédence sur les autres formes de notations.
  Stockées dans un dictionnaire.
  (ex: "K" -> 48).

### Engine

* fadePlay([str, Seq], sec)
* fadeStop(sec)
* pushM1-16()  # Midi modulation
* popM1-16()

* env.localOffset
* env.netOffset

### Elements

* Remplacer la méthode `shift` par une méthode `offset`, qu'on retrouverait aussi dans la classe `Note`. La classe `note` doit connaître son parent `Seq`.
* Micro-tonalité avec le pitch bend
* Pouvoir associer une fonction de callback à la réception d'un contrôle midi
* Listen() devrait n'avoir à s'appeler qu'une seule fois. Créer une fonction stop_listen().
* Possibilité de jouer des notes d'une séquence se trouvent au delà de la taille (param length) de la séquence.
* Autoriser les pitch négatifs (utile lorsqu'on utilise la transposition)
* Les fonctions lambda de `filter`, `separate`, etc... doivent accepter 3 paramètres : `i` (index), `t` (time) et `n` (Note)

### Class Note

  * Ratchet(n) -> Divise la note en `n` notes de durée égales
  * offset(shift) -> Deplace la note dans le temps, si elle appartient à une séquence

### Classe Seq

  * shapeVel(fn)
  * shapePitch(fn)
  * separate(fn) -> Sépare les notes de la séquence en deux séquences différentes, d'après fonction
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
  * delay(offset, num, att)

### Classe Chord

  * fonction `omit(*degrees)`

### Classe Track

  * addClear([Seq, str]) Supprime toutes les séquences et ajoute celle-ci, seulement à la fin de la séquence actuelle.

### Net

* connect(ip)
* disconnect()
* startServer()
* stopServer()
