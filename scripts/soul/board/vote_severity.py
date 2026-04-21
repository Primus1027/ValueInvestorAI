"""Phase 3b-sev: Severity aggregation (pure Python, no LLM).

Severity is an attribute of each seed in the cluster (already in variant_seeds).
Rules (v0.4.1 哲学):
  - Layer 0 severity = lightest severity among masters (true consensus floor)
  - Upgrade proposals from masters with stricter severity → follow_up_agenda
  - EXCEPTION: if canonical_claim contains negation verbs (拒绝/禁止/不投/不应),
    AND at least one master proposes veto, then Layer 0 = max(warning, lightest)
    — prevents "all note" degeneration in veto-semantic clusters.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.soul.board import PREP_DIR, SEVERITY_ORDER

# Negation-verb patterns that indicate "veto semantics" — these clusters should
# never degrade below warning per §二.2.2 of v0.4.1
# Placed as function-local to keep module stateless and easy to extend.
NEGATION_VERBS = [
    "拒绝", "禁止", "不投", "不应", "回避", "不买", "不做", "不参与",
    "归入.{0,5}太难", "归入.{0,5}过于困难",
    "pass\\b",  # Munger "pass" conversion
]
_NEGATION_RE = re.compile("|".join(NEGATION_VERBS), re.IGNORECASE)


def has_negation_semantics(canonical_claim: str) -> bool:
    if not canonical_claim:
        return False
    return bool(_NEGATION_RE.search(canonical_claim))


def compute_lowest_severity(severity_variants: dict[str, str],
                              canonical_claim: str) -> dict:
    """Compute Layer 0 severity + list of upgrade proposals.

    Args:
        severity_variants: {"buffett": "veto", "munger": "warning", "duan": "note"}
        canonical_claim: cluster's qualitative_claim for negation detection
    """
    if not severity_variants:
        return {
            "layer0_severity": None,
            "variants_by_master": {},
            "upgrade_agenda_items": [],
            "has_negation_semantics": False,
        }

    # Normalize to valid severities, skip unknowns
    valid_variants = {
        m: s for m, s in severity_variants.items()
        if s in SEVERITY_ORDER
    }
    if not valid_variants:
        return {
            "layer0_severity": "note",  # safe fallback
            "variants_by_master": severity_variants,
            "upgrade_agenda_items": [],
            "has_negation_semantics": False,
        }

    # Sort by severity order; pick lightest
    sorted_severities = sorted(valid_variants.items(), key=lambda kv: SEVERITY_ORDER[kv[1]])
    lightest_severity = sorted_severities[0][1]
    has_neg = has_negation_semantics(canonical_claim)

    # Negation-semantics floor: if canonical claim is negative and ≥1 master
    # proposes veto, floor Layer 0 at warning
    layer0 = lightest_severity
    has_veto_proposal = "veto" in valid_variants.values()
    if has_neg and has_veto_proposal and SEVERITY_ORDER[layer0] < SEVERITY_ORDER["warning"]:
        layer0 = "warning"

    # Generate upgrade agenda items for masters stricter than Layer 0
    upgrade_items = []
    for m, s in valid_variants.items():
        if SEVERITY_ORDER[s] > SEVERITY_ORDER[layer0]:
            upgrade_items.append({
                "master": m,
                "from_severity": layer0,
                "to_severity": s,
            })

    return {
        "layer0_severity": layer0,
        "variants_by_master": severity_variants,
        "upgrade_agenda_items": upgrade_items,
        "has_negation_semantics": has_neg,
        "floored_due_to_negation": (layer0 != lightest_severity),
    }


def phase3b_severity_vote(debate_id: str) -> dict:
    """Process all clusters that passed qualitative voting.

    Reads phase3a_clusters.jsonl + phase3b_qual_votes.jsonl.
    Writes phase3b_sev_votes.jsonl.
    """
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
        cid = cluster.get("cluster_id")
        qv = qual_by_cluster.get(cid)
        if not qv or qv.get("decision") not in ("L1", "L2"):
            continue

        sev_variants = cluster.get("severity_variants_by_master", {})
        consensus = compute_lowest_severity(sev_variants, cluster.get("canonical_claim", ""))
        results.append({
            "cluster_id": cid,
            "canonical_claim": cluster.get("canonical_claim"),
            "rule_subject": cluster.get("rule_subject"),
            "consensus": consensus,
        })

    out_path = PREP_DIR / "phase3b_sev_votes.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "debate_id": debate_id,
        "total_clusters": len(results),
        "layer0_severity_counts": {
            "veto": sum(1 for r in results if r["consensus"]["layer0_severity"] == "veto"),
            "warning": sum(1 for r in results if r["consensus"]["layer0_severity"] == "warning"),
            "note": sum(1 for r in results if r["consensus"]["layer0_severity"] == "note"),
        },
        "floored_due_to_negation_count": sum(
            1 for r in results if r["consensus"].get("floored_due_to_negation")
        ),
        "output_path": str(out_path),
    }
    (PREP_DIR / "phase3b_sev_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return summary
