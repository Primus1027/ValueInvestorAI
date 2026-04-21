"""Phase 3b-quant: Quantitative threshold voting.

Only runs for clusters that passed Phase 3b-qual (L1 or L2).
For each such cluster:
  - Each master proposes their threshold + would_accept_looser/stricter
  - Compute "lowest consensus" using spectrum of acceptance ranges
  - Generate follow-up agenda items for upgrade proposals
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, MASTERS, master_display_name,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

QUANT_VOTE_TIMEOUT = 180
# "Same magnitude" defined as max/min < 10 (standard 1-order-of-magnitude test).
# e.g., 3/5/10 years → ratio 3.3, same magnitude.
#       0.05 / 0.15 / 0.25 → ratio 5, same magnitude.
#       0 / 3 / 25 → cross-magnitude (zero-involving or 25x spread).
SAME_MAGNITUDE_RATIO = 10.0


def render_quant_vote_prompt(master: str, cluster: dict,
                                qual_vote_summary: dict,
                                own_final_position: str) -> str:
    template = (PROMPTS_DIR / "phase3b_quant_vote.md").read_text(encoding="utf-8")
    return template.format(
        master=master,
        master_display_name=master_display_name(master),
        cluster_id=cluster.get("cluster_id"),
        canonical_claim=cluster.get("canonical_claim", ""),
        rule_subject=cluster.get("rule_subject", ""),
        qual_vote_summary=json.dumps(qual_vote_summary, ensure_ascii=False)[:500],
        variant_seeds=json.dumps(cluster.get("variant_seeds", []), ensure_ascii=False, indent=2),
        own_final_position=own_final_position or "(无 Phase 2.75 辩论)",
    )


def call_quant_vote_for_master(master: str, cluster: dict,
                                  qual_vote_summary: dict,
                                  own_final_position: str) -> dict:
    prompt = render_quant_vote_prompt(master, cluster, qual_vote_summary, own_final_position)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=QUANT_VOTE_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "error": f"exit {res.returncode}",
                    "proposed_threshold": None, "proposed_severity": None}
        parsed = parse_claude_cli_result(res.stdout, expected_keys=[
            "proposed_threshold", "proposed_operator", "proposed_data_field",
            "proposed_severity", "rationale",
        ])
        if not parsed:
            return {"master": master, "error": "parse_fail",
                    "proposed_threshold": None, "proposed_severity": None}
        return {
            "master": master,
            "proposed_threshold": parsed.get("proposed_threshold"),
            "proposed_operator": parsed.get("proposed_operator"),
            "proposed_data_field": parsed.get("proposed_data_field"),
            "proposed_severity": parsed.get("proposed_severity"),
            "rationale": str(parsed.get("rationale", ""))[:400],
            "would_accept_looser": parsed.get("would_accept_looser"),
            "would_accept_stricter": parsed.get("would_accept_stricter"),
            "direction_preference": parsed.get("direction_preference", "neutral"),
        }
    except Exception as e:
        return {"master": master, "error": str(e),
                "proposed_threshold": None, "proposed_severity": None}


def run_quant_vote_for_cluster(cluster: dict, qual_vote_summary: dict) -> dict:
    """Run 3 parallel master votes."""
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(call_quant_vote_for_master, m, cluster, qual_vote_summary, ""): m
            for m in MASTERS
        }
        results = {}
        for fut in futures:
            r = fut.result(timeout=QUANT_VOTE_TIMEOUT + 30)
            results[r["master"]] = r
    return results


def compute_lowest_consensus(proposals: dict, cluster: dict) -> dict:
    """Compute Layer 0 threshold from 3 master proposals.

    Modes:
    - same_magnitude: all thresholds non-null and max/min < 3 →
        Layer 0 = the weakest (loosest) threshold that all accept
    - cross_magnitude: thresholds vary >3x but acceptance ranges might overlap →
        check if would_accept_looser intersections exist
    - subject_mismatch: different operators (>, <) suggest different rule_subjects
    - direction_conflict: incompatible direction preferences
    - no_threshold: cluster is qualitative-only, no numeric consensus needed
    """
    master_thresholds = {
        m: p.get("proposed_threshold")
        for m, p in proposals.items()
    }
    non_null = {m: t for m, t in master_thresholds.items() if isinstance(t, (int, float))}

    if not non_null:
        # Qualitative-only
        return {
            "mode": "no_threshold",
            "layer0_threshold": None,
            "variant_thresholds_by_master": master_thresholds,
            "follow_up_items": [],
            "requires_manual_review": False,
        }

    thresholds = list(non_null.values())
    ops = {p.get("proposed_operator") for p in proposals.values() if p.get("proposed_operator")}
    # Direction conflict — one wants >, another wants <
    has_gt = any(op in (">", ">=") for op in ops)
    has_lt = any(op in ("<", "<=") for op in ops)
    if has_gt and has_lt:
        return {
            "mode": "direction_conflict",
            "layer0_threshold": None,
            "variant_thresholds_by_master": master_thresholds,
            "follow_up_items": [],
            "requires_manual_review": True,
        }

    t_min, t_max = min(thresholds), max(thresholds)

    # Special case: if any master proposes a zero threshold, this is either
    # "no constraint" (dominates lowest-consensus, removing the rule) or a
    # genuine bound (rare). We require manual review rather than silently
    # zeroing out everyone else's constraint.
    zero_count = sum(1 for t in thresholds if t == 0)
    if zero_count > 0 and zero_count < len(thresholds):
        return {
            "mode": "zero_threshold_present",
            "layer0_threshold": None,
            "variant_thresholds_by_master": master_thresholds,
            "follow_up_items": [],
            "requires_manual_review": True,
            "note": "at least one master proposed threshold=0 (no-constraint); manual review required",
        }

    if t_min == 0:
        # All thresholds are 0 — everyone agrees on no constraint
        magnitude_ratio = 1.0
    else:
        magnitude_ratio = abs(t_max / t_min)

    if magnitude_ratio < SAME_MAGNITUDE_RATIO:
        # Same magnitude — Layer 0 picks the "loosest acceptable" value.
        # For "<" operator (e.g., ROIC<15% warning), loosest = LARGEST threshold
        #   (triggers less often, excludes fewer companies)
        # For ">" operator (e.g., holding period ≥10 yr), loosest = SMALLEST
        #   (fewer investments ruled out)
        # Since ops normalized to single direction, use direction to pick.
        is_lt_op = has_lt  # either lt or gt, not both (passed conflict check)
        if is_lt_op:
            # Looser = larger threshold (less strict trigger)
            # BUT user wants "lowest consensus" which means every master accepts
            # the result. For threshold<X triggers, the LARGEST threshold is the
            # loosest (triggers on most values). Every master would accept at
            # least the LARGEST since their own is <= LARGEST.
            # Wait, that's wrong. Master A says threshold=10 (trigger when X<10).
            # Master B says threshold=15 (trigger when X<15). B's trigger fires
            # in more cases. "Loosest" for the business = X must be >=10 to pass
            # Master A, but X must be >=15 to pass Master B. To pass ALL, X must
            # be >=15. So the stricter Master's threshold is the "consensus
            # bar that all accept".
            # Re-read spec: "最低共识" — lowest common-denominator bar. For
            # holding-period (>= N), Layer 0 = min N (easiest bar). For ROIC (<N
            # threshold), Layer 0 = max N (easiest bar)... Actually the user's
            # intent from our earlier discussion: "持有期 Y=10 / W=3 / C=5 →
            # Layer 0 取最低共识 ≥ 3 年" — i.e., the LEAST strict bar. For
            # "≥ N 年" (higher = stricter), least strict = smallest N = 3.
            # So we take min() for ">=" operator, max() for "<=" operator.
            layer0 = max(thresholds)  # for "<" op: largest = least-strict
        else:
            layer0 = min(thresholds)  # for ">=": smallest = least-strict

        # Follow-up agenda: each master whose threshold is stricter
        upgrade_items = []
        for m, t in non_null.items():
            if t != layer0:
                upgrade_items.append({
                    "master": m,
                    "from_threshold": layer0,
                    "to_threshold": t,
                    "rationale": proposals[m].get("rationale", ""),
                })

        return {
            "mode": "same_magnitude",
            "layer0_threshold": layer0,
            "variant_thresholds_by_master": master_thresholds,
            "follow_up_items": upgrade_items,
            "requires_manual_review": False,
        }

    else:
        # Cross-magnitude — check would_accept_looser overlap
        looser_bounds = {}
        for m, p in proposals.items():
            wa = p.get("would_accept_looser")
            if isinstance(wa, (int, float)):
                looser_bounds[m] = wa
        if looser_bounds and len(looser_bounds) >= 2:
            # Check if loosest-acceptable intersects
            common_loosest = max(looser_bounds.values()) if has_lt else min(looser_bounds.values())
            return {
                "mode": "cross_magnitude_resolved_via_accept_looser",
                "layer0_threshold": common_loosest,
                "variant_thresholds_by_master": master_thresholds,
                "follow_up_items": [
                    {
                        "master": m, "from_threshold": common_loosest,
                        "to_threshold": proposals[m].get("proposed_threshold"),
                        "rationale": proposals[m].get("rationale", ""),
                    }
                    for m in non_null
                ],
                "requires_manual_review": False,
            }
        # Really cross magnitude — may indicate subject mismatch
        return {
            "mode": "cross_magnitude_unresolved",
            "layer0_threshold": None,
            "variant_thresholds_by_master": master_thresholds,
            "follow_up_items": [],
            "requires_manual_review": True,
        }


def phase3b_quant_vote(debate_id: str, qual_summary: dict) -> dict:
    """Only vote on clusters with decision L1 or L2."""
    from scripts.soul.board.vote_qualitative import load_clusters
    clusters = load_clusters()
    qual_votes_path = PREP_DIR / "phase3b_qual_votes.jsonl"
    if not qual_votes_path.exists():
        return {"error": "phase3b_qual_votes.jsonl missing"}

    qual_by_cluster = {}
    with qual_votes_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                v = json.loads(line)
                qual_by_cluster[v["cluster_id"]] = v
            except Exception:
                continue

    results = []
    for cluster in clusters:
        qv = qual_by_cluster.get(cluster.get("cluster_id"))
        if not qv:
            continue
        if qv.get("decision") not in ("L1", "L2"):
            continue

        print(f"[phase3b-quant] Voting on {cluster.get('cluster_id')}")
        proposals = run_quant_vote_for_cluster(cluster, qv)
        consensus = compute_lowest_consensus(proposals, cluster)
        results.append({
            "cluster_id": cluster.get("cluster_id"),
            "canonical_claim": cluster.get("canonical_claim"),
            "rule_subject": cluster.get("rule_subject"),
            "proposals_by_master": proposals,
            "consensus": consensus,
        })

    out_path = PREP_DIR / "phase3b_quant_votes.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "debate_id": debate_id,
        "total_clusters_voted": len(results),
        "consensus_modes": {
            mode: sum(1 for r in results if r["consensus"]["mode"] == mode)
            for mode in set(r["consensus"]["mode"] for r in results)
        } if results else {},
        "manual_review_count": sum(1 for r in results
                                    if r["consensus"].get("requires_manual_review")),
        "output_path": str(out_path),
    }
    (PREP_DIR / "phase3b_quant_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return summary
