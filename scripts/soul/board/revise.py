"""Phase 2.5: Revise round.

Each master sees Phase 2 comparative analysis (matrix + transcripts) and
decides for each of their own seeds: keep / modify / withdraw / new.

Also optionally submits process_critique entries (Primus reads these to
inform v0.5 design; does NOT affect this round's voting).

Timeout: 900s per master + 2 retries.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, MASTERS, master_display_name,
)
from scripts.soul.validate_seed import validate_seed

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

PHASE_2_5_TIMEOUT = 900  # 15 minutes
PHASE_2_5_MAX_RETRIES = 2


def load_own_sanitized_seeds(master: str) -> list[dict]:
    """Load seeds for this master from Phase 1.5 output."""
    p = PREP_DIR / f"phase1_5_{master}_sanitized.jsonl"
    if not p.exists():
        return []
    out = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                s = json.loads(line)
                if s.get("_master") == master:
                    out.append(s)
            except json.JSONDecodeError:
                continue
    return out


def load_phase2_matrix() -> list[dict]:
    """Load the final equivalence matrix from Phase 2."""
    p = PREP_DIR / "phase2_final_matrix.jsonl"
    if not p.exists():
        return []
    out = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def render_revise_prompt(master: str, own_seeds: list[dict],
                           phase2_matrix: list[dict]) -> str:
    """Fill phase2_5_revise.md template."""
    template = (PROMPTS_DIR / "phase2_5_revise.md").read_text(encoding="utf-8")
    # Compact Phase 2 analysis: only entries involving this master's seeds
    own_seed_ids = {s["seed_id"] for s in own_seeds}
    relevant_pairs = [
        p for p in phase2_matrix
        if any(sid in own_seed_ids for sid in p.get("seed_ids", []))
    ]
    # Keep it compact — strip long fields
    compact = []
    for p in relevant_pairs[:100]:  # cap to 100 entries
        compact.append({
            "pair_id": p.get("pair_id"),
            "seed_ids": p.get("seed_ids"),
            "equivalent": p.get("equivalent"),
            "confidence": p.get("confidence"),
            "brief_reason": p.get("brief_reason", "")[:100],
            "arbitrated_by_opus": p.get("arbitrated_by_opus", False),
        })

    return template.format(
        master=master,
        master_display_name=master_display_name(master),
        own_seeds=json.dumps(own_seeds, ensure_ascii=False, indent=2),
        phase2_analysis=json.dumps(compact, ensure_ascii=False, indent=2),
    )


def call_revise_for_master(master: str, own_seeds: list[dict],
                             phase2_matrix: list[dict],
                             timeout: int = PHASE_2_5_TIMEOUT) -> tuple[Optional[dict], dict]:
    """Call Sonnet for this master's revision. Returns (parsed_result, meta)."""
    prompt = render_revise_prompt(master, own_seeds, phase2_matrix)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=timeout, text=True,
        )
        if res.returncode != 0:
            return None, {"error": f"exit {res.returncode}",
                          "stderr_head": res.stderr[:200]}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["revisions", "new_seeds",
                                                         "process_critique"])
        if not parsed:
            return None, {"error": "parse_fail"}
        return parsed, {"returncode": 0}
    except subprocess.TimeoutExpired:
        return None, {"error": "timeout", "timeout_seconds": timeout}
    except Exception as e:
        return None, {"error": str(e)}


