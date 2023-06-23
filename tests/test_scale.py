from midiseq import Seq, Scale, Note


def test_scale_getdegree():
    sc = Scale("major", "c")
    assert sc.getDegree(0) == sc.tonic
    assert sc.getDegree(1) == sc.tonic + 2
    assert sc.getDegree(2) == sc.tonic + 4
    assert sc.getDegree(7) == sc.tonic + 12
    assert sc.getDegree(-1) == sc.tonic - 1
    assert sc.getDegree(-2) == sc.tonic - 3
    assert sc.getDegree(-7) == sc.tonic - 12

    sc = Scale("minor", "b")
    assert sc.getDegree(0) == sc.tonic
    assert sc.getDegree(1) == sc.tonic + 2
    assert sc.getDegree(2) == sc.tonic + 3
    assert sc.getDegree(7) == sc.tonic + 12
    assert sc.getDegree(-1) == sc.tonic - 2
    assert sc.getDegree(-2) == sc.tonic - 4
    assert sc.getDegree(-7) == sc.tonic - 12


def test_scale_getclosest():
    sc = Scale("minor", "b")
    assert sc.getClosest("do") == Note("-1b").pitch


def test_scale_getdegreefrom():
    sc = Scale("minor", "b")
    assert sc.getDegreeFrom("b", 0) == Note("b").pitch
    