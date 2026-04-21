"""Phase 3a: Semantic clustering (Opus call).

Takes Phase 2 pairwise matrix + Phase 2.75 final positions and produces
canonical clusters.

Enforces:
- Same rule_subject within a cluster (hard constraint)
- Preserves variant thresholds / severity / category
- Uses Phase 2.75 convergence info to inform merging decisions
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, MASTERS,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

CLUSTER_TIMEOUT = 900  # 15 minutes for Opus on large input


def load_phase2_matrix() -> list[dict]:
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


def load_phase275_summary() -> dict:
    p = PREP_DIR / "phase2_75_summary.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_all_revised_seeds() -> list[dict]:
    """Load all revised seeds from all 3 masters."""
    out = []
    for m in MASTERS:
        p = PREP_DIR / f"phase2_5_{m}_revised_seeds.jsonl"
        if not p.exists():
            continue
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


def render_cluster_prompt(all_seeds: list[dict], phase2_matrix: list[dict],
                            phase275_final_positions: dict) -> str:
    template = (PROMPTS_DIR / "phase3a_cluster.md").read_text(encoding="utf-8")
    # Compact seeds to save tokens
    compact_seeds = [
        {
            "seed_id": s["seed_id"],
            "_master": s.get("_master"),
            "rule_subject": s.get("rule_subject"),
            "theme": s.get("theme"),
            "category": s.get("category"),
            "qualitative_claim": s.get("qualitative_claim"),
            "threshold": (s.get("quantitative_rule") or {}).get("threshold")
                if isinstance(s.get("quantitative_rule"), dict) else None,
            "severity": s.get("severity"),
            "supporting_section_id": s.get("supporting_section_id"),
        }
        for s in all_seeds
    ]
    compact_matrix = [
        {"seed_ids": p.get("seed_ids"), "equivalent": p.get("equivalent"),
         "confidence": p.get("confidence")}
        for p in phase2_matrix
        if not p.get("skipped_llm") and p.get("equivalent")  # Only equivalent pairs matter
    ]
    return template.format(
        all_seeds=json.dumps(compact_seeds, ensure_ascii=False, indent=2),
        pairwise_matrix=json.dumps(compact_matrix, ensure_ascii=False, indent=2),
        cross_rebuttal_final_positions=json.dumps(phase275_final_positions,
                                                    ensure_ascii=False, indent=2),
    )


def call_opus_cluster(all_seeds: list[dict], phase2_matrix: list[dict],
                        phase275_final_positions: dict) -> dict:
    prompt = render_cluster_prompt(all_seeds, phase2_matrix, phase275_final_positions)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-opus-4-7",
             "--output-format", "json"],
            capture_output=True, timeout=CLUSTER_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"error": f"exit {res.returncode}",
                    "stderr_head": res.stderr[:300]}
        parsed = parse_claude_cli_result(res.stdout, expected_keys=["clusters"])
        if not parsed:
            return {"error": "parse_fail"}
        clusters = parsed.get("clusters", [])
        if not isinstance(clusters, list):
            return {"error": "clusters not list"}
        return {"clusters": clusters}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}


def validate_cluster_output(clusters: list[dict],
                              all_seed_uids: set[tuple]) -> tuple[list[dict], list[str]]:
    """Check:
    - Every (master, seed_id) UID appears in exactly one cluster
    - All variant_seeds within a cluster share same rule_subject

    Seed identity is `(master, seed_id)` tuple. Bare `seed_id` is NOT unique
    across masters (each master mints its own seed_01..seed_N namespace), so
    deduping by bare seed_id causes false-positive "duplicate" errors when two
    masters happen to share a numeric index.

    Returns (valid_clusters, list_of_errors).
    """
    errors = []
    seen_uids: set[tuple] = set()
    valid_clusters = []

    for c in clusters:
        if not isinstance(c, dict):
            continue
        cid = c.get("cluster_id", "?")
        variants = c.get("variant_seeds") or []
        if not variants:
            errors.append(f"cluster {cid}: no variant_seeds")
            continue

        # Extract rule_subjects
        rule_subjects = {v.get("rule_subject") or c.get("rule_subject")
                         for v in variants}
        rule_subjects.discard(None)
        if len(rule_subjects) > 1:
            errors.append(f"cluster {cid}: mixed rule_subjects {rule_subjects}")
            continue

        # Dedup check — keyed on (master, seed_id) to survive namespace collisions.
        for v in variants:
            uid = (v.get("master"), v.get("seed_id"))
            if uid in seen_uids:
                errors.append(
                    f"cluster {cid}: seed {uid[0]}/{uid[1]} appears in multiple clusters"
                )
            else:
                seen_uids.add(uid)

        # Compute support_count from distinct masters
        masters = {v.get("master") for v in variants if v.get("master")}
        c["support_count"] = len(masters)
        valid_clusters.append(c)

    # Check coverage
    missing = all_seed_uids - seen_uids
    if missing:
        errors.append(
            f"{len(missing)} seeds missing from any cluster: "
            f"{[f'{m}/{s}' for m, s in list(missing)[:10]]}"
        )

    return valid_clusters, errors


def phase3a_cluster() -> dict:
    """Main entry for Phase 3a."""
    all_seeds = load_all_revised_seeds()
    if not all_seeds:
        return {"error": "no_seeds_loaded"}

    matrix = load_phase2_matrix()
    # Guard against stale pre-fix matrices that lack the `masters` field
    # (would silently miscluster when masters share bare seed_ids).
    from scripts.soul.board.cross_rebuttal import _assert_matrix_has_masters
    _assert_matrix_has_masters(matrix)
    p275_summary = load_phase275_summary()
    # Extract final_positions flat dict
    final_positions = {}
    for d in p275_summary.get("disputes", []):
        final_positions[d["dispute_id"]] = d.get("final_positions_by_master", {})

    result = call_opus_cluster(all_seeds, matrix, final_positions)
    if "error" in result:
        # On failure, create minimal fallback clustering: one cluster per seed
        print(f"[phase3a] Opus call failed: {result['error']}; using singleton fallback")
        clusters = []
        for idx, s in enumerate(all_seeds):
            clusters.append({
                "cluster_id": f"cl_{idx+1:02d}",
                "rule_subject": s.get("rule_subject"),
                "canonical_claim": s.get("qualitative_claim"),
                "canonical_theme": s.get("theme"),
                "category_primary": s.get("category"),
                "categories_secondary": [],
                "variant_seeds": [{
                    "seed_id": s["seed_id"],
                    "master": s.get("_master"),
                    "claim": s.get("qualitative_claim"),
                    "threshold": (s.get("quantitative_rule") or {}).get("threshold")
                        if isinstance(s.get("quantitative_rule"), dict) else None,
                    "severity": s.get("severity"),
                    "category": s.get("category"),
                    "supporting_section_id": s.get("supporting_section_id"),
                }],
                "thresholds_variants_by_master": None,
                "severity_variants_by_master": {s.get("_master"): s.get("severity")},
                "support_count": 1,
                "merge_confidence": 0.0,
                "_fallback_singleton": True,
            })
    else:
        clusters = result["clusters"]

    # Validate — seed identity is (master, seed_id) UID, not bare seed_id.
    all_uids: set[tuple] = {(s.get("_master"), s["seed_id"]) for s in all_seeds}
    valid_clusters, errors = validate_cluster_output(clusters, all_uids)

    # Abort gate: genuine invariant breaches (mixed rule_subject, missing variant
    # seeds) must halt the pipeline. Missing-seed errors are recoverable below.
    hard_errors = [
        e for e in errors
        if "mixed rule_subjects" in e or "no variant_seeds" in e
           or "appears in multiple clusters" in e
    ]
    if hard_errors and not any(c.get("_fallback_singleton") for c in valid_clusters):
        raise RuntimeError(
            f"phase3a validation failed with {len(hard_errors)} hard errors "
            f"(bad cluster structure); refusing to proceed. First 3: {hard_errors[:3]}"
        )

    # If there were missing seeds, add as singletons
    existing_uids: set[tuple] = set()
    for c in valid_clusters:
        for v in c.get("variant_seeds", []):
            existing_uids.add((v.get("master"), v.get("seed_id")))
    missing_uids = all_uids - existing_uids
    next_cid_num = len(valid_clusters) + 1
    for mid_uid in missing_uids:
        m_name, m_sid = mid_uid
        s = next(
            (x for x in all_seeds
             if x["seed_id"] == m_sid and x.get("_master") == m_name),
            None,
        )
        if not s:
            continue
        valid_clusters.append({
            "cluster_id": f"cl_{next_cid_num:02d}",
            "rule_subject": s.get("rule_subject"),
            "canonical_claim": s.get("qualitative_claim"),
            "canonical_theme": s.get("theme"),
            "category_primary": s.get("category"),
            "categories_secondary": [],
            "variant_seeds": [{
                "seed_id": s["seed_id"],
                "master": s.get("_master"),
                "claim": s.get("qualitative_claim"),
                "threshold": (s.get("quantitative_rule") or {}).get("threshold")
                    if isinstance(s.get("quantitative_rule"), dict) else None,
                "severity": s.get("severity"),
                "category": s.get("category"),
                "supporting_section_id": s.get("supporting_section_id"),
            }],
            "thresholds_variants_by_master": None,
            "severity_variants_by_master": {s.get("_master"): s.get("severity")},
            "support_count": 1,
            "merge_confidence": 0.0,
            "_recovered_missing": True,
        })
        next_cid_num += 1

    # Persist
    out_path = PREP_DIR / "phase3a_clusters.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for c in valid_clusters:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    summary = {
        "total_clusters": len(valid_clusters),
        "hard_candidate": sum(1 for c in valid_clusters if c.get("support_count") == 3),
        "soft_candidate": sum(1 for c in valid_clusters if c.get("support_count") == 2),
        "singleton": sum(1 for c in valid_clusters if c.get("support_count") == 1),
        "validation_errors": errors,
        "fallback_singleton_used": any(c.get("_fallback_singleton") for c in valid_clusters),
        "output_path": str(out_path),
    }
    (PREP_DIR / "phase3a_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return summary
