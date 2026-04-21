"""Phase 3b-qual: Qualitative direction voting.

For each cluster from Phase 3a:
  Round 1: 3 masters parallel vote (support / oppose / abstain + rationale)
  Round 2 (conditional): if 2/3 support + 1 oppose, oppose master sees
    supporters' rationales and re-votes

Decision mapping:
  3/3 support or (2 support + 1 abstain) → pass to L1/L2
  2 support + 1 oppose after Round 2 re-vote still 1 oppose → DROP
  < 2 support → DROP
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR, HISTORY_DIR, MASTERS, master_display_name,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

QUAL_VOTE_TIMEOUT = 180


def find_transcript_path(debate_id: str, cluster: dict) -> Optional[Path]:
    """Find debate transcript for a cluster; return None if no transcript exists."""
    history_dir = HISTORY_DIR / debate_id
    if not history_dir.exists():
        return None
    # Try multiple naming patterns: cluster_id, dispute_<root_seed>
    cid = cluster.get("cluster_id", "")
    for pattern in [f"debate_transcript_{cid}.md",
                    f"debate_transcript_dispute_{cid}.md"]:
        p = history_dir / pattern
        if p.exists():
            return p
    # Also try matching by root seed in variant_seeds
    for v in cluster.get("variant_seeds", []):
        sid = v.get("seed_id")
        if sid:
            p = history_dir / f"debate_transcript_dispute_{sid}.md"
            if p.exists():
                return p
    return None


def render_qual_vote_prompt(master: str, cluster: dict,
                              transcript_path: Optional[Path]) -> str:
    template = (PROMPTS_DIR / "phase3b_qual_vote.md").read_text(encoding="utf-8")

    transcript_text = ""
    own_final_position = ""
    if transcript_path and transcript_path.exists():
        transcript_text = transcript_path.read_text(encoding="utf-8")
        # Extract own position from transcript final_positions section
        # This is best-effort; transcript uses labels not master names
        # For vote prompt, we rely on transcript being self-explanatory
        own_final_position = "(在 transcript 的 Final Positions 部分查看本框架立场)"
    else:
        transcript_text = "(本 cluster 无 Phase 2.75 辩论 — 直接投票)"
        own_final_position = "(无)"

    return template.format(
        master=master,
        master_display_name=master_display_name(master),
        cluster_id=cluster.get("cluster_id"),
        canonical_claim=cluster.get("canonical_claim", ""),
        rule_subject=cluster.get("rule_subject", ""),
        canonical_theme=cluster.get("canonical_theme", ""),
        variant_seeds=json.dumps(cluster.get("variant_seeds", []), ensure_ascii=False, indent=2),
        transcript_text=transcript_text[:8000],  # cap
        own_final_position=own_final_position,
    )


def call_qual_vote_for_master(master: str, cluster: dict,
                                transcript_path: Optional[Path]) -> dict:
    prompt = render_qual_vote_prompt(master, cluster, transcript_path)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=QUAL_VOTE_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"master": master, "stance": "abstain",
                    "rationale": f"error: exit {res.returncode}",
                    "transcript_refs": []}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["stance", "rationale", "transcript_refs"])
        if not parsed:
            return {"master": master, "stance": "abstain",
                    "rationale": "parse_fail", "transcript_refs": []}
        stance = str(parsed.get("stance", "abstain"))
        if stance not in ("support", "oppose", "abstain"):
            stance = "abstain"
        refs = parsed.get("transcript_refs", [])
        if not isinstance(refs, list):
            refs = []
        return {
            "master": master,
            "stance": stance,
            "rationale": str(parsed.get("rationale", ""))[:500],
            "transcript_refs": [str(r) for r in refs[:10]],
        }
    except Exception as e:
        return {"master": master, "stance": "abstain",
                "rationale": f"error: {e}", "transcript_refs": []}


def run_qual_vote_round_for_cluster(cluster: dict,
                                       transcript_path: Optional[Path]) -> dict:
    """Round 1 of qualitative voting — 3 parallel calls."""
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(call_qual_vote_for_master, m, cluster, transcript_path): m
            for m in MASTERS
        }
        results = {}
        for fut in futures:
            r = fut.result(timeout=QUAL_VOTE_TIMEOUT + 30)
            results[r["master"]] = r
    return results


def compute_round_outcome(vote_results: dict) -> dict:
    """Count support / oppose / abstain; return outcome category.

    Categories:
    - "3_support" or "2_support_1_abstain" → pass (L1 or L2)
    - "2_support_1_oppose" → needs Round 2 re-vote
    - "< 2 support" → drop
    """
    stances = [v.get("stance") for v in vote_results.values()]
    support = stances.count("support")
    oppose = stances.count("oppose")
    abstain = stances.count("abstain")

    outcome = "drop"
    if support >= 2 and oppose == 0:
        outcome = "pass"
    elif support == 2 and oppose == 1:
        outcome = "needs_round2"
    elif support < 2:
        outcome = "drop"

    return {
        "support_count": support,
        "oppose_count": oppose,
        "abstain_count": abstain,
        "outcome": outcome,
    }


def run_round2_for_oppose_masters(cluster: dict,
                                     round1_results: dict,
                                     transcript_path: Optional[Path]) -> dict:
    """For oppose master(s), re-vote after seeing support rationales."""
    # Build mini-prompt injection: show support rationales to each oppose master
    supporters = [(m, r) for m, r in round1_results.items() if r.get("stance") == "support"]
    opposers = [(m, r) for m, r in round1_results.items() if r.get("stance") == "oppose"]

    round2_results: dict = {}
    for opp_master, _opp_round1 in opposers:
        # Construct augmented prompt with supporters' rationales
        base_prompt = render_qual_vote_prompt(opp_master, cluster, transcript_path)
        supp_ctx = "\n\n==== Round 2 RE-VOTE ====\n你在 Round 1 投了 oppose。以下是支持方的 rationales，请重新考虑：\n\n"
        for m, r in supporters:
            supp_ctx += f"- **{m}**: {r.get('rationale', '')}\n"
        supp_ctx += "\n你可改投 support / abstain，或坚持 oppose。请再次以同样 JSON 格式输出（stance / rationale / transcript_refs）。"

        full = base_prompt + supp_ctx
        try:
            res = subprocess.run(
                ["claude", "-p", full, "--model", "claude-sonnet-4-6",
                 "--output-format", "json"],
                capture_output=True, timeout=QUAL_VOTE_TIMEOUT, text=True,
            )
            if res.returncode != 0:
                round2_results[opp_master] = {
                    "master": opp_master, "stance": "oppose",
                    "rationale": f"Round 2 error: exit {res.returncode}",
                    "transcript_refs": [],
                }
                continue
            parsed = parse_claude_cli_result(res.stdout,
                                              expected_keys=["stance", "rationale", "transcript_refs"])
            if not parsed:
                round2_results[opp_master] = {
                    "master": opp_master, "stance": "oppose",
                    "rationale": "Round 2 parse fail",
                    "transcript_refs": [],
                }
                continue
            new_stance = str(parsed.get("stance", "oppose"))
            if new_stance not in ("support", "oppose", "abstain"):
                new_stance = "oppose"
            round2_results[opp_master] = {
                "master": opp_master,
                "stance": new_stance,
                "rationale": str(parsed.get("rationale", ""))[:500],
                "transcript_refs": parsed.get("transcript_refs", []),
            }
        except Exception as e:
            round2_results[opp_master] = {
                "master": opp_master, "stance": "oppose",
                "rationale": f"Round 2 error: {e}",
                "transcript_refs": [],
            }
    return round2_results


def qual_vote_cluster(cluster: dict, debate_id: str) -> dict:
    """Full qualitative voting for one cluster (possibly 2 rounds)."""
    transcript_path = find_transcript_path(debate_id, cluster)
    round1 = run_qual_vote_round_for_cluster(cluster, transcript_path)
    outcome1 = compute_round_outcome(round1)

    final_stances = dict(round1)
    round2 = None
    if outcome1["outcome"] == "needs_round2":
        round2 = run_round2_for_oppose_masters(cluster, round1, transcript_path)
        final_stances = dict(round1)
        final_stances.update(round2)

    final_outcome = compute_round_outcome(final_stances)
    # Final decision mapping
    decision = "L3"  # drop
    if final_outcome["outcome"] == "pass":
        if final_outcome["support_count"] == 3:
            decision = "L1"
        else:
            decision = "L2"  # 2+1abstain
    elif final_outcome["outcome"] == "needs_round2":
        # This only happens if after Round 2 still 2/1 oppose
        decision = "L3"  # drop — 1 master opposes
    else:
        decision = "L3"

    return {
        "cluster_id": cluster.get("cluster_id"),
        "transcript_used": str(transcript_path) if transcript_path else None,
        "round1_stances": round1,
        "round1_outcome": outcome1,
        "round2_stances": round2,
        "final_stances": final_stances,
        "final_outcome": final_outcome,
        "decision": decision,
    }


def load_clusters() -> list[dict]:
    p = PREP_DIR / "phase3a_clusters.jsonl"
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


def phase3b_qual_vote(debate_id: str) -> dict:
    """Main entry for Phase 3b-qual. Votes on all clusters from Phase 3a."""
    clusters = load_clusters()
    if not clusters:
        return {"error": "no_clusters_loaded"}

    results = []
    for cluster in clusters:
        print(f"[phase3b-qual] Voting on {cluster.get('cluster_id')}")
        vote_result = qual_vote_cluster(cluster, debate_id)
        results.append(vote_result)

    # Save
    out_path = PREP_DIR / "phase3b_qual_votes.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "debate_id": debate_id,
        "total_clusters_voted": len(results),
        "decision_counts": {
            "L1": sum(1 for r in results if r["decision"] == "L1"),
            "L2": sum(1 for r in results if r["decision"] == "L2"),
            "L3": sum(1 for r in results if r["decision"] == "L3"),
        },
        "output_path": str(out_path),
    }
    (PREP_DIR / "phase3b_qual_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return summary
