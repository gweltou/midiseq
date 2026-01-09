
from midiseq.elements import Seq
from midiseq.tracks import Track, TrackGroup
from midiseq.utils import rnd
from midiseq import env as env



def test_track():
    t = Track(name="my_track")
    env.note_dur = 1/8
    t.add(Seq("do re mi fa"))
    assert t.name == "my_track"
    assert len(t.seqs) == 1

    t.start()
    data = t.update(0.0)
    assert len(data) == 8
    assert t._next_timer == 0.5 # Half a second

    t.clear()
    assert len(t.seqs) == 0
    assert t.seq_i == 0


def test_instrument():
    t = Track(instrument=15)
    t.add(Seq("do re mi"))
    t.start()
    data = t.update(0.0)
    assert len(data) == 7


def test_trackgroup():
    tg = TrackGroup()

    t1 = Track(channel=0, name="t1")
    assert t1._sync_from == None

    t2 = Track(channel=1, name="t2", sync_from=t1)
    assert t2._sync_from is t1
    assert len(t1._sync_children) == 1

    tg.add_track(t1)
    
    assert len(tg.priority_list) == 2


def test_track_modifiers():
    t = Track()
    t.add(rnd(8))
    t.push(Seq.stretch, 2.0)
    m = t.update(0.0)

    t.pop()
    assert len(t.transforms) == 0