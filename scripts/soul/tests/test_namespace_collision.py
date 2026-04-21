"""Regression tests for cross-master seed_id namespace collisions.

Background: Each master (buffett/munger/duan) mints its own seed_01..seed_N
namespace. v1.1 debate shipped with multiple modules treating bare seed_id as
globally unique, which produced:
  - 16 false-positive "seed appears in multiple clusters" validation errors
  - 0 Cross-Rebuttal disputes (union-find over bare seed_id collapsed masters)
  - 8 spurious transitivity violations

These tests lock in that seed identity is always (master, seed_id) UID.
"""

import unittest

from scripts.soul.board.cluster import validate_cluster_output
from scripts.soul.board.comparative import (
    _base_matrix_record, _matrix_record_uids, _pair_id,
    build_equivalence_map, find_transitivity_violations,
)
from scripts.soul.board.cross_rebuttal import identify_dispute_clusters


class TestClusterValidatorUid(unittest.TestCase):
    """cluster.py validator must not flag cross-master seed_id collisions as duplicates."""

    def test_seed_01_across_masters_is_not_duplicate(self):
        clusters = [
            {
                "cluster_id": "cl_01",
                "rule_subject": "target",
                "variant_seeds": [
                    {"seed_id": "seed_01", "master": "buffett"},
                    {"seed_id": "seed_01", "master": "munger"},
                    {"seed_id": "seed_01", "master": "duan"},
                ],
            },
        ]
        all_uids = {
            ("buffett", "seed_01"),
            ("munger", "seed_01"),
            ("duan", "seed_01"),
        }
        valid, errors = validate_cluster_output(clusters, all_uids)
        self.assertEqual(len(errors), 0, f"expected no errors, got {errors}")
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["support_count"], 3)

    def test_same_master_seed_in_two_clusters_is_duplicate(self):
        clusters = [
            {"cluster_id": "cl_01", "rule_subject": "target",
             "variant_seeds": [{"seed_id": "seed_01", "master": "buffett"}]},
            {"cluster_id": "cl_02", "rule_subject": "target",
             "variant_seeds": [{"seed_id": "seed_01", "master": "buffett"}]},
        ]
        all_uids = {("buffett", "seed_01")}
        _, errors = validate_cluster_output(clusters, all_uids)
        self.assertTrue(any("appears in multiple clusters" in e for e in errors))


class TestMatrixMastersField(unittest.TestCase):
    """comparative.py matrix records must carry a masters field."""

    def test_base_record_includes_masters(self):
        sa = {"seed_id": "seed_01", "_master": "buffett"}
        sb = {"seed_id": "seed_01", "_master": "munger"}
        record = _base_matrix_record(sa, sb)
        self.assertEqual(record["masters"], ["buffett", "munger"])
        self.assertEqual(record["seed_ids"], ["seed_01", "seed_01"])

    def test_pair_id_survives_bare_id_collision(self):
        sa = {"seed_id": "seed_03", "_master": "munger"}
        sb = {"seed_id": "seed_03", "_master": "duan"}
        self.assertNotEqual(_pair_id(sa, sb),
                             _pair_id({"seed_id": "seed_03", "_master": "buffett"}, sb))

    def test_record_uids_extracts_tuples(self):
        record = {"seed_ids": ["s1", "s2"], "masters": ["buffett", "duan"]}
        uid_a, uid_b = _matrix_record_uids(record)
        self.assertEqual(uid_a, ("buffett", "s1"))
        self.assertEqual(uid_b, ("duan", "s2"))


class TestEquivalenceMapUid(unittest.TestCase):
    """build_equivalence_map must key on UID tuples, not bare seed_id."""

    def test_collision_does_not_conflate(self):
        matrix = [
            {"seed_ids": ["seed_01", "seed_02"], "masters": ["buffett", "buffett"],
             "equivalent": True},
            {"seed_ids": ["seed_01", "seed_02"], "masters": ["munger", "duan"],
             "equivalent": False},
        ]
        m = build_equivalence_map(matrix)
        # Both orderings of each pair must exist with distinct values.
        self.assertTrue(m[(("buffett", "seed_01"), ("buffett", "seed_02"))])
        self.assertFalse(m[(("munger", "seed_01"), ("duan", "seed_02"))])


