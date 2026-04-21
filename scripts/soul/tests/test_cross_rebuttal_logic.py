"""Tests for cross_rebuttal pure-Python logic (dispute identification + anonymization)."""

import unittest

from scripts.soul.board.cross_rebuttal import (
    identify_dispute_clusters, anonymize_for_dispute,
)


class TestDisputeIdentification(unittest.TestCase):

    def test_threshold_variants_detected(self):
        revised = {
            "buffett": [
                {"seed_id": "b1", "_master": "buffett", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "munger": [
                {"seed_id": "m1", "_master": "munger", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.12, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "duan": [
                {"seed_id": "y1", "_master": "duan", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
        }
        matrix = [
            {"pair_id": "buffett/b1__munger/m1", "seed_ids": ["b1", "m1"],
             "masters": ["buffett", "munger"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "buffett/b1__duan/y1", "seed_ids": ["b1", "y1"],
             "masters": ["buffett", "duan"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "munger/m1__duan/y1", "seed_ids": ["m1", "y1"],
             "masters": ["munger", "duan"], "equivalent": True, "confidence": 0.9},
        ]
        disputes = identify_dispute_clusters(revised, matrix)
        self.assertEqual(len(disputes), 1)
        self.assertIn("threshold", disputes[0]["dispute_type"])

    def test_severity_variants_detected(self):
        revised = {
            "buffett": [
                {"seed_id": "b1", "_master": "buffett", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "munger": [
                {"seed_id": "m1", "_master": "munger", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "note",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "duan": [
                {"seed_id": "y1", "_master": "duan", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "veto",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
        }
        matrix = [
            {"pair_id": "buffett/b1__munger/m1", "seed_ids": ["b1", "m1"],
             "masters": ["buffett", "munger"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "buffett/b1__duan/y1", "seed_ids": ["b1", "y1"],
             "masters": ["buffett", "duan"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "munger/m1__duan/y1", "seed_ids": ["m1", "y1"],
             "masters": ["munger", "duan"], "equivalent": True, "confidence": 0.9},
        ]
        disputes = identify_dispute_clusters(revised, matrix)
        self.assertEqual(len(disputes), 1)
        self.assertIn("severity", disputes[0]["dispute_type"])

    def test_no_dispute_when_all_same(self):
        revised = {
            "buffett": [
                {"seed_id": "b1", "_master": "buffett", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "munger": [
                {"seed_id": "m1", "_master": "munger", "rule_subject": "target",
                 "theme": "moat", "qualitative_claim": "x",
                 "severity": "warning",
                 "quantitative_rule": {"threshold": 0.15, "metric": "r", "operator": "<", "data_field": "f"}},
            ],
            "duan": [],
        }
        matrix = [
            {"pair_id": "buffett/b1__munger/m1", "seed_ids": ["b1", "m1"],
             "masters": ["buffett", "munger"], "equivalent": True, "confidence": 0.9},
        ]
        disputes = identify_dispute_clusters(revised, matrix)
        # Even though equivalent, same threshold AND same severity → no dispute
        self.assertEqual(len(disputes), 0)


class TestAnonymization(unittest.TestCase):

    def test_stable_within_dispute(self):
        l1 = anonymize_for_dispute("dispute_X")
        l2 = anonymize_for_dispute("dispute_X")
        self.assertEqual(l1, l2)

    def test_all_labels_assigned(self):
        m = anonymize_for_dispute("dispute_Y")
        self.assertEqual(set(m.keys()), {"buffett", "munger", "duan"})
        self.assertEqual(set(m.values()), {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
