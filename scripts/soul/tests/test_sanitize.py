"""Tests for Phase 1.5 sanitize (static pass only; LLM pass tested manually)."""

import unittest

from scripts.soul.board.sanitize import (
    sanitize_seed_static, load_fingerprint_dict,
    apply_static_replacement, detect_remaining_fingerprints,
    sanitize_all_seeds,
)


class TestSanitizeStatic(unittest.TestCase):

    def setUp(self):
        self.replacements, self.scan_patterns = load_fingerprint_dict()

    def test_fingerprint_replacements_applied(self):
        seed = {
            "seed_id": "seed_01",
            "_master": "duan",
            "qualitative_claim": "商业模式过于复杂则归入太难的堆",
            "rationale": "本分要求明知是错就不做，能力圈外要拒绝",
            "anti_scope": "本条不约束一般市场分析",
            "supporting_section_id": "duan/y-.../section",
            "rule_subject": "self",
            "theme": "circle_of_competence",
            "category": "veto_line",
            "severity": "veto",
            "evidence_strength": "direct_quote",
            "supporting_profile_factor": "simplicity",
            "quantitative_rule": None,
            "qualitative_rule": "test",
        }
        counter = [0]
        sanitized, ref_map, needs_llm = sanitize_seed_static(
            seed, self.replacements, self.scan_patterns, counter,
        )
        self.assertNotIn("太难的堆", sanitized["qualitative_claim"])
        self.assertNotIn("本分", sanitized["rationale"])
        self.assertNotIn("能力圈", sanitized["rationale"])
        self.assertEqual(sanitized["supporting_section_id"], "[ref_1]")
        self.assertTrue(sanitized["_sanitized"])

    def test_ref_map_tracks_original(self):
        seed = {
            "seed_id": "s1", "_master": "buffett",
            "qualitative_claim": "x", "rationale": "y", "anti_scope": "z",
            "supporting_section_id": "buffett/module/circle",
            "rule_subject": "target", "theme": "moat", "category": "qualitative_required",
            "severity": "warning", "evidence_strength": "direct_quote",
            "supporting_profile_factor": "f", "quantitative_rule": None,
            "qualitative_rule": "r",
        }
        counter = [0]
        _, ref_map, _ = sanitize_seed_static(seed, self.replacements, self.scan_patterns, counter)
        self.assertIn("[ref_1]", ref_map)
        self.assertEqual(ref_map["[ref_1]"], "buffett/module/circle")

    def test_counter_increments_across_seeds(self):
        counter = [0]
        for i in range(3):
            seed = {
                "seed_id": f"s{i}", "_master": "buffett",
                "qualitative_claim": "x", "rationale": "y", "anti_scope": "z",
                "supporting_section_id": f"path_{i}",
                "rule_subject": "target", "theme": "moat", "category": "qualitative_required",
                "severity": "warning", "evidence_strength": "direct_quote",
                "supporting_profile_factor": "f", "quantitative_rule": None,
                "qualitative_rule": "r",
            }
            san, _, _ = sanitize_seed_static(seed, self.replacements, self.scan_patterns, counter)
            self.assertEqual(san["supporting_section_id"], f"[ref_{i+1}]")
        self.assertEqual(counter[0], 3)

    def test_static_replacement_multi_keys(self):
        text = "本分 和 能力圈 都很重要"
        new, keys = apply_static_replacement(text, self.replacements)
        self.assertNotIn("本分", new)
        self.assertNotIn("能力圈", new)
        self.assertIn("本分", keys)
        self.assertIn("能力圈", keys)

    def test_remaining_fingerprint_detection(self):
        # A passage containing a master name — should be detected
        text = "这是 Buffett 的核心观点"
        hits = detect_remaining_fingerprints(text, self.scan_patterns)
        self.assertGreater(len(hits), 0)


class TestSanitizeGuard(unittest.TestCase):
    """Guard: sanitize_all_seeds must refuse to proceed on silent upstream failure.

    Background: v1.1 debate shipped 28 garbage HARD rules because phase1 errored
    for buffett silently (empty `error` string), sanitize iterated an empty list,
    wrote a 0-byte file, and the pipeline continued end-to-end with 2 masters.
    """

    def test_raises_on_master_with_error_status(self):
        phase1_summary = {
            "debate_id": "test",
            "results_by_master": {
                "buffett": {"master": "buffett", "seeds": [], "seed_count": 0,
                             "status": "error", "error": "TimeoutError"},
                "munger": {"master": "munger",
                            "seeds": [{"seed_id": "m1", "_master": "munger"}],
                            "status": "success"},
                "duan": {"master": "duan",
                          "seeds": [{"seed_id": "d1", "_master": "duan"}],
                          "status": "success"},
            },
        }
        with self.assertRaises(RuntimeError) as ctx:
            sanitize_all_seeds(phase1_summary)
        self.assertIn("buffett", str(ctx.exception))
        self.assertIn("error", str(ctx.exception).lower())

    def test_raises_on_master_with_zero_seeds(self):
        phase1_summary = {
            "debate_id": "test",
            "results_by_master": {
                "buffett": {"master": "buffett", "seeds": [], "seed_count": 0,
                             "status": "success"},
                "munger": {"master": "munger",
                            "seeds": [{"seed_id": "m1", "_master": "munger"}],
                            "status": "success"},
                "duan": {"master": "duan",
                          "seeds": [{"seed_id": "d1", "_master": "duan"}],
                          "status": "success"},
            },
        }
        with self.assertRaises(RuntimeError) as ctx:
            sanitize_all_seeds(phase1_summary)
        self.assertIn("buffett", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
