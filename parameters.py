import random


# Sitala drum sampler mapping to midi pitch
# Clean 808
sit1 = 36 # Kick
sit2 = 37 # Snare
sit3 = 38 # Closed HH
sit4 = 39 # Open HH
sit5 = 40 # Cymbal
sit6 = 41 # Low Tom
sit7 = 42 # Mid Tom
sit8 = 43 # High Tom
sit9 = 44 # Low Conga
sit10 = 45 # Mid Conga
sit11 = 46 # High Conga
sit12 = 47 # Hand Clap
sit13 = 48 # Clave
sit14 = 49 # Maraca
sit15 = 50 # Cowbell
sit16 = 51 # Rim shot




def loop1():
    g = Grid()
    g.length = 2
    g.euclid(sit3, 12, 1)
    g.euclid(sit2, 4, 4)
    g.euclid(sit1, 2, 0)
    return g


def loop_euclidian_sitala():
    short = [sit3, sit4, sit14, sit16]
    g = Grid()
    g.length = 4

    g.euclid(sit1, random.randint(2, 5), random.randint(0, 3))
    g.euclid(sit2, random.randint(2, 5), random.randint(1, 5))

    if random.random() > 0.5:
        g.euclid(sit12, random.randint(1, 3), random.randint(0, 8))

    random.shuffle(short)
    for i in range(random.randint(0, len(short))):
        n = random.randint(5, 12)
        g.euclid(short[i], n, random.randint(0, n))

    return g