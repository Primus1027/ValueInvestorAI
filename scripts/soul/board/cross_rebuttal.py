"""Phase 2.75: Cross-Rebuttal structured debate.

For each "dispute cluster" (potential clusters where threshold/severity variants
exist or equivalence confidence is borderline), run a 4-round debate:
  Round 1 — Position Statement (3 masters, parallel)
  Round 2 — Rebuttal (3 masters, parallel)
  Round 3 — Response (targets reply, parallel)
  Round 4 — Closing (optional, only if unresolved disagreement remains)

Produces transcripts under Principles/history/{debate_id}/debate_transcript_*.md
— these are the user-readable "meeting scripts".
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
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, HISTORY_DIR, MASTERS,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result, parse_llm_json  # noqa: E402

ROUND_TIMEOUT = 180  # 3 minutes per LLM call
PARTIAL_EQUIV_LOW = 0.3
PARTIAL_EQUIV_HIGH = 0.7

# Random but consistent-within-run anonymization: each dispute gets its own
# shuffled label assignment (A/B/C). masters tuple order is (buffett, munger, duan).
# We shuffle per-dispute using a seed derived from cluster_id.
import hashlib
import random


def anonymize_for_dispute(dispute_id: str) -> dict[str, str]:
    """Return master → label mapping for this dispute's debate transcript.

    Deterministic within a dispute, randomized across disputes.
    """
    seed = int(hashlib.md5(dispute_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    labels = ["A", "B", "C"]
    rng.shuffle(labels)
    return {m: labels[i] for i, m in enumerate(MASTERS)}


# ─────────── Identify dispute clusters (pre-clustering) ───────────

def identify_dispute_clusters(revised_seeds_by_master: dict,
                                phase2_matrix: list[dict]) -> list[dict]:
    """Scan seeds + matrix to find clusters with threshold/severity variants
    or partial equivalence — these need cross-rebuttal.

    Output: list of dispute cluster dicts ready for Phase 2.75.
    """
    # Build seed_id → seed index
    all_seeds: list[dict] = []
    for master, seeds in revised_seeds_by_master.items():
        all_seeds.extend(seeds)
    seeds_by_id = {s["seed_id"]: s for s in all_seeds}

    # Use equivalence matrix to union-find clusters of equivalent seeds
    from itertools import combinations
    parent = {s["seed_id"]: s["seed_id"] for s in all_seeds}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Union equivalent pairs
    for p in phase2_matrix:
        if p.get("equivalent") and not p.get("skipped_llm"):
            a, b = p["seed_ids"]
            if a in parent and b in parent:
                union(a, b)

    # Build clusters
    cluster_members: dict[str, list[str]] = {}
    for sid in parent:
        root = find(sid)
        cluster_members.setdefault(root, []).append(sid)

    # For each cluster with members from >=2 masters, check for variants
    disputes = []
    for root, members in cluster_members.items():
        if len(members) < 2:
            continue
        member_seeds = [seeds_by_id[sid] for sid in members]
        masters_in_cluster = set(s.get("_master") for s in member_seeds)
        if len(masters_in_cluster) < 2:
            continue
        # Get all distinct thresholds and severities
        thresholds = set()
        severities = set()
        for s in member_seeds:
            qr = s.get("quantitative_rule")
            if isinstance(qr, dict) and "threshold" in qr:
                thresholds.add(qr["threshold"])
            severities.add(s.get("severity"))
        # Dispute exists if: threshold variants OR severity variants
        has_threshold_dispute = len(thresholds) > 1
        has_severity_dispute = len(severities) > 1
        if not (has_threshold_dispute or has_severity_dispute):
            continue

        # Also include partial-equivalence borderlines (confidence 0.3-0.7 pairs)
        # even if they didn't make it to union. For now we include only this cluster.
        disputes.append({
            "dispute_id": f"dispute_{root}",
            "root_seed_id": root,
            "canonical_claim": (member_seeds[0].get("qualitative_claim") or "")[:150],
            "rule_subject": member_seeds[0].get("rule_subject", "target"),
            "theme": member_seeds[0].get("theme", ""),
            "member_seeds_by_master": {
                m: [s for s in member_seeds if s.get("_master") == m]
                for m in MASTERS
            },
            "dispute_type": (
                ("threshold" if has_threshold_dispute else "") +
                ("," if has_threshold_dispute and has_severity_dispute else "") +
                ("severity" if has_severity_dispute else "")
            ) or "equivalence_borderline",
            "thresholds_seen": sorted(thresholds) if thresholds else [],
            "severities_seen": sorted(severities),
        })

    # Also: borderline partial-equivalence pairs (cross-cluster)
    # Add them as separate disputes only if not already covered
    covered_sids = set()
    for d in disputes:
        for sids in d["member_seeds_by_master"].values():
            for s in sids:
                covered_sids.add(s["seed_id"])

    for p in phase2_matrix:
        if p.get("skipped_llm"):
            continue
        conf = p.get("confidence", 0)
        if PARTIAL_EQUIV_LOW <= conf <= PARTIAL_EQUIV_HIGH:
            a, b = p["seed_ids"]
            if a in covered_sids and b in covered_sids:
                continue
            sa = seeds_by_id.get(a)
            sb = seeds_by_id.get(b)
            if not sa or not sb:
                continue
            if sa.get("rule_subject") != sb.get("rule_subject"):
                continue
            d_id = f"dispute_partial_{a}_{b}"
            member_by_master: dict[str, list] = {m: [] for m in MASTERS}
            member_by_master.setdefault(sa.get("_master"), []).append(sa)
            if sa.get("_master") != sb.get("_master"):
                member_by_master.setdefault(sb.get("_master"), []).append(sb)
            disputes.append({
                "dispute_id": d_id,
                "root_seed_id": a,
                "canonical_claim": (sa.get("qualitative_claim") or "")[:150],
                "rule_subject": sa.get("rule_subject"),
                "theme": sa.get("theme"),
                "member_seeds_by_master": member_by_master,
                "dispute_type": "equivalence_borderline",
                "partial_equivalence_confidence": conf,
            })

    return disputes


# ─────────── Round 1: Position ───────────

def render_round1_prompt(dispute: dict, framework_label: str, master: str) -> str:
    template = (PROMPTS_DIR / "phase2_75_round1_position.md").read_text(encoding="utf-8")
    all_seeds_flat = []
    for m, seeds in dispute["member_seeds_by_master"].items():
        all_seeds_flat.extend(seeds)
    own_seeds = dispute["member_seeds_by_master"].get(master, [])
    return template.format(
        framework_label=framework_label,
        cluster_id=dispute["dispute_id"],
        canonical_claim=dispute["canonical_claim"],
        rule_subject=dispute["rule_subject"],
        theme=dispute.get("theme", ""),
        all_seeds_sanitized=json.dumps(all_seeds_flat, ensure_ascii=False, indent=2),
        own_seeds=json.dumps(own_seeds, ensure_ascii=False, indent=2),
    )


def call_round1(dispute: dict, master: str, label: str) -> dict:
    """Return dict with position_text."""
    prompt = render_round1_prompt(dispute, label, master)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=ROUND_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "label": label,
                    "position_text": f"[Round 1 error: exit {res.returncode}]"}
        # The output is a text-only response, not JSON-structured, but
        # it comes wrapped in {"result": "..."}. Unwrap.
        try:
            outer = json.loads(res.stdout)
            text = outer.get("result", "")
        except Exception:
            text = res.stdout
        text = text.strip()
        # Truncate to 150 Chinese chars if exceeded
        if len(text) > 250:
            text = text[:250] + "..."
        return {"master": master, "label": label, "position_text": text}
    except Exception as e:
        return {"master": master, "label": label, "position_text": f"[Round 1 error: {e}]"}


# ─────────── Round 2: Rebuttal ───────────

def render_round2_prompt(dispute: dict, framework_label: str,
                          round1_by_label: dict[str, str], own_position: str) -> str:
    template = (PROMPTS_DIR / "phase2_75_round2_rebuttal.md").read_text(encoding="utf-8")
    return template.format(
        framework_label=framework_label,
        cluster_id=dispute["dispute_id"],
        canonical_claim=dispute["canonical_claim"],
        position_a=round1_by_label.get("A", "(no position)"),
        position_b=round1_by_label.get("B", "(no position)"),
        position_c=round1_by_label.get("C", "(no position)"),
        own_position=own_position,
    )


def call_round2(dispute: dict, master: str, label: str,
                round1_by_label: dict[str, str], own_position: str) -> dict:
    prompt = render_round2_prompt(dispute, label, round1_by_label, own_position)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=ROUND_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "label": label, "target": None,
                    "rebuttal_text": "[Round 2 error]"}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["target", "rebuttal_text"])
        if not parsed:
            return {"master": master, "label": label, "target": None,
                    "rebuttal_text": "[Round 2 parse fail]"}
        target = parsed.get("target", "")
        # Defensive: LLM may return non-string (dict/list) or invalid label.
        # Must be a string, one of {"A","B","C"}, and not self.
        if not isinstance(target, str) or target not in ("A", "B", "C") or target == label:
            target = next((l for l in ["A", "B", "C"] if l != label), None)
        return {"master": master, "label": label, "target": target,
                "rebuttal_text": str(parsed.get("rebuttal_text", ""))[:200]}
    except Exception as e:
        return {"master": master, "label": label, "target": None,
                "rebuttal_text": f"[Round 2 error: {e}]"}


# ─────────── Round 3: Response ───────────

def render_round3_prompt(dispute: dict, framework_label: str, challenger_label: str,
                          rebuttal_text: str, own_position: str) -> str:
    template = (PROMPTS_DIR / "phase2_75_round3_response.md").read_text(encoding="utf-8")
    return template.format(
        framework_label=framework_label,
        cluster_id=dispute["dispute_id"],
        canonical_claim=dispute["canonical_claim"],
        own_position=own_position,
        challenger_label=challenger_label,
        rebuttal_text=rebuttal_text,
    )


def call_round3(dispute: dict, master: str, label: str,
                  challenger_label: str, rebuttal_text: str,
                  own_position: str) -> dict:
    prompt = render_round3_prompt(dispute, label, challenger_label, rebuttal_text, own_position)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=ROUND_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "label": label, "action": "acknowledge",
                    "response_text": "[Round 3 error]"}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["action", "response_text",
                                                         "revised_position"])
        if not parsed:
            return {"master": master, "label": label, "action": "acknowledge",
                    "response_text": "[Round 3 parse fail]"}
        return {
            "master": master, "label": label,
            "action": str(parsed.get("action", "acknowledge")),
            "response_text": str(parsed.get("response_text", ""))[:200],
            "revised_position": parsed.get("revised_position"),
        }
    except Exception as e:
        return {"master": master, "label": label, "action": "acknowledge",
                "response_text": f"[Round 3 error: {e}]"}


# ─────────── Round 4: Closing (optional) ───────────

def render_round4_prompt(dispute: dict, framework_label: str,
                          transcript_so_far: str) -> str:
    template = (PROMPTS_DIR / "phase2_75_round4_closing.md").read_text(encoding="utf-8")
    return template.format(
        framework_label=framework_label,
        cluster_id=dispute["dispute_id"],
        canonical_claim=dispute["canonical_claim"],
        transcript_so_far=transcript_so_far,
    )


def call_round4(dispute: dict, master: str, label: str,
                  transcript_so_far: str) -> dict:
    prompt = render_round4_prompt(dispute, label, transcript_so_far)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=ROUND_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "label": label, "closing_text": "[Round 4 error]"}
        try:
            outer = json.loads(res.stdout)
            text = outer.get("result", "").strip()
        except Exception:
            text = res.stdout.strip()
        if len(text) > 130:
            text = text[:130] + "..."
        return {"master": master, "label": label, "closing_text": text}
    except Exception as e:
        return {"master": master, "label": label, "closing_text": f"[Round 4 error: {e}]"}


# ─────────── Run one dispute end to end ───────────

def run_dispute(dispute: dict) -> dict:
    """Run all 4 rounds for one dispute. Return transcript + metadata."""
    label_map = anonymize_for_dispute(dispute["dispute_id"])
    reverse_label = {v: k for k, v in label_map.items()}

    # Round 1 — 3 parallel
    with ThreadPoolExecutor(max_workers=3) as ex:
        r1_futs = {
            ex.submit(call_round1, dispute, m, label_map[m]): m
            for m in MASTERS
        }
        r1_results = {}
        for fut in r1_futs:
            r = fut.result(timeout=ROUND_TIMEOUT + 30)
            r1_results[r["label"]] = r

    round1_by_label = {lbl: r["position_text"] for lbl, r in r1_results.items()}
    own_position_by_master = {m: r1_results[label_map[m]]["position_text"] for m in MASTERS}

    # Round 2 — 3 parallel
    with ThreadPoolExecutor(max_workers=3) as ex:
        r2_futs = {
            ex.submit(call_round2, dispute, m, label_map[m],
                      round1_by_label, own_position_by_master[m]): m
            for m in MASTERS
        }
        r2_results = {}
        for fut in r2_futs:
            r = fut.result(timeout=ROUND_TIMEOUT + 30)
            r2_results[r["label"]] = r

    # Round 3 — targeted masters respond
    # For each master, find if they were targeted
    target_to_responders = {}  # target_label → [(challenger_label, rebuttal_text)]
    for challenger_label, r2 in r2_results.items():
        tgt = r2.get("target")
        # Defensive: only accept valid A/B/C labels, not self
        if (isinstance(tgt, str) and tgt in ("A", "B", "C")
                and tgt != challenger_label):
            target_to_responders.setdefault(tgt, []).append(
                (challenger_label, r2.get("rebuttal_text", ""))
            )

    r3_results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        r3_futs = {}
        for responder_label, challenges in target_to_responders.items():
            if not challenges:
                continue
            # Respond to the first challenger (if multiple)
            chl_label, reb_text = challenges[0]
            responder_master = reverse_label.get(responder_label)
            if responder_master is None:
                # Shouldn't happen given the guards above, but be safe
                continue
            own_pos = own_position_by_master[responder_master]
            r3_futs[ex.submit(call_round3, dispute, responder_master, responder_label,
                                chl_label, reb_text, own_pos)] = responder_label
        for fut in r3_futs:
            r = fut.result(timeout=ROUND_TIMEOUT + 30)
            r3_results[r["label"]] = r

    # Round 4 — if any 'rebut' action in r3, run closing
    needs_closing = any(r.get("action") == "rebut" for r in r3_results.values())
    r4_results: dict = {}
    if needs_closing:
        transcript_so_far_for_closing = _format_transcript_so_far(
            dispute, label_map, r1_results, r2_results, r3_results
        )
        with ThreadPoolExecutor(max_workers=3) as ex:
            r4_futs = {
                ex.submit(call_round4, dispute, m, label_map[m],
                          transcript_so_far_for_closing): m
                for m in MASTERS
            }
            for fut in r4_futs:
                r = fut.result(timeout=ROUND_TIMEOUT + 30)
                r4_results[r["label"]] = r

    # Extract final positions (accept → revised_position; else → own_position)
    final_positions = {}
    for m in MASTERS:
        lbl = label_map[m]
        r3 = r3_results.get(lbl)
        if r3 and r3.get("action") == "accept" and r3.get("revised_position"):
            final_positions[m] = str(r3["revised_position"])
        else:
            final_positions[m] = own_position_by_master[m]

    # Convergence assessment
    actions = [r.get("action", "acknowledge") for r in r3_results.values()]
    if any(a == "accept" for a in actions) and not any(a == "rebut" for a in actions):
        convergence = "converged"
    elif any(a == "accept" for a in actions):
        convergence = "narrowed"
    else:
        convergence = "unchanged"

    return {
        "dispute_id": dispute["dispute_id"],
        "label_map": label_map,
        "round1": r1_results,
        "round2": r2_results,
        "round3": r3_results,
        "round4": r4_results,
        "closing_ran": needs_closing,
        "final_positions_by_master": final_positions,
        "convergence": convergence,
        "rounds_taken": 4 if needs_closing else 3,
    }


def _format_transcript_so_far(dispute: dict, label_map: dict,
                                r1: dict, r2: dict, r3: dict) -> str:
    lines = []
    lines.append(f"Round 1 Positions:")
    for lbl in ["A", "B", "C"]:
        pos = r1.get(lbl, {}).get("position_text", "")
        lines.append(f"  {lbl}: {pos}")
    lines.append("\nRound 2 Rebuttals:")
    for lbl in ["A", "B", "C"]:
        rb = r2.get(lbl, {})
        lines.append(f"  {lbl} → {rb.get('target', '?')}: {rb.get('rebuttal_text', '')}")
    lines.append("\nRound 3 Responses:")
    for lbl in ["A", "B", "C"]:
        rp = r3.get(lbl, {})
        if rp:
            lines.append(f"  {lbl} ({rp.get('action')}): {rp.get('response_text', '')}")
    return "\n".join(lines)


def render_transcript_md(dispute: dict, result: dict) -> str:
    """Render the dispute's full transcript as markdown for permanent archive."""
    lines = [
        f"# Cluster {dispute['dispute_id']} 交叉辩论 — {dispute.get('canonical_claim', '')[:60]}",
        "",
        f"**rule_subject**: {dispute.get('rule_subject')}",
        f"**dispute_type**: {dispute.get('dispute_type')}",
        f"**convergence**: {result['convergence']}",
        "",
        "## Round 1 Position Statements", "",
    ]
    for lbl in ["A", "B", "C"]:
        pos = result["round1"].get(lbl, {}).get("position_text", "")
        lines.append(f"**Framework {lbl}**: {pos}")
        lines.append("")

    lines.append("## Round 2 Rebuttals")
    lines.append("")
    for lbl in ["A", "B", "C"]:
        r2 = result["round2"].get(lbl, {})
        target = r2.get("target", "?")
        text = r2.get("rebuttal_text", "")
        lines.append(f"**{lbl} 质疑 {target}**: {text}")
        lines.append("")

    lines.append("## Round 3 Responses")
    lines.append("")
    for lbl in ["A", "B", "C"]:
        r3 = result["round3"].get(lbl)
        if not r3:
            continue
        action = r3.get("action", "")
        text = r3.get("response_text", "")
        lines.append(f"**{lbl} 回应** (action: {action}): {text}")
        if r3.get("revised_position"):
            lines.append(f"  修正立场: {r3['revised_position']}")
        lines.append("")

    if result.get("closing_ran"):
        lines.append("## Round 4 Closing Statements")
        lines.append("")
        for lbl in ["A", "B", "C"]:
            r4 = result["round4"].get(lbl, {})
            text = r4.get("closing_text", "")
            lines.append(f"**{lbl}**: {text}")
            lines.append("")

    lines.append("## Final Positions (for Phase 3b voting)")
    lines.append("")
    for m, pos in result["final_positions_by_master"].items():
        lbl = result["label_map"].get(m, "?")
        # NOTE: In transcript file, we use label not master name — Phase E compliance.
        lines.append(f"- **Framework {lbl}**: {pos}")
    lines.append("")

    lines.append("## 分歧收窄 & 仍存")
    if result["convergence"] == "converged":
        lines.append("- 三方立场经辩论后收敛到同方向，可进入 Phase 3b 投票")
    elif result["convergence"] == "narrowed":
        lines.append("- 部分方接受修正，立场收窄但未完全一致")
    else:
        lines.append("- 三方立场未收敛，将进入 Phase 3b 投票表决")

    return "\n".join(lines)