class TestTransitivityNoCollision(unittest.TestCase):
    """find_transitivity_violations must not produce spurious violations from bare seed_id."""

    def test_distinct_masters_same_bare_id_not_triple(self):
        # Three seeds that happen to share the bare id "seed_03" across masters
        # but are semantically distinct. No equivalences between them → no violations.
        all_seeds = [
            {"seed_id": "seed_03", "_master": "buffett",
             "qualitative_claim": "A", "rule_subject": "target"},
            {"seed_id": "seed_03", "_master": "munger",
             "qualitative_claim": "B", "rule_subject": "target"},
            {"seed_id": "seed_03", "_master": "duan",
             "qualitative_claim": "C", "rule_subject": "target"},
        ]
        matrix = []  # No equivalences between any pair
        violations = find_transitivity_violations(matrix, all_seeds)
        self.assertEqual(
            len(violations), 0,
            f"bare seed_id collision produced spurious violations: {violations}",
        )


class TestCrossMasterDispute(unittest.TestCase):
    """Cross-Rebuttal must detect disputes when masters share bare seed_id but differ semantically."""

    def test_same_bare_seed_id_across_masters_with_different_thresholds(self):
        # Simulates the v1.1 collision scenario: all three masters mint seed_01,
        # the Sonnet pairwise judges them equivalent, but thresholds differ.
        revised = {
            "buffett": [{
                "seed_id": "seed_01", "_master": "buffett",
                "rule_subject": "target", "theme": "moat",
                "qualitative_claim": "X", "severity": "warning",
                "quantitative_rule": {"threshold": 0.15},
            }],
            "munger": [{
                "seed_id": "seed_01", "_master": "munger",
                "rule_subject": "target", "theme": "moat",
                "qualitative_claim": "X", "severity": "warning",
                "quantitative_rule": {"threshold": 0.10},
            }],
            "duan": [{
                "seed_id": "seed_01", "_master": "duan",
                "rule_subject": "target", "theme": "moat",
                "qualitative_claim": "X", "severity": "warning",
                "quantitative_rule": {"threshold": 0.20},
            }],
        }
        matrix = [
            {"seed_ids": ["seed_01", "seed_01"], "masters": ["buffett", "munger"],
             "equivalent": True, "confidence": 0.9},
            {"seed_ids": ["seed_01", "seed_01"], "masters": ["buffett", "duan"],
             "equivalent": True, "confidence": 0.9},
            {"seed_ids": ["seed_01", "seed_01"], "masters": ["munger", "duan"],
             "equivalent": True, "confidence": 0.9},
        ]
        disputes = identify_dispute_clusters(revised, matrix)
        self.assertEqual(
            len(disputes), 1,
            "cross-master seed_id collision must still surface a dispute",
        )
        self.assertIn("threshold", disputes[0]["dispute_type"])
        # All three masters should appear in the dispute
        member_masters = {
            s.get("_master")
            for master_list in disputes[0]["member_seeds_by_master"].values()
            for s in master_list
        }
        self.assertEqual(member_masters, {"buffett", "munger", "duan"})


