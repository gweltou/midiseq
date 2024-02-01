# TODO

- [ ] Iteration sur la classe Chord
- [ ] Opérateur `%` (durée des notes) à la classe Seq
- [ ] Rajouter l'opérateur `%` aux classes Note et Chord (bon ça parraît un peu redondant mais c'est pour la coherence)
- [ ] Synchronisation du bpm depuis un signal extérieur
- [ ] Émission de messages de tempo
- [ ] Permettre des enregistrements midi live silencieux
- [X] Tap rhythm with microphone
- [X] Opérateur `^` (transposition) à la classe Chord
- [X] Améliorer l'ajout de générateurs (avec et sans arguments) à une Track
- [X] Chord string notation
- [X] Opérateur `^` (transposition) à la classe Seq
- [X] Paramètre `silprob` pour les fonctions randXXX
- [X] Track instrument selection (via midi program changes)

# Changelog

* Simple interface : playX/stopX/pushTx/popTx
* New `parse` function for convert a string sequence to a Seq
* New `PNote` class, a type of Note that can resolve to different pitches with probabilities.
* `openOutput` accepts a `str` argument, with is matched against ports descriptions
* New Seq methods : `mask` and `maskNot`

## Développement futur / idées à explorer

### Parser

* "note__n" -> ratcheting
* "(do re mi)*4" -> repeat
* Sequencial group (ex: "<do re mi>"), but that would need storing and passing a state
* Existence modifier, with prob (do?0.1)

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

* Remplacer la méthode `shift` par une méthode `offset`, qu'on retrouverait aussi dans la classe `Note`. La classe `note` doit connaître son parent `Seq` (why ?).
* Micro-tonalité avec le pitch bend
* Pouvoir associer une fonction de callback à la réception d'un contrôle midi
* Listen() devrait n'avoir à s'appeler qu'une seule fois. Créer une fonction stop_listen().
* Possibilité de jouer des notes d'une séquence se trouvent au delà de la taille (param length) de la séquence.
* Autoriser les pitch négatifs (utile lorsqu'on utilise la transposition)
* Les fonctions lambda de `filter`, `separate`, etc... doivent accepter 3 paramètres : `i` (index), `t` (time) et `n` (Note)

### Class Note

  * Ratchet(n) -> Divise la note en `n` notes de durée égales
  * offset (shift) -> Deplace la note dans le temps, si elle appartient à une séquence

### Classe Seq

  * shapeVel(fn)
  * shapePitch(fn)
  * separte(fn) -> Sépare les notes de la séquence en deux séquences différentes, d'après fonction
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