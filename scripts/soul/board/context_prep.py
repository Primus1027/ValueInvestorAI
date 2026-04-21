"""Phase 0: Context preparation.

Steps:
1. Load/refresh soul_index via existing build_soul_index.py
2. Auto-identify priority sections per master (Sonnet call)
3. Read current Principles, follow_up_agenda, dropped-archive
4. Compute re-introduction candidates per master (subject to cooldown + quota)
5. Package everything into a context dict + write prep/context_{debate_id}.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PRINCIPLES_DIR, PROMPTS_DIR, MASTERS,
    master_display_name,
)
from scripts.soul.board.dropped_tracker import DroppedTracker
from scripts.soul.board.agenda_tracker import AgendaTracker
from scripts.soul.board.archive import list_past_debate_ids

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

PROFILES_DIR = PROJECT_ROOT / "src" / "souls" / "profiles"

# How many priority sections to flag per master
PRIORITY_SECTIONS_PER_MASTER = 5
PRIORITY_IDENTIFY_TIMEOUT = 120  # seconds


# ─────────────────── soul_index loading ───────────────────

def ensure_soul_index_fresh(force: bool = False) -> dict:
    """Run build_soul_index.py if output missing or force=True. Return loaded index."""
    idx_path = PREP_DIR / "soul_index.json"
    if force or not idx_path.exists():
        print(f"[context_prep] Running build_soul_index.py ...")
        result = subprocess.run(
            ["python3", "-m", "scripts.soul.build_soul_index"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"build_soul_index failed: stderr={result.stderr[:500]}"
            )
    return json.loads(idx_path.read_text(encoding="utf-8"))


def load_toc_for_master(master: str) -> dict:
    """Load prep/soul_prompt_toc_{master}.json produced by build_soul_index."""
    path = PREP_DIR / f"soul_prompt_toc_{master}.json"
    if not path.exists():
        return {"master": master, "toc_sections": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(master: str) -> dict:
    """Load src/souls/profiles/{master}.json."""
    path = PROFILES_DIR / f"{master}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ───────────────── priority section auto-identification ─────────────────

def identify_priority_sections_via_sonnet(master: str, toc: dict,
                                            profile: dict) -> list[str]:
    """Ask Sonnet to pick the N most central section_ids for the master's methodology.

    Returns list of section_ids. On failure, falls back to top-N by char_count.
    """
    toc_compact = [
        {"section_id": s["section_id"], "title": s["title"],
         "keywords": s.get("keywords", [])[:5], "char_count": s.get("char_count", 0)}
        for s in toc.get("toc_sections", [])
    ]
    if not toc_compact:
        return []

    prompt = f"""你是方法论节选员。请从以下 TOC 中挑选对 {master_display_name(master)} 方法论最核心的 {PRIORITY_SECTIONS_PER_MASTER} 个 sections。

判断标准：
1. 与 profile.json 中的 factor 对应（优先选覆盖最重要 factor 的 section）
2. 内容密度高（char_count 较大）
3. 避免总览/目录类 section

==== Profile Factors ====
{json.dumps(list(profile.get('factors', profile).keys())[:20] if isinstance(profile, dict) else [], ensure_ascii=False)}

==== TOC ====
{json.dumps(toc_compact[:60], ensure_ascii=False, indent=2)}

输出仅 JSON（不要 markdown fence）:

