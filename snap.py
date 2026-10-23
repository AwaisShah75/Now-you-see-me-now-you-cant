"""A closed-fist hold gesture independent of the camera UI."""
import math

class SnapDetector:
    def __init__(self):
        self.started = None
        self.latched = False
        self.last_trigger = -10.0
        self.progress = 0.0

    def update(self, landmarks, now):
        if not landmarks:
            self.started = None
            self.progress = 0.0
            return False
        def distance(a, b):
            return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 +
                             (getattr(a, 'z', 0)-getattr(b, 'z', 0))**2)
        # Compare each fingertip with its own middle joint relative to wrist.
        # 3D distances preserve the decision when the hand rotates.
        ratios = [distance(landmarks[tip], landmarks[0]) /
                  max(distance(landmarks[pip], landmarks[0]), .001)
                  for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18))]
        closed = sum(r < 1.0 for r in ratios) >= 3 and max(ratios) < 1.15
        opened = sum(r > 1.25 for r in ratios) >= 3
        if opened:
            self.latched = False
            self.started = None
            self.progress = 0.0
        elif closed and not self.latched:
            if self.started is None:
                self.started = now
            self.progress = min(1.0, (now-self.started)/0.35)
            if self.progress >= 1 and now-self.last_trigger > 1.2:
                self.latched = True
                self.last_trigger = now
                return True
        elif not self.latched:
            self.started = None
            self.progress = 0.0
        return False
