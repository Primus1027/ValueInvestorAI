"""Archive — Phase F: move prep/ artifacts to Principles/history/{debate_id}/.

After a debate completes (whether successful or not), all intermediate artifacts
in `prep/` are moved (not copied) to `Principles/history/{debate_id}/prep/`
for permanent retention. This satisfies the user requirement that every debate
be a "precious historical document mirroring a real master's board meeting".

Also writes `debate_log.md` summarizing the debate.

Non-moved files (cumulative state, never archived):
- Principles/dropped-archive.md
- Principles/follow_up_agenda.md
- Principles/current.md
- Principles/monitoring.md
- prep/process_critique.jsonl (kept accumulating)
- prep/trigger_log.jsonl (kept accumulating)
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import PREP_DIR, HISTORY_DIR

# Files that are cumulative across debates — keep in prep/, don't archive.
CUMULATIVE_PREP_FILES = {
    "process_critique.jsonl",
    "trigger_log.jsonl",
    "last_debate_state.json",  # used by trigger_detector for T2/T3
}


def archive_debate(debate_id: str, prep_dir: Path = PREP_DIR,
                    history_root: Path = HISTORY_DIR,
                    stats: Optional[dict] = None) -> Path:
    """Move debate artifacts to history/{debate_id}/.

    Args:
        debate_id: e.g. "2026-04-21_manual"
        prep_dir: usually PREP_DIR
        history_root: usually HISTORY_DIR
        stats: optional dict with debate statistics for debate_log.md

    Returns:
        Path to archived directory.
    """
    archive_dir = history_root / debate_id
    archive_prep = archive_dir / "prep"
    archive_prep.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    skipped: list[str] = []
    if prep_dir.exists():
        for f in prep_dir.iterdir():
            if not f.is_file():
                continue
            if f.name in CUMULATIVE_PREP_FILES:
                skipped.append(f.name)
                continue
            dest = archive_prep / f.name
            shutil.move(str(f), str(dest))
            moved.append(f.name)

    # Write debate_log.md
    log_path = archive_dir / "debate_log.md"
    write_debate_log(debate_id, archive_dir, stats or {}, moved, skipped)

    return archive_dir


def write_debate_log(debate_id: str, archive_dir: Path,
                      stats: dict, moved_files: list[str],
                      skipped_files: list[str]) -> Path:
    """Write Markdown summary of this debate."""
    now = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Debate Log — {debate_id}",
        "",
        f"**Archived at**: {now}",
        f"**Trigger type**: {stats.get('trigger_type', 'unknown')}",
        f"**Debate mode**: {stats.get('debate_mode', 'unknown')}",
        f"**Outcome**: {stats.get('outcome', 'unknown')}",
        "",
        "## Key Statistics",
        "",
    ]

    for key in ("phase1_seed_counts", "phase2_pairs_total",
                "phase2_low_conf_count", "phase2_transitivity_violations",
                "phase2_5_action_counts", "phase2_75_disputes_count",
                "phase3a_cluster_counts", "phase3b_vote_results",
                "circuit_breaker"):
        if key in stats:
            lines.append(f"- **{key}**: {json.dumps(stats[key], ensure_ascii=False)}")
    lines.append("")

    if "version_published" in stats:
        lines.append(f"## Output Version")
        lines.append(f"- **Version**: {stats['version_published']}")
        lines.append(f"- **Published**: {stats.get('published', False)}")
        if stats.get("quarantine_path"):
            lines.append(f"- **Quarantine path**: {stats['quarantine_path']}")
            lines.append(f"- **Quarantine reasons**: {stats.get('quarantine_reasons', [])}")
        lines.append("")

    if moved_files:
        lines.append("## Archived prep/ files")
        for f in sorted(moved_files):
            lines.append(f"- `{f}`")
        lines.append("")

    if skipped_files:
        lines.append("## Kept in prep/ (cumulative)")
        for f in sorted(skipped_files):
            lines.append(f"- `{f}`")
        lines.append("")

    if stats.get("process_critique_entries"):
        lines.append("## Process Critique (for Primus v0.5 design review)")
        for c in stats["process_critique_entries"]:
            lines.append(f"- **{c.get('critique_type')}** by {c.get('master')}: {c.get('critique_content')[:120]}")
        lines.append("")

    if stats.get("transcripts"):
        lines.append("## Cross-Rebuttal Transcripts")
        for t in stats["transcripts"]:
            lines.append(f"- [{t}](./{t})")
        lines.append("")

    archive_dir.mkdir(parents=True, exist_ok=True)
    log_path = archive_dir / "debate_log.md"
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


def list_past_debate_ids(history_root: Path = HISTORY_DIR) -> list[str]:
    """List all past debate IDs in chronological order (by debate_id lexical sort)."""
    if not history_root.exists():
        return []
    ids = [d.name for d in history_root.iterdir() if d.is_dir()]
    # debate_id format 'YYYY-MM-DD_trigger' sorts chronologically
    return sorted(ids)
