"""DroppedTracker — manages Principles/dropped-archive.md state.

Handles:
- 3-round sliding window (a cluster must fail 3 consecutive debates to be archived)
- Re-introduction cooldown (4 debates after archival before a master can re-intro)
- Per-master annual quota (max 6 re-introductions per master per year)

File format (YAML frontmatter + Markdown body):

---
dropped_clusters:
  - cluster_id: cl_26
    canonical_claim: "..."
    rule_subject: self
    category: veto_line
    first_dropped_at: "2026-04-20_initial"
    _drop_history:
      - debate_id: "2026-04-20_initial"
        support_count: 1
    _archived_at_debate_id: null  # or debate_id string
    _reintro_count_by_master_year:
      "2026":
        duan: 2
        buffett: 0
        munger: 0
---

# Human-readable body (auto-generated)
...
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import PRINCIPLES_DIR


def _extract_year_from_debate_id(debate_id: str) -> str:
    """Extract a 4-digit year from debate_id. Falls back to current year.

    Supports formats like:
    - "2026-04-21_manual"       → "2026"
    - "test-2026-01-01"          → "2026"
    - "manual"                   → current year
    """
    m = re.search(r"(\d{4})", debate_id or "")
    if m:
        return m.group(1)
    return str(datetime.now().year)

DEFAULT_ARCHIVE_PATH = PRINCIPLES_DIR / "dropped-archive.md"

DROP_WINDOW_SIZE = 3          # consecutive drops required to archive
REINTRO_COOLDOWN = 4          # debates after archive before re-intro allowed
REINTRO_ANNUAL_QUOTA = 6      # max re-intros per master per year


@dataclass
class DroppedClusterRecord:
    cluster_id: str
    canonical_claim: str
    rule_subject: str
    category: str
    first_dropped_at: str
    _drop_history: list[dict] = field(default_factory=list)
    _archived_at_debate_id: Optional[str] = None
    _reintro_count_by_master_year: dict[str, dict[str, int]] = field(default_factory=dict)
    _soul_doc_snapshot: Optional[dict] = None  # master → commit hash at drop time

    def is_archived(self) -> bool:
        return self._archived_at_debate_id is not None

    def consecutive_drops(self) -> int:
        """Count of drops in the sliding window (excludes re-intro failures).

        Per v0.4.1 §5.5, re-introduction failures go back to archive directly
        and MUST NOT count toward the 3-round sliding window.
        """
        return sum(1 for h in self._drop_history if not h.get("_reintro_failed"))


class DroppedTracker:
    def __init__(self, archive_path: Path = DEFAULT_ARCHIVE_PATH):
        self.archive_path = archive_path
        self.records: dict[str, DroppedClusterRecord] = {}
        self._lock = threading.Lock()  # guards mutations for concurrent Phase 1
        self._load()

    # ─── Persistence ───

    def _load(self) -> None:
        if not self.archive_path.exists():
            self.records = {}
            return
        text = self.archive_path.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not frontmatter_match:
            self.records = {}
            return
        yaml_text = frontmatter_match.group(1)
        data = self._parse_simple_yaml(yaml_text)
        clusters_data = data.get("dropped_clusters", [])
        if not isinstance(clusters_data, list):
            self.records = {}
            return
        for c in clusters_data:
            if not isinstance(c, dict) or "cluster_id" not in c:
                continue
            rec = DroppedClusterRecord(
                cluster_id=c.get("cluster_id", ""),
                canonical_claim=c.get("canonical_claim", ""),
                rule_subject=c.get("rule_subject", "target"),
                category=c.get("category", "quantitative_hard"),
                first_dropped_at=c.get("first_dropped_at", ""),
                _drop_history=c.get("_drop_history") or [],
                _archived_at_debate_id=c.get("_archived_at_debate_id"),
                _reintro_count_by_master_year=c.get("_reintro_count_by_master_year") or {},
                _soul_doc_snapshot=c.get("_soul_doc_snapshot"),
            )
            self.records[rec.cluster_id] = rec

    def _parse_simple_yaml(self, text: str) -> dict:
        """Parse our own YAML — we write it as JSON directly, so just parse as JSON.

        For robustness, also attempt real yaml if available.
        """
        text = text.strip()
        # Our writer emits a full JSON object (starts with { and ends with })
        try:
            return json.loads(text)
        except Exception:
            pass
        # If someone wrote it without braces (plain key:value pairs), try wrapping
        try:
            return json.loads("{" + text.replace("\n", " ") + "}")
        except Exception:
            pass
        # Fall through to yaml module if installed
        try:
            import yaml  # type: ignore
            return yaml.safe_load(text) or {}
        except Exception:
            return {}

    def save(self) -> None:
        """Write archive file."""
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = self._serialize_frontmatter()
        body = self._render_body()
        full = f"---\n{frontmatter}\n---\n\n{body}"
        self.archive_path.write_text(full, encoding="utf-8")

    def _serialize_frontmatter(self) -> str:
        """Serialize as YAML-compatible JSON (readable + parseable)."""
        data = {
            "dropped_clusters": [asdict(r) for r in self.records.values()]
        }
        # Write as JSON for maximal roundtrip safety
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _render_body(self) -> str:
        """Human-readable Markdown body."""
        lines = ["# Dropped Archive", "",
                 f"> Auto-generated by `board/dropped_tracker.py`",
                 f"> Last updated: {datetime.now().isoformat(timespec='seconds')}",
                 "",
                 f"Total dropped clusters: {len(self.records)}",
                 f"Archived (3+ consecutive drops): {sum(1 for r in self.records.values() if r.is_archived())}",
                 "",
                 "---", ""]
        for rec in sorted(self.records.values(), key=lambda r: r.cluster_id):
            lines.append(f"## {rec.cluster_id} — {rec.canonical_claim[:60]}...")
            lines.append(f"- **rule_subject**: {rec.rule_subject}")
            lines.append(f"- **category**: {rec.category}")
            lines.append(f"- **first_dropped_at**: {rec.first_dropped_at}")
            lines.append(f"- **consecutive_drops**: {rec.consecutive_drops()}")
            lines.append(f"- **archived**: {'yes (' + (rec._archived_at_debate_id or '') + ')' if rec.is_archived() else 'no'}")
            if rec._drop_history:
                lines.append("- **drop_history**:")
                for h in rec._drop_history:
                    lines.append(f"  - {h.get('debate_id')}: support={h.get('support_count')}")
            lines.append("")
        return "\n".join(lines)

    # ─── Core operations ───

    def record_drop(self, cluster_id: str, debate_id: str, support_count: int,
                    canonical_claim: str, rule_subject: str,
                    category: str = "quantitative_hard",
                    soul_doc_snapshot: Optional[dict] = None) -> dict:
        """Record a drop event. Returns status dict including whether it became archived."""
        now_iso = datetime.now().isoformat(timespec="seconds")

        with self._lock:
            if cluster_id not in self.records:
                self.records[cluster_id] = DroppedClusterRecord(
                    cluster_id=cluster_id,
                    canonical_claim=canonical_claim,
                    rule_subject=rule_subject,
                    category=category,
                    first_dropped_at=debate_id,
                    _soul_doc_snapshot=soul_doc_snapshot,
                )

            rec = self.records[cluster_id]
            # Append to history (but skip duplicate same-debate entries)
            if not rec._drop_history or rec._drop_history[-1].get("debate_id") != debate_id:
                rec._drop_history.append({"debate_id": debate_id, "support_count": support_count})

            newly_archived = False
            if not rec.is_archived() and rec.consecutive_drops() >= DROP_WINDOW_SIZE:
                rec._archived_at_debate_id = debate_id
                newly_archived = True

            return {
                "cluster_id": cluster_id,
                "consecutive_drops": rec.consecutive_drops(),
                "is_archived": rec.is_archived(),
                "newly_archived": newly_archived,
                "recorded_at": now_iso,
            }

    def record_reintroduction_attempt(self, cluster_id: str, master: str,
                                       debate_id: str) -> None:
        """Called when a master re-introduces a cluster in Phase 1."""
        if cluster_id not in self.records:
            return
        rec = self.records[cluster_id]
        year = _extract_year_from_debate_id(debate_id)
        with self._lock:
            year_counts = rec._reintro_count_by_master_year.setdefault(year, {})
            year_counts[master] = year_counts.get(master, 0) + 1

    def record_reintroduction_failure(self, cluster_id: str, debate_id: str,
                                       support_count: int) -> None:
        """If re-introduction failed (< 2/3 support), go straight back to archive.

        Per v0.4.1 §5.5: re-introduced-and-failed does NOT re-enter sliding window.
        """
        if cluster_id not in self.records:
            return
        rec = self.records[cluster_id]
        # Log this attempt in history for audit
        rec._drop_history.append({
            "debate_id": debate_id,
            "support_count": support_count,
            "_reintro_failed": True,
        })
        # Ensure it stays archived
        if not rec.is_archived():
            rec._archived_at_debate_id = debate_id

    def promote_from_dropped(self, cluster_id: str) -> None:
        """Called when a cluster passes (>= 2/3) in Phase 3b-qual — remove from archive."""
        if cluster_id in self.records:
            del self.records[cluster_id]

    # ─── Re-introduction candidate logic ───

    def get_reintroduction_candidates(self, master: str, current_debate_id: str,
                                       all_past_debate_ids: list[str]) -> list[dict]:
        """Return list of clusters this master can re-introduce.

        Filters applied:
        - cluster must be archived (3+ consecutive drops)
        - cooldown: N debates (4) must have passed since archival
        - quota: master's annual count < REINTRO_ANNUAL_QUOTA
        """
        candidates: list[dict] = []
        current_year = current_debate_id[:4] if len(current_debate_id) >= 4 and current_debate_id[:4].isdigit() else str(datetime.now().year)

        for rec in self.records.values():
            if not rec.is_archived():
                continue

            # Cooldown check: how many debates since archive?
            if not rec._archived_at_debate_id:
                continue
            if rec._archived_at_debate_id not in all_past_debate_ids:
                # archive debate not yet in past_debates list — conservatively skip
                continue
            archive_index = all_past_debate_ids.index(rec._archived_at_debate_id)
            # all_past_debate_ids includes the archive debate; current_debate_id is not in this list yet
            debates_since_archive = len(all_past_debate_ids) - 1 - archive_index
            if debates_since_archive < REINTRO_COOLDOWN:
                continue

            # Quota check
            year_counts = rec._reintro_count_by_master_year.get(current_year, {})
            master_count = year_counts.get(master, 0)
            if master_count >= REINTRO_ANNUAL_QUOTA:
                continue

            candidates.append({
                "cluster_id": rec.cluster_id,
                "canonical_claim": rec.canonical_claim,
                "rule_subject": rec.rule_subject,
                "category": rec.category,
                "first_dropped_at": rec.first_dropped_at,
                "archived_at": rec._archived_at_debate_id,
                "soul_doc_snapshot": rec._soul_doc_snapshot,
                "debates_since_archive": debates_since_archive,
                "master_annual_count": master_count,
                "remaining_quota": REINTRO_ANNUAL_QUOTA - master_count,
            })

        return candidates

    def is_archived(self, cluster_id: str) -> bool:
        rec = self.records.get(cluster_id)
        return rec is not None and rec.is_archived()
