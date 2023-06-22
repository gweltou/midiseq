
from midiseq.sequence import Track, Seq
from midiseq.engine import TrackGroup


def test_track():
    t = Track(name="my_track")
    t.add(Seq("do re mi fa"))
    assert t.name == "my_track"
    assert len(t.seqs) == 1

    t.reset()
    data = t.update(0.0)
    assert len(data) == 8
    assert t._next_timer == 0.5 # Half a second

    t.clear()
    assert len(t.seqs) == 0
    assert t.seq_i == 0
    print(t._next_timer)


def test_instrument():
    t = Track(instrument=15)
    t.add(Seq("do re mi"))
    t.reset()
    data = t.update(0.0)
    assert len(data) == 7


def test_trackgroup():
    tg = TrackGroup()

    t1 = Track(channel=0, name="t1")
    assert t1._sync_from == None

    t2 = Track(channel=1, name="t2", sync_from=t1)
    assert t2._sync_from is t1
    assert len(t1._sync_children) == 1

    tg.addTrack(t1)

    for t in tg.tracks:
        print(t)
    
    assert len(tg.priority_list) == 2