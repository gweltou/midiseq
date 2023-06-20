
from midiseq.sequence import Track
from midiseq.engine import TrackGroup


def test_track_sync():
    tg = TrackGroup()

    t1 = Track(channel=0, name="t1")
    assert t1._sync_from == None
    assert t1.name == "t1"

    t2 = Track(channel=1, name="t2", sync_from=t1)
    assert t2._sync_from is t1
    assert t2.name == "t2"
    assert len(t1._sync_children) == 1

    tg.addTrack(t1)

    for t in tg.tracks:
        print(t)
    
    assert len(tg.priority_list) == 2