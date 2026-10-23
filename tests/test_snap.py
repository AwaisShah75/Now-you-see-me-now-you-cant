import unittest
from types import SimpleNamespace
from snap import SnapDetector


def hand(closed=True):
    points = [SimpleNamespace(x=0., y=0., z=0.) for _ in range(21)]
    for n,(tip,pip) in enumerate(((8,6),(12,10),(16,14),(20,18))):
        points[pip] = SimpleNamespace(x=n*.08, y=1., z=0.)
        points[tip] = SimpleNamespace(x=n*.08, y=.6 if closed else 1.7, z=0.)
    return points


class FistTests(unittest.TestCase):
    def test_hold_and_latch(self):
        d=SnapDetector()
        self.assertFalse(d.update(hand(),0))
        self.assertFalse(d.update(hand(),.2))
        self.assertTrue(d.update(hand(),.36))
        self.assertFalse(d.update(hand(),3))

    def test_open_hand_rearms(self):
        d=SnapDetector();d.update(hand(),0)
        self.assertTrue(d.update(hand(),.4))
        d.update(hand(False),1)
        d.update(hand(),2)
        self.assertTrue(d.update(hand(),2.4))

    def test_open_hand_never_triggers(self):
        d=SnapDetector()
        for t in (0,.4,1,3):self.assertFalse(d.update(hand(False),t))

    def test_tracking_loss_does_not_rearm(self):
        d=SnapDetector();d.update(hand(),0)
        self.assertTrue(d.update(hand(),.4))
        d.update(None,1)
        self.assertFalse(d.update(hand(),3))

    def test_rotation(self):
        p=hand()
        for v in p:v.y,v.z=v.z,v.y
        d=SnapDetector();d.update(p,0)
        self.assertTrue(d.update(p,.4))
