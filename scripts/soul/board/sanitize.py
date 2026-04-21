"""Phase 1.5: Seed de-anonymization.

Replaces methodology fingerprint words (e.g., "本分" → "品行自律") in
qualitative_claim / rationale / anti_scope so Phase 2 anonymity holds.

Also maps supporting_section_id → [ref_N] placeholders.

Two-pass approach:
1. Static replacement using _fingerprint_dict.json
2. Optional Sonnet pass for subtle identity markers the dict missed
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, FINGERPRINT_DICT_PATH,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

SANITIZE_TIMEOUT = 90


def load_fingerprint_dict() -> tuple[dict, list[re.Pattern]]:
    """Load _fingerprint_dict.json. Returns empty dicts if file missing or corrupt."""
    if not FINGERPRINT_DICT_PATH.exists():
        print(f"[sanitize] WARN: {FINGERPRINT_DICT_PATH} missing; "
              f"Phase 1.5 will do no static replacement")
        return {}, []
    try:
        data = json.loads(FINGERPRINT_DICT_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[sanitize] WARN: could not parse {FINGERPRINT_DICT_PATH}: {e}")
        return {}, []
    replacements = data.get("replacements", {}) or {}
    scan_pats_raw = (data.get("_scan_patterns", {}) or {}).get("patterns", []) or []
    scan_pats = []
    for p in scan_pats_raw:
        try:
            scan_pats.append(re.compile(p, re.IGNORECASE))
        except re.error:
            continue
    return replacements, scan_pats


def apply_static_replacement(text: str, replacements: dict) -> tuple[str, list[str]]:
    """Apply fingerprint dictionary. Returns (new_text, list_of_keys_replaced)."""
    replaced_keys: list[str] = []
    # Sort keys by length desc so longer matches win first
    for key in sorted(replacements.keys(), key=len, reverse=True):
        if key.startswith("_"):
            continue
        if key in text:
            text = text.replace(key, replacements[key])
            replaced_keys.append(key)
    return text, replaced_keys


def detect_remaining_fingerprints(text: str, scan_patterns: list[re.Pattern]) -> list[str]:
    """Return list of fingerprint matches still present after static replacement."""
    hits = []
    for pat in scan_patterns:
        m = pat.search(text)
        if m:
            hits.append(m.group(0))
    return hits


def sanitize_seed_static(seed: dict, replacements: dict,
                           scan_patterns: list[re.Pattern],
                           section_id_counter: list[int]) -> tuple[dict, dict, bool]:
    """Single-pass static sanitization. Returns (sanitized_seed, ref_map, needs_llm_pass).

    needs_llm_pass=True means residual fingerprints were detected and an LLM
    second pass is recommended.
    """
    sanitized = dict(seed)  # shallow copy
    all_replaced: list[str] = []

    # Fields to sanitize
    for field in ("qualitative_claim", "rationale", "anti_scope", "qualitative_rule"):
        v = sanitized.get(field)
        if isinstance(v, str) and v:
            new_v, keys = apply_static_replacement(v, replacements)
            sanitized[field] = new_v
            all_replaced.extend(keys)

    # supporting_section_id → [ref_N]
    ref_map: dict[str, str] = {}
    orig_section = sanitized.get("supporting_section_id", "")
    if orig_section:
        section_id_counter[0] += 1
        ref_key = f"[ref_{section_id_counter[0]}]"
        ref_map[ref_key] = orig_section
        sanitized["supporting_section_id"] = ref_key

    # Check residual fingerprints across all sanitized text fields
    needs_llm_pass = False
    for field in ("qualitative_claim", "rationale", "anti_scope", "qualitative_rule"):
        v = sanitized.get(field)
        if isinstance(v, str):
            hits = detect_remaining_fingerprints(v, scan_patterns)
            if hits:
                needs_llm_pass = True
                break

    sanitized["_sanitized"] = True
    sanitized["_ref_map"] = ref_map
    sanitized["_static_replacements_applied"] = all_replaced

    return sanitized, ref_map, needs_llm_pass


def sanitize_seed_via_llm(seed: dict, fingerprint_dict: dict) -> Optional[dict]:
    """Second-pass LLM sanitization for subtle fingerprints.

    Uses phase1_5_sanitize.md template.
    """
    template = (PROMPTS_DIR / "phase1_5_sanitize.md").read_text(encoding="utf-8")
    prompt = template.format(
        fingerprint_dict_json=json.dumps(fingerprint_dict, ensure_ascii=False, indent=2)[:3000],
        seed_json=json.dumps(seed, ensure_ascii=False, indent=2),
    )
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=SANITIZE_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return None
        parsed = parse_claude_cli_result(res.stdout, expected_keys=["qualitative_claim", "rationale"])
        if parsed and "qualitative_claim" in parsed:
            return parsed
    except Exception:
        pass
    return None


def sanitize_all_seeds(phase1_summary: dict) -> dict:
    """Phase 1.5 entry point. Processes all masters' seeds.

    Writes:
      prep/phase1_5_{master}_sanitized.jsonl
      prep/phase1_5_section_id_map.json   (ref_N → original path)
      prep/phase1_5_summary.json
    """
    replacements, scan_patterns = load_fingerprint_dict()
    section_id_counter = [0]  # mutable box for reference counter
    overall_ref_map: dict[str, str] = {}

    # Backup original seeds (for audit)
    backup_dir = PREP_DIR / "phase1_original_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    results_by_master: dict = {}
    for master, result in phase1_summary.get("results_by_master", {}).items():
        original_seeds = result.get("seeds", [])
        # Write backup
        backup_path = backup_dir / f"phase1_{master}_seeds_original.jsonl"
        with backup_path.open("w", encoding="utf-8") as bf:
            for s in original_seeds:
                bf.write(json.dumps(s, ensure_ascii=False) + "\n")

        sanitized_seeds: list[dict] = []
        llm_passes_used = 0
        for s in original_seeds:
            sanitized, ref_map, needs_llm = sanitize_seed_static(
                s, replacements, scan_patterns, section_id_counter
            )
            overall_ref_map.update(ref_map)

            if needs_llm:
                llm_result = sanitize_seed_via_llm(sanitized, replacements)
                if llm_result:
                    # Merge LLM-pass result back into sanitized seed
                    for f in ("qualitative_claim", "rationale", "anti_scope", "qualitative_rule"):
                        if f in llm_result and isinstance(llm_result[f], str):
                            sanitized[f] = llm_result[f]
                    llm_passes_used += 1
                    # Re-check residuals after LLM pass
                    for f in ("qualitative_claim", "rationale", "anti_scope", "qualitative_rule"):
                        v = sanitized.get(f)
                        if isinstance(v, str):
                            hits = detect_remaining_fingerprints(v, scan_patterns)
                            if hits:
                                sanitized["_sanitize_warning"] = f"residual fingerprints after LLM pass: {hits}"
                                break

            sanitized_seeds.append(sanitized)

        out_path = PREP_DIR / f"phase1_5_{master}_sanitized.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for s in sanitized_seeds:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        results_by_master[master] = {
            "master": master,
            "sanitized_count": len(sanitized_seeds),
            "llm_passes_used": llm_passes_used,
            "output_path": str(out_path),
            "backup_path": str(backup_path),
        }

    # Save section_id ref map
    ref_map_path = PREP_DIR / "phase1_5_section_id_map.json"
    ref_map_path.write_text(json.dumps(overall_ref_map, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    summary = {
        "results_by_master": results_by_master,
        "total_sanitized_seeds": sum(r["sanitized_count"] for r in results_by_master.values()),
        "total_llm_passes": sum(r["llm_passes_used"] for r in results_by_master.values()),
        "ref_map_path": str(ref_map_path),
    }
    summary_path = PREP_DIR / "phase1_5_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    return summary
