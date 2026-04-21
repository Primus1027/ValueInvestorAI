"""Tests for dropped_tracker and agenda_tracker."""

import tempfile
import unittest
from pathlib import Path

from scripts.soul.board.dropped_tracker import DroppedTracker, REINTRO_ANNUAL_QUOTA, REINTRO_COOLDOWN
from scripts.soul.board.agenda_tracker import AgendaTracker


class TestDroppedTracker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "dropped-archive.md"

    def test_three_drops_archives(self):
        dt = DroppedTracker(self.path)
        for i, did in enumerate(["2026-04", "2026-07", "2026-10"]):
            r = dt.record_drop("cl_26", did, 1, "claim", "self", "veto_line")
            if i < 2:
                self.assertFalse(r["is_archived"])
            else:
                self.assertTrue(r["is_archived"])
                self.assertTrue(r["newly_archived"])

    def test_roundtrip(self):
        dt = DroppedTracker(self.path)
        dt.record_drop("cl_1", "2026-01", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-02", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-03", 1, "a", "target", "cat")
        dt.save()
        dt2 = DroppedTracker(self.path)
        self.assertIn("cl_1", dt2.records)
        self.assertTrue(dt2.records["cl_1"].is_archived())

    def test_reintro_cooldown(self):
        dt = DroppedTracker(self.path)
        dt.record_drop("cl_1", "2026-01", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-02", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-03", 1, "a", "target", "cat")
        # Archived at 2026-03, need >= REINTRO_COOLDOWN debates since
        past = ["2026-01", "2026-02", "2026-03"]
        cands = dt.get_reintroduction_candidates("buffett", "2026-04", past)
        self.assertEqual(len(cands), 0)  # only 0 debates since archive
        past += ["2026-04", "2026-05", "2026-06", "2026-07"]
        cands = dt.get_reintroduction_candidates("buffett", "2026-08", past)
        self.assertGreaterEqual(len(cands), 1)  # 4 debates since archive

    def test_reintro_quota(self):
        dt = DroppedTracker(self.path)
        dt.record_drop("cl_1", "2026-01", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-02", 1, "a", "target", "cat")
        dt.record_drop("cl_1", "2026-03", 1, "a", "target", "cat")
        # Exhaust duan's quota
        for _ in range(REINTRO_ANNUAL_QUOTA):
            dt.record_reintroduction_attempt("cl_1", "duan", "2026-08")

        past = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05",
                "2026-06", "2026-07", "2026-08"]
        cands = dt.get_reintroduction_candidates("duan", "2026-09", past)
        self.assertEqual(len(cands), 0)
        # Buffett's quota still available
        cands_b = dt.get_reintroduction_candidates("buffett", "2026-09", past)
        self.assertGreaterEqual(len(cands_b), 1)


class TestAgendaTracker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "agenda.md"

    def test_add_quant_upgrade(self):
        at = AgendaTracker(self.path)
        item_id = at.add_quant_upgrade(
            "cl_10", 3, {"duan": 10, "munger": 5},
            {"duan": "full cycle", "munger": "balanced"},
            "holding period", "self", "2026-04-21")
        self.assertIsNotNone(item_id)
        self.assertEqual(at.active_count(), 1)

    def test_resolve(self):
        at = AgendaTracker(self.path)
        at.add_quant_upgrade("cl_1", 3, {"duan": 10}, {"duan": "r"}, "c", "self", "2026-01")
        at.resolve_item("cl_1", "quant_upgrade", "5", "2026-07", "new consensus")
        self.assertEqual(at.active_count(), 0)

    def test_stale_to_dormant(self):
        at = AgendaTracker(self.path)
        at.add_quant_upgrade("cl_1", 3, {"duan": 10}, {"duan": "r"}, "c", "self", "2026-01")
        # Simulate 4 quarters
        for _ in range(4):
            at.mark_stale_and_demote("q_next")
        # Should demote after 4 quarters
        self.assertEqual(at.active_count(), 0)
        dormant = [v for v in at.items.values() if v.status == "dormant"]
        self.assertEqual(len(dormant), 1)


if __name__ == "__main__":
    unittest.main()
