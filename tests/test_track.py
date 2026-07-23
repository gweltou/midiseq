from midiseq.elements import Seq
from midiseq.tracks import Track, TrackGroup
from midiseq.ports import OutputPort
from midiseq.utils import rnd
from midiseq import env as env


output_port = OutputPort(0)


def test_track():
    t = Track(port=output_port, name="my_track")
    
    env.note_dur = 1/8
    t.add(Seq("do re mi fa"))
    assert t.name == "my_track"
    assert len(t.sequences) == 1

    t.start()
    t.process(0.0)

    # Only the first note on event should have been sent at this point
    assert len(output_port._events) == 1
    assert t._sequence_dur == 0.5 # Half a second

    t.clear()
    assert len(t.sequences) == 0
    assert t._sequence_idx == 0


def test_instrument():
    t = Track(port=output_port, instrument=15)

    t.add(Seq("do re mi"))
    t.start()
    t.process(0.0)
    assert len(output_port._events) == 2


def test_trackgroup():
    tg = TrackGroup()

    t1 = Track(port=output_port, channel=0, name="t1")
    assert t1._sync_from == None

    t2 = Track(port=output_port, channel=1, name="t2", sync_from=t1)
    assert t2._sync_from is t1
    assert len(t1._sync_children) == 1

    tg.add_track(t1)
    
    assert len(tg.priority_list) == 2


def test_track_modifiers():
    t = Track(port=output_port)
    t.add(rnd(8))
    t.push(Seq.stretch, 2.0)
    t.process(0.0)

    t.pop()
    assert len(t.transforms) == 0