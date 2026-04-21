"""Tests for scripts.soul.validate_seed."""

import unittest
from scripts.soul.validate_seed import validate_seed, validate_seeds_file
import json
import tempfile
from pathlib import Path


def _good_seed() -> dict:
    return {
        "seed_id": "seed_01",
        "_master": "buffett",
        "rule_subject": "target",
        "theme": "capital_return",
        "category": "quantitative_hard",
        "qualitative_claim": "长期资本回报率过低反映业务质量不足",
        "quantitative_rule": {
            "metric": "roic_10yr_avg", "operator": "<",
            "threshold": 0.15, "data_field": "financials.roic_10yr_avg",
        },
        "qualitative_rule": None,
        "severity": "warning",
        "anti_scope": "本条不适用于银行、保险等结构性高杠杆行业",
        "rationale": "方法论要求资本回报率是业务质量的定量前置信号。",
        "evidence_strength": "direct_quote",
        "supporting_section_id": "[ref_1]",
        "supporting_profile_factor": "return_on_equity_without_leverage",
    }


class TestValidateSeed(unittest.TestCase):

    def test_good_seed_passes(self):
        ok, errs = validate_seed(_good_seed())
        self.assertTrue(ok, msg=f"errors: {errs}")

    def test_digit_in_claim_fails(self):
        s = _good_seed()
        s["qualitative_claim"] = "ROIC低于15%的公司标记不足"
        ok, errs = validate_seed(s)
        self.assertFalse(ok)
        self.assertTrue(any("digit" in e for e in errs))

    def test_compound_claim_fails(self):
        s = _good_seed()
        s["qualitative_claim"] = "既要求高回报率又要求低估值"
        ok, errs = validate_seed(s)
        self.assertFalse(ok)
        self.assertTrue(any("compound" in e for e in errs))

    def test_missing_anti_scope_fails(self):
        s = _good_seed()
        del s["anti_scope"]
        ok, errs = validate_seed(s)
        self.assertFalse(ok)

    def test_both_rules_null_fails(self):
        s = _good_seed()
        s["quantitative_rule"] = None
        s["qualitative_rule"] = None
        ok, errs = validate_seed(s)
        self.assertFalse(ok)

    def test_invalid_master_enum_fails(self):
        s = _good_seed()
        s["_master"] = "random_master"
        ok, errs = validate_seed(s)
        self.assertFalse(ok)

    def test_reintroduction_consistency(self):
        s = _good_seed()
        s["_reintroduced_from"] = "cl_26 (v1.0 dropped-archive)"
        # Missing other 3 reintro fields
        ok, errs = validate_seed(s)
        self.assertFalse(ok)
        # Now add all 3
        s["_reintroduction_rationale"] = "new section justifies re-intro"
        s["_reintroduced_seed_commit_hash"] = "a1b2c3d"
        s["_reintroduced_seed_section_id"] = "#new-section"
        ok, errs = validate_seed(s)
        self.assertTrue(ok, msg=f"errors: {errs}")

    def test_file_validation(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "seeds.jsonl"
            with p.open("w", encoding="utf-8") as f:
                for i in range(6):
                    s = _good_seed()
                    s["seed_id"] = f"seed_{i+1:02d}"
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
            summary = validate_seeds_file(str(p))
            self.assertTrue(summary["passed"])
            self.assertEqual(summary["total"], 6)
            self.assertEqual(summary["valid"], 6)

    def test_file_validation_fails_below_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "seeds.jsonl"
            with p.open("w", encoding="utf-8") as f:
                for i in range(3):  # below min=5
                    s = _good_seed()
                    s["seed_id"] = f"seed_{i+1:02d}"
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
            summary = validate_seeds_file(str(p))
            self.assertFalse(summary["passed"])


if __name__ == "__main__":
    unittest.main()