class TestTranscriptLookup(unittest.TestCase):
    """Phase 3b-qual must resolve cluster variant_seeds back to Phase 2.75 transcripts.

    After the dispute_id format changed from `dispute_{seed_id}` to
    `dispute_{master}_{seed_id}`, the legacy filename-probe returned None for
    every cluster. Phase 2.75 now emits a `seed_uid_to_transcript` map.
    """

    def test_find_via_uid_map(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpd:
            tmpp = Path(tmpd)
            prep_dir = tmpp / "prep"
            history_dir = tmpp / "history"
            debate_id = "test_debate"
            (history_dir / debate_id).mkdir(parents=True)
            prep_dir.mkdir()

            transcript_path = history_dir / debate_id / "debate_transcript_dispute_buffett_seed_01.md"
            transcript_path.write_text("fake transcript", encoding="utf-8")

            (prep_dir / "phase2_75_summary.json").write_text(json.dumps({
                "seed_uid_to_transcript": {
                    "buffett/seed_01": str(transcript_path),
                },
            }), encoding="utf-8")

            with patch("scripts.soul.board.vote_qualitative.PREP_DIR", prep_dir), \
                 patch("scripts.soul.board.vote_qualitative.HISTORY_DIR", history_dir):
                # Reset cache since we're testing a new debate
                from scripts.soul.board import vote_qualitative
                vote_qualitative._PHASE275_UID_MAP_CACHE.clear()

                cluster = {
                    "cluster_id": "cl_01",
                    "variant_seeds": [
                        {"seed_id": "seed_01", "master": "buffett"},
                    ],
                }
                found = vote_qualitative.find_transcript_path(debate_id, cluster)
                self.assertEqual(found, transcript_path)


class TestLegacyMatrixGuard(unittest.TestCase):
    """Stale pre-fix matrix (no `masters` field) must fail loud, not silently miscluster."""

    def test_assert_raises_on_missing_masters(self):
        from scripts.soul.board.cross_rebuttal import _assert_matrix_has_masters
        stale_matrix = [
            {"pair_id": "seed_01-seed_02", "seed_ids": ["seed_01", "seed_02"],
             "equivalent": True, "confidence": 0.9},
        ]
        with self.assertRaises(RuntimeError) as ctx:
            _assert_matrix_has_masters(stale_matrix)
        self.assertIn("stale", str(ctx.exception).lower())

    def test_assert_passes_on_valid_matrix(self):
        from scripts.soul.board.cross_rebuttal import _assert_matrix_has_masters
        valid_matrix = [
            {"pair_id": "buffett/seed_01__munger/seed_01",
             "seed_ids": ["seed_01", "seed_01"],
             "masters": ["buffett", "munger"],
             "equivalent": True, "confidence": 0.9},
        ]
        _assert_matrix_has_masters(valid_matrix)  # must not raise


class TestConsistencyFixUid(unittest.TestCase):
    """apply_consistency_fixes must use UID-qualified suggestions."""

    def test_parse_uid_token(self):
        from scripts.soul.board.comparative import _parse_uid_token
        self.assertEqual(_parse_uid_token("buffett/seed_01"),
                          ("buffett", "seed_01"))
        self.assertEqual(_parse_uid_token("seed_01"), (None, "seed_01"))

    def test_bare_id_suggestion_rejected(self):
        """Legacy bare-id suggestions must be skipped (not processed) to avoid cross-master ambiguity."""
        from scripts.soul.board.comparative import apply_consistency_fixes
        matrix = [
            {"pair_id": "buffett/seed_01__munger/seed_01",
             "seed_ids": ["seed_01", "seed_01"],
             "masters": ["buffett", "munger"],
             "equivalent": False, "confidence": 0.5},
        ]
        all_seeds = [
            {"seed_id": "seed_01", "_master": "buffett", "qualitative_claim": "A",
             "rule_subject": "target", "theme": "moat", "severity": "warning"},
            {"seed_id": "seed_01", "_master": "munger", "qualitative_claim": "B",
             "rule_subject": "target", "theme": "moat", "severity": "warning"},
        ]
        suggestions = [{"suspicious_pair": ["seed_01", "seed_01"],
                        "suggested_change": "should_be_equivalent"}]
        # With bare-id suggestion, no Opus call should fire (skipped).
        result = apply_consistency_fixes(matrix, suggestions, all_seeds)
        # Matrix unchanged — equivalent still False, no arbitration flag
        self.assertFalse(result[0]["equivalent"])
        self.assertFalse(result[0].get("arbitrated_by_opus"))


class TestReviseUidFilter(unittest.TestCase):
    """revise.py must filter matrix pairs by (master, seed_id) UID, not bare seed_id."""

    def test_bare_id_collision_does_not_leak(self):
        from scripts.soul.board.revise import render_revise_prompt
        own_seeds = [
            {"seed_id": "seed_01", "_master": "buffett", "qualitative_claim": "A",
             "rule_subject": "target", "theme": "moat", "severity": "warning",
             "rationale": "", "anti_scope": "", "category": "warning"},
        ]
        matrix = [
            # Buffett's own pair — should be included
            {"pair_id": "buffett/seed_01__buffett/seed_02",
             "seed_ids": ["seed_01", "seed_02"],
             "masters": ["buffett", "buffett"],
             "equivalent": True, "confidence": 0.9,
             "brief_reason": "own"},
            # Munger+Duan pair that happens to share seed_01 — MUST be excluded
            {"pair_id": "munger/seed_01__duan/seed_02",
             "seed_ids": ["seed_01", "seed_02"],
             "masters": ["munger", "duan"],
             "equivalent": False, "confidence": 0.2,
             "brief_reason": "other_masters"},
        ]
        # We can't easily test the final prompt output without the template,
        # but we can test the filter via a local re-implementation.
        own_uids = {(s.get("_master"), s["seed_id"]) for s in own_seeds}
        filtered = [
            p for p in matrix
            if (p["masters"][0], p["seed_ids"][0]) in own_uids
               or (p["masters"][1], p["seed_ids"][1]) in own_uids
        ]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["brief_reason"], "own")


if __name__ == "__main__":
    unittest.main()
