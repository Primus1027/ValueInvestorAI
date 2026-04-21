"""Tests for pure-Python voting logic (severity + quantitative consensus)."""

import unittest

from scripts.soul.board.vote_severity import compute_lowest_severity, has_negation_semantics
from scripts.soul.board.vote_quantitative import compute_lowest_consensus
from scripts.soul.board.comparative import find_transitivity_violations


class TestSeverityConsensus(unittest.TestCase):

    def test_lightest_consensus_takes_note(self):
        r = compute_lowest_severity(
            {"buffett": "veto", "munger": "warning", "duan": "note"},
            "Long-term ROIC below baseline indicates quality shortfall",
        )
        self.assertEqual(r["layer0_severity"], "note")
        self.assertEqual(len(r["upgrade_agenda_items"]), 2)

    def test_negation_floor_forces_warning(self):
        r = compute_lowest_severity(
            {"buffett": "veto", "munger": "warning", "duan": "note"},
            "拒绝任何使用借贷资金的投资方案",
        )
        self.assertEqual(r["layer0_severity"], "warning")
        self.assertTrue(r["floored_due_to_negation"])

    def test_negation_without_veto_no_floor(self):
        r = compute_lowest_severity(
            {"buffett": "warning", "munger": "note", "duan": "note"},
            "拒绝任何使用借贷资金的投资方案",
        )
        self.assertEqual(r["layer0_severity"], "note")
        self.assertFalse(r["floored_due_to_negation"])

    def test_all_same_severity(self):
        r = compute_lowest_severity(
            {"buffett": "warning", "munger": "warning", "duan": "warning"},
            "A non-negating claim",
        )
        self.assertEqual(r["layer0_severity"], "warning")
        self.assertEqual(len(r["upgrade_agenda_items"]), 0)

    def test_has_negation_semantics(self):
        self.assertTrue(has_negation_semantics("拒绝任何借贷"))
        self.assertTrue(has_negation_semantics("禁止使用杠杆"))
        self.assertTrue(has_negation_semantics("归入太难堆"))
        self.assertFalse(has_negation_semantics("长期资本回报率过低"))


class TestQuantitativeConsensus(unittest.TestCase):

    def test_same_magnitude_gte_takes_min(self):
        # For >= N (larger = stricter), loosest bar = min → Layer 0 = 3
        proposals = {
            "buffett": {"proposed_threshold": 3, "proposed_operator": ">=", "rationale": ""},
            "munger": {"proposed_threshold": 5, "proposed_operator": ">=", "rationale": ""},
            "duan": {"proposed_threshold": 10, "proposed_operator": ">=", "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["layer0_threshold"], 3)
        self.assertEqual(c["mode"], "same_magnitude")
        self.assertEqual(len(c["follow_up_items"]), 2)  # munger + duan

    def test_same_magnitude_lt_takes_max(self):
        # For < N (smaller = stricter), loosest = max → Layer 0 = 15
        proposals = {
            "buffett": {"proposed_threshold": 10, "proposed_operator": "<", "rationale": ""},
            "munger": {"proposed_threshold": 12, "proposed_operator": "<", "rationale": ""},
            "duan": {"proposed_threshold": 15, "proposed_operator": "<", "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["layer0_threshold"], 15)

    def test_direction_conflict_detected(self):
        proposals = {
            "buffett": {"proposed_threshold": 3, "proposed_operator": ">=", "rationale": ""},
            "munger": {"proposed_threshold": 5, "proposed_operator": "<", "rationale": ""},
            "duan": {"proposed_threshold": 10, "proposed_operator": ">=", "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["mode"], "direction_conflict")
        self.assertTrue(c["requires_manual_review"])

    def test_qualitative_only_cluster_returns_no_threshold(self):
        proposals = {
            "buffett": {"proposed_threshold": None, "rationale": ""},
            "munger": {"proposed_threshold": None, "rationale": ""},
            "duan": {"proposed_threshold": None, "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["mode"], "no_threshold")


class TestTransitivity(unittest.TestCase):

    def test_detects_violation(self):
        matrix = [
            {"pair_id": "a-b", "seed_ids": ["a", "b"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "b-c", "seed_ids": ["b", "c"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "a-c", "seed_ids": ["a", "c"], "equivalent": False, "confidence": 0.8},
        ]
        seeds = [{"seed_id": "a"}, {"seed_id": "b"}, {"seed_id": "c"}]
        v = find_transitivity_violations(matrix, seeds)
        self.assertEqual(len(v), 1)

    def test_no_violation_when_all_equivalent(self):
        matrix = [
            {"pair_id": "a-b", "seed_ids": ["a", "b"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "b-c", "seed_ids": ["b", "c"], "equivalent": True, "confidence": 0.9},
            {"pair_id": "a-c", "seed_ids": ["a", "c"], "equivalent": True, "confidence": 0.9},
        ]
        seeds = [{"seed_id": "a"}, {"seed_id": "b"}, {"seed_id": "c"}]
        v = find_transitivity_violations(matrix, seeds)
        self.assertEqual(len(v), 0)

    def test_no_violation_when_none_equivalent(self):
        matrix = [
            {"pair_id": "a-b", "seed_ids": ["a", "b"], "equivalent": False, "confidence": 0.9},
            {"pair_id": "b-c", "seed_ids": ["b", "c"], "equivalent": False, "confidence": 0.9},
            {"pair_id": "a-c", "seed_ids": ["a", "c"], "equivalent": False, "confidence": 0.9},
        ]
        seeds = [{"seed_id": "a"}, {"seed_id": "b"}, {"seed_id": "c"}]
        v = find_transitivity_violations(matrix, seeds)
        self.assertEqual(len(v), 0)


if __name__ == "__main__":
    unittest.main()