# ─────────── Main ───────────

def load_revised_seeds_by_master() -> dict:
    out: dict = {}
    for m in MASTERS:
        p = PREP_DIR / f"phase2_5_{m}_revised_seeds.jsonl"
        if not p.exists():
            out[m] = []
            continue
        seeds = []
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    seeds.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        out[m] = seeds
    return out


def phase2_75_cross_rebuttal(debate_id: str,
                                phase2_matrix: Optional[list[dict]] = None) -> dict:
    """Main entry for Phase 2.75.

    Writes transcripts to Principles/history/{debate_id}/debate_transcript_*.md
    and a summary to prep/phase2_75_summary.json.
    """
    if phase2_matrix is None:
        from scripts.soul.board.revise import load_phase2_matrix
        phase2_matrix = load_phase2_matrix()

    revised_seeds = load_revised_seeds_by_master()
    disputes = identify_dispute_clusters(revised_seeds, phase2_matrix)
    print(f"[phase2.75] Found {len(disputes)} dispute clusters")

    history_dir = HISTORY_DIR / debate_id
    history_dir.mkdir(parents=True, exist_ok=True)

    transcript_paths = []
    dispute_results = []

    # Run disputes sequentially; inside each, rounds have parallelism
    for dispute in disputes:
        print(f"[phase2.75] Running debate for {dispute['dispute_id']}")
        try:
            result = run_dispute(dispute)
        except Exception as e:
            print(f"[phase2.75] ERROR in {dispute['dispute_id']}: {e}")
            result = {"dispute_id": dispute["dispute_id"],
                      "error": str(e),
                      "convergence": "error",
                      "final_positions_by_master": {},
                      "rounds_taken": 0}
        dispute_results.append(result)

        # Render transcript (even on error — partial data is useful)
        try:
            md = render_transcript_md(dispute, result)
            path = history_dir / f"debate_transcript_{dispute['dispute_id']}.md"
            path.write_text(md, encoding="utf-8")
            transcript_paths.append(str(path))
        except Exception as e:
            print(f"[phase2.75] transcript render error: {e}")

    summary = {
        "debate_id": debate_id,
        "total_disputes": len(disputes),
        "convergence_stats": {
            "converged": sum(1 for r in dispute_results if r.get("convergence") == "converged"),
            "narrowed": sum(1 for r in dispute_results if r.get("convergence") == "narrowed"),
            "unchanged": sum(1 for r in dispute_results if r.get("convergence") == "unchanged"),
            "error": sum(1 for r in dispute_results if r.get("convergence") == "error"),
        },
        "transcript_paths": transcript_paths,
        "disputes": [
            {
                "dispute_id": d["dispute_id"],
                "canonical_claim": d.get("canonical_claim"),
                "dispute_type": d.get("dispute_type"),
                "convergence": r.get("convergence"),
                "final_positions_by_master": r.get("final_positions_by_master"),
            }
            for d, r in zip(disputes, dispute_results)
        ],
    }
    summary_path = PREP_DIR / "phase2_75_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
