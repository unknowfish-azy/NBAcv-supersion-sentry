import unittest

from basketball_track_guard import audit_track
from court_geometry import footpoint_in_polygon, filter_detections_by_court
from shot_event_fsm import ShotEventFSM


class BasketballPipelineTests(unittest.TestCase):
    def test_track_guard_marks_large_speed_and_gap_for_review(self):
        rows = [
            {"timestamp": 0.0, "track_id": "ball", "bbox": [10, 10, 10, 10], "confidence": 0.9},
            {"timestamp": 0.1, "track_id": "ball", "bbox": [12, 12, 10, 10], "confidence": 0.9},
            {"timestamp": 1.6, "track_id": "ball", "bbox": [300, 300, 10, 10], "confidence": 0.8},
        ]
        result = audit_track(rows, max_speed_px_s=500, max_gap_s=0.5)
        self.assertEqual(result["status"], "REVIEW")
        self.assertGreaterEqual(len(result["issues"]), 1)

    def test_court_filter_uses_bottom_center(self):
        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        self.assertTrue(footpoint_in_polygon([40, 40, 20, 20], polygon))
        self.assertFalse(footpoint_in_polygon([40, 90, 20, 20], polygon))
        kept, rejected = filter_detections_by_court(
            [{"id": "a", "bbox": [40, 40, 20, 20]}, {"id": "b", "bbox": [40, 90, 20, 20]}], polygon)
        self.assertEqual([x["id"] for x in kept], ["a"])
        self.assertEqual(rejected[0]["reason"], "footpoint_outside_court")

    def test_shot_fsm_requires_evidence_for_made(self):
        fsm = ShotEventFSM()
        fsm.update(0.0, ball=(50, 80), wrist=(50, 82), rim_y=40, rim_x=(40, 60))
        fsm.update(0.1, ball=(50, 60), wrist=(50, 50), rim_y=40, rim_x=(40, 60))
        fsm.update(0.2, ball=(50, 30), wrist=None, rim_y=40, rim_x=(40, 60))
        fsm.update(0.3, ball=(50, 45), wrist=None, rim_y=40, rim_x=(40, 60))
        self.assertEqual(fsm.result["status"], "made")

    def test_shot_fsm_unknown_without_rim(self):
        fsm = ShotEventFSM()
        fsm.update(0.0, ball=(50, 80), wrist=(50, 82), rim_y=None, rim_x=None)
        fsm.update(0.1, ball=(50, 30), wrist=None, rim_y=None, rim_x=None)
        self.assertEqual(fsm.result["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
