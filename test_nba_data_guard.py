import unittest

from nba_data_guard import (normalize_players, build_sentinel_report,
                             resolve_schedule_context, classify_closed_set_frame,
                             validate_color_metric, filter_bootstrap_boxes,
                             resource_preflight)


class NbaDataGuardTests(unittest.TestCase):
    def test_normalize_players(self):
        rows = normalize_players([{"team": "HOU", "name": "Amen Thompson", "jersey": 1,
                                  "player_id": 4684740, "height_in": "79", "position": "G"}], "fixture")
        self.assertEqual(rows[0]["jersey_number"], "1")
        self.assertEqual(rows[0]["identity_features"]["position_group"], "guard")

    def test_duplicate_jersey_blocks(self):
        report = build_sentinel_report([
            {"team": "HOU", "jersey_number": "1", "player_id": "a"},
            {"team": "HOU", "jersey_number": "1", "player_id": "b"}], [])
        self.assertEqual(report["status"], "BLOCK")

    def test_context_unknown_when_no_unique_match(self):
        games = [{"game_id": "g1", "date_utc": "2025-11-04T01:00Z", "home": "HOU", "away": "DAL"}]
        self.assertEqual(resolve_schedule_context(games, "2025-11-05T01:00Z", {"HOU", "DAL"})["status"], "context_unknown")

    def test_person_signal_does_not_prove_closed_set_miss(self):
        for count in (None, 0, 1):
            self.assertEqual(classify_closed_set_frame([], {"amen"}, count)["status"], "unverifiable")
        self.assertEqual(classify_closed_set_frame([], {"amen"}, 1, {"powell"})["status"], "valid_empty_closed_set")
        self.assertEqual(classify_closed_set_frame([], {"amen"}, 1, {"amen"})["status"], "suspicious")

    def test_large_pseudo_label_sample_does_not_validate_accuracy(self):
        self.assertIsNone(validate_color_metric(human_gt_count=1000, reported_accuracy=.924)["reported_accuracy"])

    def test_color_accuracy_requires_independent_human_ground_truth(self):
        result = validate_color_metric(human_gt_count=4, reported_accuracy=0.924)
        self.assertEqual(result["status"], "unverified")
        self.assertIsNone(result["reported_accuracy"])

    def test_bootstrap_filter_rejects_feet_outside_court_polygon(self):
        boxes = [{"id": "clean", "bbox": [40, 40, 20, 20]},
                 {"id": "sideline", "bbox": [200, 200, 20, 20]}]
        kept, audit = filter_bootstrap_boxes(boxes, [(0, 0), (100, 0), (100, 100), (0, 100)])
        self.assertEqual([x["id"] for x in kept], ["clean"])
        self.assertEqual(audit["rejected"], 1)

    def test_resource_preflight_blocks_low_memory(self):
        result = resource_preflight(available_memory_mb=512, min_memory_mb=1024, path="C:/data")
        self.assertEqual(result["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
