"""Tests for Phase 3c circuit breaker."""

import tempfile
import unittest
from pathlib import Path

from scripts.soul.board.render import circuit_breaker, count_hard_in_md, count_veto_in_md


class TestCircuitBreaker(unittest.TestCase):

    def _prev_file(self, content: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        p = tmp / "v_prev.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_healthy_new_version_passes(self):
        prev = self._prev_file(
            "### 1. X\n- Severity: `veto`\n\n"
            "### 2. Y\n- Severity: `warning`\n\n"
            "### 3. Z\n- Severity: `warning`\n\n"
            "### 4. W\n- Severity: `warning`\n",
        )
        new_clusters = [
            {"_render_level": "L1", "_layer0_severity": "veto"},
            {"_render_level": "L1", "_layer0_severity": "warning"},
            {"_render_level": "L2", "_layer0_severity": "warning"},
        ]
        cb = circuit_breaker(new_clusters, "", prev, 0)
        self.assertTrue(cb["all_pass"])

    def test_regression_guard_blocks_too_few_hard(self):
        prev = self._prev_file(
            "### 1. A\n- Severity: `veto`\n"
            "### 2. B\n- Severity: `veto`\n"
            "### 3. C\n- Severity: `veto`\n"
            "### 4. D\n- Severity: `veto`\n",
        )
        new_clusters = [{"_render_level": "L1", "_layer0_severity": "veto"}]
        cb = circuit_breaker(new_clusters, "", prev, 0)
        self.assertFalse(cb["all_pass"])
        self.assertFalse(cb["regression_guard"]["pass"])

    def test_drift_guard_blocks_severity_softening(self):
        prev = self._prev_file(
            "### 1. A\n- Severity: `veto`\n"
            "### 2. B\n- Severity: `veto`\n"
            "### 3. C\n- Severity: `veto`\n"
            "### 4. D\n- Severity: `veto`\n",
        )
        # New: same HARD count but all warning now
        new_clusters = [
            {"_render_level": "L1", "_layer0_severity": "warning"},
            {"_render_level": "L1", "_layer0_severity": "warning"},
            {"_render_level": "L1", "_layer0_severity": "warning"},
            {"_render_level": "L2", "_layer0_severity": "warning"},
        ]
        cb = circuit_breaker(new_clusters, "", prev, 0)
        self.assertFalse(cb["all_pass"])
        self.assertFalse(cb["drift_guard"]["pass"])

    def test_health_check_blocks_2_fallbacks(self):
        prev = self._prev_file("### 1. A\n- Severity: `warning`\n")
        new_clusters = [{"_render_level": "L1", "_layer0_severity": "warning"}]
        cb = circuit_breaker(new_clusters, "", prev, 2)
        self.assertFalse(cb["all_pass"])
        self.assertFalse(cb["health_check"]["pass"])

    def test_count_helpers(self):
        md = "### 1. A\n- Severity: `veto`\n### 2. B\n- Severity: `warning`\n"
        self.assertEqual(count_hard_in_md(md), 2)
        self.assertEqual(count_veto_in_md(md), 1)


if __name__ == "__main__":
    unittest.main()
