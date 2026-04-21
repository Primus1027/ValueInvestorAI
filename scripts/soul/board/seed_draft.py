"""Phase 1: Three-way parallel seed drafting.

For each master (buffett / munger / duan), run a Sonnet call to produce 5-20
structured seed principles.

Key requirements:
- Strict schema enforcement via validate_seed
- Minimum 5 valid seeds per master (retry 2x on failure)
- Fallback to v{N-1} HARD if retries exhausted
- Debate marked partial_failure if >= 2 masters fall back
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, MASTERS, master_display_name,
)
from scripts.soul.board.dropped_tracker import DroppedTracker
from scripts.soul.validate_seed import validate_seed

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

PHASE1_TIMEOUT = 900  # 15 minutes per master (Claude CLI + ~333KB context can take 8-10min)
MIN_VALID_SEEDS = 5
MAX_RETRIES = 2


# ─── Prompt rendering ───

def render_phase1_prompt(master: str, master_ctx: dict, debate_id: str,
                          debate_mode: str, strict_retry: bool = False) -> str:
    """Fill in the phase1_seed_draft.md template."""
    template_path = PROMPTS_DIR / "phase1_seed_draft.md"
    template = template_path.read_text(encoding="utf-8")

    reintro_candidates = master_ctx.get("reintro_candidates", [])
    reintro_display = "(无)"
    if reintro_candidates:
        reintro_display = json.dumps([
            {
                "cluster_id": c["cluster_id"],
                "canonical_claim": c["canonical_claim"],
                "rule_subject": c["rule_subject"],
                "archived_at": c.get("archived_at"),
                "remaining_quota": c.get("remaining_quota"),
            }
            for c in reintro_candidates[:10]
        ], ensure_ascii=False, indent=2)

    # TOC summary — compact list of (section_id, title)
    toc = master_ctx.get("toc", {}).get("toc_sections", [])
    toc_summary_lines = []
    for s in toc[:80]:  # cap to prevent prompt bloat
        toc_summary_lines.append(f"- [{s['section_id']}] {s['title']}")
    toc_summary = "\n".join(toc_summary_lines) if toc_summary_lines else "(无)"

    # Profile JSON compact
    profile = master_ctx.get("profile", {})
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
    # Cap to avoid prompt bloat (11KB → target ~5KB)
    if len(profile_json) > 8000:
        profile_json = profile_json[:8000] + "\n... (truncated)"

    # Priority sections text
    priority_text = master_ctx.get("priority_sections_text", "")
    if len(priority_text) > 15000:
        priority_text = priority_text[:15000] + "\n... (truncated)"

    filled = template.format(
        master=master,
        master_display_name=master_display_name(master),
        priority_sections_text=priority_text or "(无 priority section)",
        profile_json=profile_json,
        soul_toc_summary=toc_summary,
        debate_id=debate_id,
        debate_mode=debate_mode,
        reintro_candidates=reintro_display,
    )

    if strict_retry:
        filled += """

==== STRICT RETRY NOTICE ====
上次输出不合规。特别注意：
- qualitative_claim 绝不能含数字、%、年限等数值信息
- 每条 seed 只能表达一个观点（禁止"既...又" / "不A但B"等复合句式）
- 所有必填字段（rule_subject / theme / category / anti_scope 等）不能缺失
- 最少产出 5 条合规 seed

再次严格遵守 schema，否则视为本轮提案失败。
"""
    return filled


# ─── LLM call ───

def call_phase1_for_master(master: str, master_ctx: dict, debate_id: str,
                             debate_mode: str, strict_retry: bool = False,
                             timeout: int = PHASE1_TIMEOUT) -> tuple[Optional[str], dict]:
    """Return (raw_output, meta). raw_output is inner 'result' string; None if failed."""
    prompt = render_phase1_prompt(master, master_ctx, debate_id, debate_mode, strict_retry)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=timeout, text=True,
        )
        if res.returncode != 0:
            return None, {"error": f"exit {res.returncode}",
                          "stderr_head": res.stderr[:300]}
        return res.stdout, {"returncode": 0, "prompt_len": len(prompt)}
    except subprocess.TimeoutExpired:
        return None, {"error": "timeout", "timeout_seconds": timeout}
    except Exception as e:
        return None, {"error": str(e)}


def parse_seeds_from_raw(raw_stdout: str, master: str) -> list[dict]:
    """Parse Claude CLI output → list of seed dicts. Inject _master if missing."""
    parsed = parse_claude_cli_result(raw_stdout, expected_keys=["seeds"])
    if not parsed:
        return []
    seeds = parsed.get("seeds")
    if not isinstance(seeds, list):
        return []
    for s in seeds:
        if isinstance(s, dict):
            s.setdefault("_master", master)
    return [s for s in seeds if isinstance(s, dict)]


def validate_and_separate(seeds: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split seeds into (valid, invalid_with_errors)."""
    valid, invalid = [], []
    used_ids = set()
    for idx, s in enumerate(seeds):
        # Ensure unique seed_id
        orig_id = s.get("seed_id")
        if not orig_id or orig_id in used_ids:
            s["seed_id"] = f"seed_{idx + 1:02d}"
        used_ids.add(s["seed_id"])

        ok, errs = validate_seed(s, strict=True)
        if ok:
            valid.append(s)
        else:
            invalid.append({"seed": s, "errors": errs})
    return valid, invalid


