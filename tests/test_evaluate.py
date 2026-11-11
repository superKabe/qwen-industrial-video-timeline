from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate import evaluate


class EvaluateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ground_truth = [
            {"event_type": "pick up tools", "start_s": 10.0, "end_s": 12.0},
            {"event_type": "fastening bolt", "start_s": 20.0, "end_s": 25.0},
            {"event_type": "fastening bolt", "start_s": 30.0, "end_s": 35.0},
        ]

    def test_perfect_prediction(self) -> None:
        report = evaluate(self.ground_truth, self.ground_truth, 0.3)
        self.assertEqual(report["summary"]["matched_events"], 3)
        self.assertEqual(report["summary"]["f1"], 1.0)

    def test_correct_label_at_wrong_time_is_mislocalized(self) -> None:
        prediction = [{"event_type": "pick up tools", "start_s": 15.0, "end_s": 17.0}]
        report = evaluate(self.ground_truth, prediction, 0.3)
        self.assertEqual(report["summary"]["mislocalized_predictions"], 1)
        self.assertEqual(report["summary"]["unsupported_labels"], 0)

    def test_repeated_actions_match_one_to_one(self) -> None:
        prediction = [
            {"event_type": "fastening bolt", "start_s": 20.0, "end_s": 25.0},
            {"event_type": "fastening bolt", "start_s": 30.0, "end_s": 35.0},
        ]
        report = evaluate(self.ground_truth, prediction, 0.3)
        self.assertEqual(report["summary"]["matched_events"], 2)
        self.assertEqual(report["summary"]["duplicate_predictions"], 0)


if __name__ == "__main__":
    unittest.main()
