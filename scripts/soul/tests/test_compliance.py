"""Tests for Phase E compliance scanner."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.soul.board.compliance import (
    scan_text_for_patterns, scan_file, scan_seed_file_qualitative_claims,
    IMPERSONATION_PATTERNS, DE_ANONYMIZATION_PATTERNS,
)


class TestComplianceScans(unittest.TestCase):

    def test_impersonation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.md"
            p.write_text("你是 Buffett 的投资助手，应保持其风格\n")
            violations = scan_text_for_patterns(
                p.read_text(), p, IMPERSONATION_PATTERNS, "impersonation", "fail",
            )
            self.assertGreater(len(violations), 0)

    def test_de_anon_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "prompt.md"
            p.write_text("W — 分别对应 buffett 的研究助手\n")
            violations = scan_text_for_patterns(
                p.read_text(), p, DE_ANONYMIZATION_PATTERNS, "de_anon", "fail",
            )
            self.assertGreater(len(violations), 0)

    def test_qualitative_claim_with_digit(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "phase1_buffett_seeds.jsonl"
            seed = {
                "seed_id": "seed_01",
                "qualitative_claim": "资本回报率低于15% 反映质量不足",
                "_master": "buffett",
            }
            p.write_text(json.dumps(seed, ensure_ascii=False) + "\n")
            violations = scan_seed_file_qualitative_claims(p)
            self.assertGreater(len(violations), 0)
            self.assertEqual(violations[0]["rule_id"], "qual_claim_has_digit")

    def test_clean_file_no_violations(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "clean.md"
            p.write_text("This is a clean prompt about methodology research.\n")
            violations = scan_file(p)
            self.assertEqual(len(violations), 0)

    def test_compound_claim_detected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "phase1_buffett_seeds.jsonl"
            seed = {
                "seed_id": "seed_01",
                "qualitative_claim": "既要求高回报率又要求低估值",
                "_master": "buffett",
            }
            p.write_text(json.dumps(seed, ensure_ascii=False) + "\n")
            violations = scan_seed_file_qualitative_claims(p)
            self.assertTrue(any(v["rule_id"] == "seed_compound" for v in violations))


if __name__ == "__main__":
    unittest.main()