# ─── v{N-1} fallback ───

def load_v_prev_hard_as_seeds(master: str, current_principles: dict) -> list[dict]:
    """Load HARD conditions for this master from Principles/current.schema.json
    and convert them to seed_v1_1 format (marked with _fallback_from_v).

    Returns empty list if no current principles. Prints loud diagnostic to
    stderr distinguishing first-ever-run (no schema) from incompatible-schema
    (schema exists but lacks v0.4.1 `hard_rules` + `variant_seeds_by_master`
    shape — e.g. legacy Pre-A v1.0 which used flat `rules` and only
    `threshold_variants_by_master`). Silent empty return would mask a real
    problem exactly at the moment the pipeline needs the fallback to rescue it.
    """
    schema = current_principles.get("schema")
    if not schema:
        print(f"[fallback] master={master}: no v_prev schema available "
              f"(first-ever debate — fallback not possible)", file=sys.stderr)
        return []
    if not isinstance(schema, dict):
        print(f"[fallback] master={master}: v_prev schema is not a dict "
              f"(type={type(schema).__name__})", file=sys.stderr)
        return []
    hard_rules = schema.get("hard_rules", [])
    if not hard_rules and schema.get("rules"):
        # Legacy Pre-A format uses `rules`; warn but don't auto-promote — rule
        # shape is incompatible (no `variant_seeds_by_master`), so downstream
        # master-variant lookup returns None for every rule anyway.
        print(f"[fallback] master={master}: v_prev schema uses legacy "
              f"`rules` key (Pre-A format), not v0.4.1 `hard_rules`. "
              f"Fallback cannot recover master-level variants. "
              f"Upgrade current.schema.json or accept this run cannot "
              f"tolerate phase1 failures.", file=sys.stderr)
        return []
    out = []
    for idx, rule in enumerate(hard_rules):
        variants = rule.get("variant_seeds_by_master", {})
        master_variant = variants.get(master) if isinstance(variants, dict) else None
        if not master_variant:
            continue
        # Build a seed from the stored variant
        seed = {
            "seed_id": f"seed_{idx + 1:02d}",
            "_master": master,
            "rule_subject": rule.get("rule_subject", "target"),
            "theme": rule.get("theme", "capital_return"),
            "category": master_variant.get("category", rule.get("category_primary", "quantitative_hard")),
            "qualitative_claim": rule.get("canonical_claim", ""),
            "quantitative_rule": master_variant.get("quantitative_rule"),
            "qualitative_rule": master_variant.get("qualitative_rule"),
            "severity": master_variant.get("severity", "warning"),
            "anti_scope": master_variant.get("anti_scope", "与上版本条目相同的作用域"),
            "rationale": master_variant.get("rationale", "从上版本 HARD 条款回退，等待本轮重新辩论"),
            "evidence_strength": "consistent_pattern",
            "supporting_section_id": master_variant.get("supporting_section_id", "[ref_fallback]"),
            "supporting_profile_factor": master_variant.get("supporting_profile_factor", "fallback"),
            "_fallback_from_v": schema.get("version", "v_prev"),
        }
        out.append(seed)
    if not out:
        print(f"[fallback] master={master}: v_prev schema had {len(hard_rules)} "
              f"hard_rules but no variant_seeds_by_master for this master. "
              f"Returning empty fallback.", file=sys.stderr)
    return out


# ─── Main entry ───