def revise_for_master(master: str, own_seeds: list[dict],
                       phase2_matrix: list[dict]) -> dict:
    """Run Phase 2.5 for one master, with retry and fallback.

    Fallback: if all retries fail, keep all original seeds (action=keep for each,
    rationale marks fallback).
    """
    attempts = []
    parsed = None
    for attempt_idx in range(PHASE_2_5_MAX_RETRIES + 1):
        parsed, meta = call_revise_for_master(master, own_seeds, phase2_matrix)
        attempts.append({"attempt": attempt_idx, **meta})
        if parsed is not None:
            break

    if parsed is None:
        # Fallback: keep all
        fallback_revisions = [
            {"seed_id": s["seed_id"], "action": "keep",
             "rationale": "Phase 2.5 call failed; preserved original seed as fallback.",
             "modified_seed": None}
            for s in own_seeds
        ]
        parsed = {
            "revisions": fallback_revisions,
            "new_seeds": [],
            "process_critique": [],
            "_fallback_used": True,
            "error": "All retries failed",
        }

    # Build final seeds post-revision
    final_seeds = []
    revised_seed_ids = set()
    for rev in parsed.get("revisions", []):
        seed_id = rev.get("seed_id")
        action = rev.get("action", "keep")
        revised_seed_ids.add(seed_id)
        orig = next((s for s in own_seeds if s.get("seed_id") == seed_id), None)
        if orig is None:
            continue
        if action == "withdraw":
            continue
        elif action == "modify":
            modified = rev.get("modified_seed")
            if isinstance(modified, dict):
                modified["_master"] = master
                modified["_revise_action"] = "modify"
                modified["_revise_rationale"] = rev.get("rationale", "")
                # Validate; if invalid, fall back to keep
                ok, errs = validate_seed(modified, strict=True)
                if ok:
                    final_seeds.append(modified)
                else:
                    orig_copy = dict(orig)
                    orig_copy["_revise_action"] = "keep_due_to_modify_invalid"
                    orig_copy["_modify_errors"] = errs
                    final_seeds.append(orig_copy)
                continue
        # keep
        orig_copy = dict(orig)
        orig_copy["_revise_action"] = "keep"
        orig_copy["_revise_rationale"] = rev.get("rationale", "")
        final_seeds.append(orig_copy)

    # Also include seeds that weren't mentioned in revisions (defensive keep)
    for s in own_seeds:
        if s["seed_id"] not in revised_seed_ids:
            s_copy = dict(s)
            s_copy["_revise_action"] = "keep"
            s_copy["_revise_rationale"] = "(not mentioned in revisions, default keep)"
            final_seeds.append(s_copy)

    # Append new seeds
    for idx, new_seed in enumerate(parsed.get("new_seeds", []) or []):
        if not isinstance(new_seed, dict):
            continue
        new_seed["_master"] = master
        new_seed["_revise_action"] = "new"
        # Assign seed_id if missing
        if not new_seed.get("seed_id"):
            new_seed["seed_id"] = f"seed_new_{idx+1:02d}"
        ok, errs = validate_seed(new_seed, strict=True)
        if ok:
            final_seeds.append(new_seed)

    # Write output
    out_path = PREP_DIR / f"phase2_5_{master}_revised_seeds.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for s in final_seeds:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Revisions log
    log_path = PREP_DIR / f"phase2_5_{master}_revisions.json"
    log_path.write_text(
        json.dumps({
            "master": master,
            "revisions": parsed.get("revisions", []),
            "new_seeds": parsed.get("new_seeds", []),
            "process_critique": parsed.get("process_critique", []),
            "_fallback_used": parsed.get("_fallback_used", False),
            "attempts": attempts,
            "error": parsed.get("error"),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Write process_critique to per-master file (avoid concurrent-append
    # corruption). Orchestrator/archive aggregates these into the global
    # process_critique.jsonl at the end of the debate.
    critique_entries = parsed.get("process_critique") or []
    if critique_entries:
        cpath = PREP_DIR / f"process_critique_{master}.jsonl"
        with cpath.open("w", encoding="utf-8") as f:
            for c in critique_entries:
                if isinstance(c, dict):
                    c["_master"] = master
                    c["_debate_id_emitted"] = datetime.now().isoformat(timespec="seconds")
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")

    return {
        "master": master,
        "final_seed_count": len(final_seeds),
        "action_counts": _count_actions(final_seeds),
        "fallback_used": parsed.get("_fallback_used", False),
        "process_critique_count": len(critique_entries),
        "output_path": str(out_path),
        "attempts": attempts,
    }


def _count_actions(seeds: list[dict]) -> dict:
    counts = {"keep": 0, "modify": 0, "new": 0, "keep_due_to_modify_invalid": 0}
    for s in seeds:
        act = s.get("_revise_action", "keep")
        counts[act] = counts.get(act, 0) + 1
    return counts


def revise_parallel() -> dict:
    """Run Phase 2.5 for all 3 masters in parallel."""
    phase2_matrix = load_phase2_matrix()

    own_seeds_by_master = {m: load_own_sanitized_seeds(m) for m in MASTERS}

    results: dict = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(revise_for_master, m, own_seeds_by_master[m], phase2_matrix): m
            for m in MASTERS
        }
        for fut in futures:
            master = futures[fut]
            try:
                results[master] = fut.result(timeout=PHASE_2_5_TIMEOUT + 60)
            except Exception as e:
                results[master] = {"master": master, "error": str(e)}

    fallback_count = sum(1 for r in results.values() if r.get("fallback_used"))
    summary = {
        "results_by_master": results,
        "fallback_count": fallback_count,
        "partial_failure": fallback_count >= 2,  # 2+ fallbacks → debate unhealthy
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    summary_path = PREP_DIR / "phase2_5_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