{{"priority_section_ids": ["<id1>", "<id2>", ...]}}
"""

    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=PRIORITY_IDENTIFY_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            raise RuntimeError(f"claude CLI exit {res.returncode}: {res.stderr[:200]}")
        parsed = parse_claude_cli_result(res.stdout, expected_keys=["priority_section_ids"])
        if parsed and isinstance(parsed.get("priority_section_ids"), list):
            ids = parsed["priority_section_ids"][:PRIORITY_SECTIONS_PER_MASTER]
            # Validate against toc
            valid_ids = {s["section_id"] for s in toc_compact}
            return [i for i in ids if i in valid_ids]
    except Exception as e:
        print(f"[context_prep] priority identification for {master} failed: {e}; "
              f"falling back to top-N by char_count")

    # Fallback: top-N by char_count
    sorted_by_chars = sorted(toc_compact, key=lambda s: s.get("char_count", 0), reverse=True)
    return [s["section_id"] for s in sorted_by_chars[:PRIORITY_SECTIONS_PER_MASTER]]


def load_priority_sections_text(master: str, priority_ids: list[str],
                                  soul_index: dict) -> str:
    """Return concatenated full text of priority sections (for Phase 1 prompt)."""
    master_doc = soul_index.get("docs", {}).get(master, {})
    sections_by_id = {s["section_id"]: s for s in master_doc.get("sections", [])}
    parts = []
    for sid in priority_ids:
        sec = sections_by_id.get(sid)
        if not sec:
            continue
        parts.append(f"## {sec['title']}\n\n{sec.get('text', '')}\n")
    return "\n".join(parts)


# ───────────────── current principles / agenda loading ─────────────────

def load_current_principles() -> dict:
    """Read Principles/current.md (symlink). Returns {} if none."""
    current_md = PRINCIPLES_DIR / "current.md"
    current_schema = PRINCIPLES_DIR / "current.schema.json"
    result = {"md_path": None, "schema_path": None, "hard_count": 0, "md_text": ""}

    if current_md.exists():
        result["md_path"] = str(current_md.resolve())
        result["md_text"] = current_md.read_text(encoding="utf-8")
        # Rough count of HARD sections by heading pattern
        result["hard_count"] = result["md_text"].count("\n### ")

    if current_schema.exists():
        result["schema_path"] = str(current_schema.resolve())
        try:
            result["schema"] = json.loads(current_schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    return result


# ───────────────── Main entry ─────────────────

def prepare_context(debate_id: str, debate_mode: str = "full",
                    scope: Optional[list[str]] = None,
                    refresh_soul_index: bool = False) -> dict:
    """Phase 0 entry point. Returns context dict.

    Args:
        debate_id: unique id e.g. "2026-04-21_manual"
        debate_mode: "full" | "mini"
        scope: for mini debates, list of cluster_ids or seed_ids to limit Phase 1
        refresh_soul_index: force rebuild of prep/soul_index.json

    Writes prep/context_{debate_id}.json with the full context.
    """
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    soul_index = ensure_soul_index_fresh(force=refresh_soul_index)

    past_debates = list_past_debate_ids()
    dt = DroppedTracker()
    at = AgendaTracker()

    masters_ctx = {}
    for m in MASTERS:
        toc = load_toc_for_master(m)
        profile = load_profile(m)

        priority_ids = identify_priority_sections_via_sonnet(m, toc, profile)
        priority_text = load_priority_sections_text(m, priority_ids, soul_index)

        reintro_candidates = dt.get_reintroduction_candidates(m, debate_id, past_debates)

        masters_ctx[m] = {
            "profile": profile,
            "toc": toc,
            "priority_section_ids": priority_ids,
            "priority_sections_text": priority_text,
            "priority_sections_chars": len(priority_text),
            "reintro_candidates": reintro_candidates,
        }

    current = load_current_principles()

    agenda_items = at.get_mini_debate_input() if debate_mode == "mini" else []

    context = {
        "debate_id": debate_id,
        "debate_mode": debate_mode,
        "scope": scope,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "masters": masters_ctx,
        "current_principles": current,
        "follow_up_agenda_active": at.active_count(),
        "follow_up_agenda_items_for_mini": agenda_items,
        "past_debate_ids": past_debates,
    }

    out_path = PREP_DIR / f"context_{debate_id}.json"
    out_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[context_prep] Context written to {out_path} "
          f"({out_path.stat().st_size // 1024} KB)")
    return context


# ───────────────── CLI ─────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Phase 0: Context preparation")
    ap.add_argument("--debate-id", required=True)
    ap.add_argument("--mode", choices=["full", "mini"], default="full")
    ap.add_argument("--refresh-index", action="store_true")
    args = ap.parse_args()

    context = prepare_context(args.debate_id, debate_mode=args.mode,
                                refresh_soul_index=args.refresh_index)
    print(f"\nDebate ID: {context['debate_id']}")
    print(f"Mode: {context['debate_mode']}")
    for m, mctx in context["masters"].items():
        print(f"  {m}: {len(mctx['priority_section_ids'])} priority sections "
              f"({mctx['priority_sections_chars']} chars), "
              f"{len(mctx['reintro_candidates'])} reintro candidates")


if __name__ == "__main__":
    main()
