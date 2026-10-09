"""Small evidence-driven shot state machine; unknown is the safe result."""
from __future__ import annotations

import math
from typing import Any


class ShotEventFSM:
    def __init__(self, hand_radius_px: float = 30):
        self.hand_radius_px = hand_radius_px
        self.state = "idle"
        self.previous = None
        self.result: dict[str, Any] = {"status": "unknown", "reason": "insufficient_evidence"}

    def update(self, timestamp: float, *, ball, wrist=None, rim_y=None, rim_x=None):
        if ball is None or rim_y is None or rim_x is None:
            self.result = {"status": "unknown", "reason": "missing_ball_or_rim"}
            self.previous = None
            return self.result
        if wrist is not None and math.dist(ball, wrist) <= self.hand_radius_px and self.state == "idle":
            self.state = "possession"
        if self.previous is not None:
            old_t, old_ball = self.previous
            if timestamp <= old_t:
                self.result = {"status": "unknown", "reason": "non_increasing_timestamp"}
                return self.result
            if self.state == "possession" and ball[1] < old_ball[1]:
                self.state = "flight"
            if self.state == "flight" and old_ball[1] < rim_y <= ball[1]:
                if rim_x[0] <= ball[0] <= rim_x[1]:
                    self.state = "made"
                    self.result = {"status": "made", "timestamp": timestamp, "evidence": "downward_rim_plane_crossing"}
                else:
                    self.state = "miss"
                    self.result = {"status": "miss", "timestamp": timestamp, "evidence": "outside_rim_plane"}
        self.previous = (float(timestamp), tuple(ball))
        return self.result
