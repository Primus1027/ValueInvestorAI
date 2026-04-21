"""Regression tests for issues found in code review (2026-04-21)."""

import unittest

from scripts.soul.board.comparative import _coerce_bool, _coerce_float
from scripts.soul.board.dropped_tracker import _extract_year_from_debate_id, DroppedTracker
from scripts.soul.board.vote_quantitative import compute_lowest_consensus
from scripts.soul.board.render import count_veto_in_md, count_hard_in_md
import tempfile
from pathlib import Path


class TestLLMCoercion(unittest.TestCase):
    """P0 #2 + P1 #7/#8 — bool/float coercion from LLM string outputs."""

    def test_bool_string_false_is_false(self):
        """bool('false') == True in Python — we must NOT use bool() directly."""
        self.assertFalse(_coerce_bool("false"))
        self.assertFalse(_coerce_bool("FALSE"))
        self.assertFalse(_coerce_bool("False"))
        self.assertFalse(_coerce_bool("no"))
        self.assertFalse(_coerce_bool("不等价"))
        self.assertFalse(_coerce_bool(""))
        self.assertFalse(_coerce_bool("0"))

    def test_bool_string_true_is_true(self):
        self.assertTrue(_coerce_bool("true"))
        self.assertTrue(_coerce_bool("TRUE"))
        self.assertTrue(_coerce_bool("yes"))
        self.assertTrue(_coerce_bool("1"))
        self.assertTrue(_coerce_bool("等价"))

    def test_bool_real_types(self):
        self.assertTrue(_coerce_bool(True))
        self.assertFalse(_coerce_bool(False))
        self.assertTrue(_coerce_bool(1))
        self.assertFalse(_coerce_bool(0))

    def test_bool_invalid_uses_default(self):
        self.assertFalse(_coerce_bool(None))
        self.assertFalse(_coerce_bool({"k": "v"}))
        self.assertTrue(_coerce_bool("garbage", default=True))

    def test_float_coercion(self):
        self.assertEqual(_coerce_float(0.5), 0.5)
        self.assertEqual(_coerce_float("0.5"), 0.5)
        self.assertEqual(_coerce_float(" 0.5 "), 0.5)
        self.assertEqual(_coerce_float("high"), 0.0)
        self.assertEqual(_coerce_float(None), 0.0)
        self.assertEqual(_coerce_float([]), 0.0)


class TestYearExtraction(unittest.TestCase):
    """P1 #12 — robust year extraction from debate_id."""

    def test_standard_format(self):
        self.assertEqual(_extract_year_from_debate_id("2026-04-21_manual"), "2026")

    def test_prefix_format(self):
        self.assertEqual(_extract_year_from_debate_id("test-2026-01-01"), "2026")

    def test_no_year_falls_back(self):
        y = _extract_year_from_debate_id("manual")
        self.assertEqual(len(y), 4)
        self.assertTrue(y.isdigit())

    def test_empty_string(self):
        y = _extract_year_from_debate_id("")
        self.assertEqual(len(y), 4)


class TestDroppedReintroFailureNotInSlidingWindow(unittest.TestCase):
    """P1 (logic) #2 — consecutive_drops must not count reintro failures."""

    def test_reintro_failure_does_not_increment_consecutive_drops(self):
        tmp = Path(tempfile.mkdtemp())
        dt = DroppedTracker(tmp / "a.md")
        for did in ["2026-04", "2026-07", "2026-10"]:
            dt.record_drop("cl_X", did, 1, "claim", "self", "veto_line")
        self.assertTrue(dt.records["cl_X"].is_archived())
        before = dt.records["cl_X"].consecutive_drops()

        # Re-intro failure should NOT increase consecutive_drops
        dt.record_reintroduction_failure("cl_X", "2027-04", 1)
        after = dt.records["cl_X"].consecutive_drops()
        self.assertEqual(before, after)

        # But the failure is still recorded in history for audit
        self.assertEqual(len(dt.records["cl_X"]._drop_history), 4)


class TestZeroThresholdConsensus(unittest.TestCase):
    """P1 (logic) #4 — threshold=0 requires manual review, not domination."""

    def test_mixed_zero_and_nonzero_requires_manual(self):
        proposals = {
            "buffett": {"proposed_threshold": 3, "proposed_operator": ">=", "rationale": ""},
            "munger": {"proposed_threshold": 10, "proposed_operator": ">=", "rationale": ""},
            "duan": {"proposed_threshold": 0, "proposed_operator": ">=", "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["mode"], "zero_threshold_present")
        self.assertTrue(c["requires_manual_review"])
        self.assertIsNone(c["layer0_threshold"])

    def test_all_zero_accepted(self):
        proposals = {
            "buffett": {"proposed_threshold": 0, "proposed_operator": "==", "rationale": ""},
            "munger": {"proposed_threshold": 0, "proposed_operator": "==", "rationale": ""},
            "duan": {"proposed_threshold": 0, "proposed_operator": "==", "rationale": ""},
        }
        c = compute_lowest_consensus(proposals, {})
        self.assertEqual(c["layer0_threshold"], 0)


class TestRenderRegex(unittest.TestCase):
    """P0 (logic) #1 — count_veto_in_md must match actual rendered format."""

    def test_v1_0_format(self):
        md = (
            "### 1. ROIC\n- **Severity**: `veto`\n\n"
            "### 2. Moat\n- **Severity**: `warning`\n"
        )
        self.assertEqual(count_hard_in_md(md), 2)
        self.assertEqual(count_veto_in_md(md), 1)

    def test_v1_1_format(self):
        md = (
            "### 1. Business model\n"
            "- **Severity (Layer 0)**: `veto` — 拦截投资决策\n\n"
            "### 2. Moat\n"
            "- **Severity (Layer 0)**: `note` — 仅记录\n"
        )
        self.assertEqual(count_hard_in_md(md), 2)
        self.assertEqual(count_veto_in_md(md), 1)

    def test_empty_md(self):
        self.assertEqual(count_hard_in_md(""), 0)
        self.assertEqual(count_veto_in_md(""), 0)


if __name__ == "__main__":
    unittest.main()