def draft_seeds_for_master(master: str, master_ctx: dict, debate_id: str,
                             debate_mode: str, current_principles: dict,
                             dropped_tracker: Optional[DroppedTracker] = None) -> dict:
    """Run Phase 1 for one master with retry + fallback.

    Returns {"seeds": [...], "metadata": {...}} where metadata includes status
    (success | retry_1 | retry_2 | fallback | partial_failure) and validation details.
    """
    attempts: list[dict] = []
    final_seeds: list[dict] = []
    status = "partial_failure"

    for attempt_idx in range(MAX_RETRIES + 1):
        # Per design v0.4.1 Phase 1 degradation:
        #   attempt 0: initial prompt
        #   attempt 1: same prompt (give LLM another identical shot)
        #   attempt 2: inject strict compliance notice
        strict = attempt_idx >= 2
        raw, meta = call_phase1_for_master(master, master_ctx, debate_id, debate_mode,
                                             strict_retry=strict)
        attempts.append({"attempt": attempt_idx, **meta})
        if raw is None:
            continue
        seeds = parse_seeds_from_raw(raw, master)
        valid, invalid = validate_and_separate(seeds)
        attempts[-1]["total_returned"] = len(seeds)
        attempts[-1]["valid"] = len(valid)
        attempts[-1]["invalid"] = len(invalid)
        attempts[-1]["invalid_examples"] = invalid[:3]  # for debugging

        if len(valid) >= MIN_VALID_SEEDS:
            final_seeds = valid
            status = "success" if attempt_idx == 0 else f"retry_{attempt_idx}"
            break

    # Fallback if all attempts failed to reach minimum
    if len(final_seeds) < MIN_VALID_SEEDS:
        fallback_seeds = load_v_prev_hard_as_seeds(master, current_principles)
        if fallback_seeds:
            final_seeds = fallback_seeds
            status = "fallback"

    # Track re-introductions in tracker (if any valid seed had _reintroduced_from)
    if dropped_tracker:
        for s in final_seeds:
            if s.get("_reintroduced_from"):
                # Extract cluster_id from e.g. "cl_26 (v1.0 dropped-archive)"
                m = re.match(r"(cl_\d+)", s["_reintroduced_from"])
                if m:
                    dropped_tracker.record_reintroduction_attempt(
                        m.group(1), master, debate_id
                    )

    # Write output file
    out_path = PREP_DIR / f"phase1_{master}_seeds.jsonl"
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for s in final_seeds:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    return {
        "master": master,
        "seeds": final_seeds,
        "seed_count": len(final_seeds),
        "status": status,
        "attempts": attempts,
        "output_path": str(out_path),
    }


def draft_seeds_parallel(context: dict) -> dict:
    """Phase 1 full: run all 3 masters in parallel."""
    debate_id = context["debate_id"]
    debate_mode = context.get("debate_mode", "full")
    current_principles = context.get("current_principles", {})
    masters_ctx = context.get("masters", {})

    dropped_tracker = DroppedTracker()  # shared, for tracking re-intro attempts

    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(draft_seeds_for_master, m, masters_ctx.get(m, {}),
                        debate_id, debate_mode, current_principles,
                        dropped_tracker): m
            for m in MASTERS
        }
        for fut in futures:
            master = futures[fut]
            try:
                results[master] = fut.result(timeout=PHASE1_TIMEOUT + 60)
            except Exception as e:
                tb = traceback.format_exc()
                err_msg = str(e) or type(e).__name__
                print(f"[phase1] ERROR master={master}: {err_msg}",
                      file=sys.stderr)
                print(tb, file=sys.stderr)
                # Attempt fallback to v_prev HARD before giving up
                fallback_seeds: list[dict] = []
                try:
                    fallback_seeds = load_v_prev_hard_as_seeds(master,
                                                                current_principles)
                except Exception as fb_e:
                    print(f"[phase1] fallback-load for {master} also failed: {fb_e}",
                          file=sys.stderr)

                if fallback_seeds:
                    out_path = PREP_DIR / f"phase1_{master}_seeds.jsonl"
                    PREP_DIR.mkdir(parents=True, exist_ok=True)
                    with out_path.open("w", encoding="utf-8") as f:
                        for s in fallback_seeds:
                            f.write(json.dumps(s, ensure_ascii=False) + "\n")
                    print(f"[phase1] master={master} recovered via fallback: "
                          f"{len(fallback_seeds)} v_prev HARD seeds loaded",
                          file=sys.stderr)
                    results[master] = {
                        "master": master,
                        "seeds": fallback_seeds,
                        "seed_count": len(fallback_seeds),
                        "status": "fallback",
                        "error": err_msg,
                        "traceback": tb,
                        "output_path": str(out_path),
                    }
                else:
                    results[master] = {
                        "master": master, "seeds": [], "seed_count": 0,
                        "status": "error",
                        "error": err_msg,
                        "traceback": tb,
                    }

    # Save re-intro tracker state
    dropped_tracker.save()

    # Partial failure detection
    fallback_count = sum(1 for r in results.values() if r.get("status") == "fallback")
    error_count = sum(1 for r in results.values() if r.get("status") == "error")
    partial_failure = (fallback_count + error_count) >= 2

    summary = {
        "debate_id": debate_id,
        "results_by_master": results,
        "partial_failure": partial_failure,
        "fallback_count": fallback_count,
        "error_count": error_count,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    summary_path = PREP_DIR / "phase1_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
