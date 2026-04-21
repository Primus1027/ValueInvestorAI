"""Phase 3c: Render + Circuit Breaker.

Takes all phase 3b votes (qual + quant + sev) and produces:
- Principles/v{N}.md (HARD + L2 with variants)
- Principles/v{N}.schema.json (machine-executable)
- Principles/soul-level-preferences-v{N}.md (SOFT + DROPPED)
- Updates Principles/follow_up_agenda.md
- Updates Principles/dropped-archive.md
- Runs Circuit Breaker; if passed, symlinks current.md → v{N}.md
  Otherwise writes to v{N}_quarantine.md and keeps current.md pointing to previous.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PRINCIPLES_DIR, PREP_DIR, MASTERS, SEVERITY_ORDER, RULE_SUBJECTS,
)
from scripts.soul.board.agenda_tracker import AgendaTracker
from scripts.soul.board.dropped_tracker import DroppedTracker


def load_clusters() -> list[dict]:
    from scripts.soul.board.vote_qualitative import load_clusters as lc
    return lc()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def determine_next_version() -> str:
    """Figure out next v{N}.md filename by scanning existing versions."""
    existing = []
    for p in PRINCIPLES_DIR.glob("v*.md"):
        m = re.match(r"^v(\d+(?:\.\d+)*)\.md$", p.name)
        if m:
            existing.append(m.group(1))
    if not existing:
        return "v1.1"  # first v0.4.1 run → v1.1 (v1.0 already exists from Pre-A)
    # Parse version tuples, find max, increment minor
    def parse(v):
        return tuple(int(x) for x in v.split("."))
    existing_tuples = sorted(parse(v) for v in existing)
    latest = existing_tuples[-1]
    # If latest = (1, 0), next = (1, 1); if (1, 1), next = (1, 2); etc.
    next_minor = latest[:-1] + (latest[-1] + 1,)
    return "v" + ".".join(str(x) for x in next_minor)


# ─────────── Circuit Breaker ───────────

def count_hard_in_md(md_text: str) -> int:
    """Count ### headers matching numbered HARD entries.

    Matches both v1.0 format (`### 1. ROIC ...`) and v1.1+ format
    (`### 1. Business model ...`). Does not match higher-level headings.
    """
    return len(re.findall(r"^###\s+\d+\.", md_text, flags=re.MULTILINE))


def count_veto_in_md(md_text: str) -> int:
    """Count veto severity occurrences in rendered HARD entries.

    Matches v1.0 format `- **Severity**: \`veto\`` and v1.1+ format
    `- **Severity (Layer 0)**: \`veto\``. The key markers are:
      - line starts with optional `- ` (bullet)
      - contains `Severity` (possibly wrapped in `**…**` or followed by `(…)`)
      - followed by `veto` within the same logical line.
    """
    # Tolerant pattern: any flavor of "Severity<anything>: <backtick?>veto<backtick?>"
    pattern = re.compile(
        r"Severity[^\n:]*:\s*`?veto`?",
        flags=re.IGNORECASE,
    )
    return len(pattern.findall(md_text))


def circuit_breaker(new_clusters: list[dict], new_md_text: str,
                     prev_principles_path: Optional[Path],
                     phase2_5_fallback_count: int) -> dict:
    """3 gates: regression_guard, drift_guard, health_check.

    Distinguishes "no prior version" (skip regression/drift gates) from
    "prior version parsed as 0 HARD rules" (parse failure — require manual
    investigation).
    """
    # Prev stats
    prev_hard, prev_veto = 0, 0
    prev_file_exists = prev_principles_path is not None and prev_principles_path.exists()
    prev_parse_failed = False
    if prev_file_exists:
        try:
            prev_text = prev_principles_path.read_text(encoding="utf-8")
            prev_hard = count_hard_in_md(prev_text)
            prev_veto = count_veto_in_md(prev_text)
            # If the file has content but we parsed 0 HARD, the format likely
            # doesn't match our regex — flag as parse failure rather than
            # silently passing gate1.
            if prev_hard == 0 and len(prev_text.strip()) > 100:
                prev_parse_failed = True
        except Exception:
            prev_parse_failed = True

    # New stats (based on the rendered clusters)
    new_hard = sum(1 for c in new_clusters if c.get("_render_level") in ("L1", "L2"))
    new_veto = sum(1 for c in new_clusters
                   if c.get("_render_level") in ("L1", "L2")
                   and c.get("_layer0_severity") == "veto")

    # Gate 1: regression_guard
    #   - If no prior version → pass (first-ever run, nothing to regress against)
    #   - If prior exists with known HARD count → require new >= prev * 0.7
    #   - If prior exists but parse failed (unknown format) → fail (require manual check)
    if not prev_file_exists:
        gate1_pass = True
        gate1_threshold = 0
        gate1_note = "no_prior_version"
    elif prev_parse_failed:
        gate1_pass = False
        gate1_threshold = 0
        gate1_note = "prev_version_parse_failed_manual_check_required"
    else:
        gate1_threshold = prev_hard * 0.7
        gate1_pass = new_hard >= gate1_threshold
        gate1_note = "compared_against_prev"

    # Gate 2: drift_guard — veto ratio drop <= 30% (only meaningful if prev parsed)
    prev_veto_ratio = (prev_veto / prev_hard) if prev_hard > 0 else 0.0
    new_veto_ratio = (new_veto / new_hard) if new_hard > 0 else 0.0
    if prev_veto_ratio > 0:
        veto_ratio_drop = (prev_veto_ratio - new_veto_ratio) / prev_veto_ratio
        gate2_pass = veto_ratio_drop <= 0.30
    else:
        # No prev veto ratio to compare against → skip this gate
        veto_ratio_drop = 0.0
        gate2_pass = True

    # Gate 3: health_check — Phase 2.5 fallback masters < 2
    gate3_pass = phase2_5_fallback_count < 2

    return {
        "regression_guard": {
            "pass": gate1_pass,
            "new_hard": new_hard,
            "prev_hard": prev_hard,
            "threshold": gate1_threshold,
            "note": gate1_note,
        },
        "drift_guard": {
            "pass": gate2_pass,
            "new_veto_ratio": round(new_veto_ratio, 3),
            "prev_veto_ratio": round(prev_veto_ratio, 3),
            "drop": round(veto_ratio_drop, 3),
        },
        "health_check": {
            "pass": gate3_pass,
            "phase2_5_fallback_count": phase2_5_fallback_count,
        },
        "all_pass": gate1_pass and gate2_pass and gate3_pass,
    }


# ─────────── Rendering ───────────

SEVERITY_DESCRIPTIONS = {
    "veto": "评估返回 `{passed: false}`，拦截投资决策",
    "warning": "评估返回 `{passed: true, warnings: [...]}`",
    "note": "Agent 决策输出必须显式引用本条并论证为什么本次决策不受约束。未引用或论证不充分 → 决策输出视为无效",
}


def _md_header(version: str, now_iso: str, hard_count: int) -> str:
    return f"""# ValueInvestorAI Principles {version}

> Generated: {now_iso}
> Version: {version}
> Status: **自动生效（通过 circuit breaker 后自动 symlink 为 current）**

## 概述

本文档是 ValueInvestorAI 五层防线架构的 **Layer 0 硬约束**。
所有条款由三个独立价值投资方法论框架（W / C / Y）的研究助手
经过 Phase 1 独立提案 → Phase 2 pairwise equivalence → Phase 2.5 revise →
Phase 2.75 Cross-Rebuttal → Phase 3 voting 产出。

**总计 HARD 条款：{hard_count}**

"""


def _render_cluster_entry(idx: int, cluster: dict) -> str:
    """Render one HARD / L2 cluster as Markdown section."""
    c = cluster
    claim = c.get("canonical_claim", "")
    sev = c.get("_layer0_severity", "warning")
    render_level = c.get("_render_level", "L2")

    out = [
        f"### {idx}. {claim}",
        "",
        f"- **Cluster ID**: `{c.get('cluster_id')}`",
        f"- **Rule Subject**: `{c.get('rule_subject')}`",
        f"- **Theme**: `{c.get('canonical_theme')}`",
        f"- **Category**: `{c.get('category_primary')}`",
        f"- **Severity (Layer 0)**: `{sev}` — {SEVERITY_DESCRIPTIONS.get(sev, '')}",
        f"- **Consensus Level**: {render_level}",
    ]

    # Threshold variants
    t_variants = c.get("thresholds_variants_by_master")
    if t_variants and any(v is not None for v in t_variants.values()):
        out.append(f"- **Layer 0 Threshold (lowest consensus)**: `{c.get('_layer0_threshold')}`")
        out.append(f"- **Threshold variants by master**:")
        for m in MASTERS:
            if m in t_variants:
                out.append(f"  - `{m}`: {t_variants[m]}")

    # Severity variants
    s_variants = c.get("severity_variants_by_master", {})
    if s_variants and len(set(s_variants.values())) > 1:
        out.append(f"- **Severity variants by master**:")
        for m in MASTERS:
            if m in s_variants:
                out.append(f"  - `{m}`: {s_variants[m]}")

    # Variant seeds
    out.append("")
    out.append("**Variant seeds**:")
    for v in c.get("variant_seeds", []):
        out.append(f"  - **{v.get('master')}**: {v.get('claim', '')[:150]}")

    out.append("")
    return "\n".join(out)


def render_principles_md(version: str, clusters: list[dict]) -> str:
    now = datetime.now().isoformat(timespec="seconds")

    # Split by rule_subject
    hard_or_l2 = [c for c in clusters if c.get("_render_level") in ("L1", "L2")]
    target_clusters = [c for c in hard_or_l2 if c.get("rule_subject") == "target"]
    self_clusters = [c for c in hard_or_l2 if c.get("rule_subject") == "self"]
    dp_clusters = [c for c in hard_or_l2 if c.get("rule_subject") == "decision_process"]

    lines = [_md_header(version, now, len(hard_or_l2))]

    if target_clusters:
        lines.append("## Target 约束（约束被投标的）")
        lines.append("")
        for i, c in enumerate(target_clusters, 1):
            lines.append(_render_cluster_entry(i, c))

    if self_clusters:
        lines.append("## Self 约束（约束投资机构/投资人自身）")
        lines.append("")
        for i, c in enumerate(self_clusters, 1):
            lines.append(_render_cluster_entry(i, c))

    if dp_clusters:
        lines.append("## Decision Process 约束（约束分析流程本身）")
        lines.append("")
        for i, c in enumerate(dp_clusters, 1):
            lines.append(_render_cluster_entry(i, c))

    lines.append("\n---\n\n## Layer 0 执行说明\n")
    lines.append("每条条款的 `severity` 决定 PrinciplesEngine 的行为：\n")
    for sev, desc in SEVERITY_DESCRIPTIONS.items():
        lines.append(f"- `{sev}`: {desc}")

    lines.append(f"\n机器可执行版本：`{version}.schema.json`\n")
    lines.append(f"Follow-up agenda: `follow_up_agenda.md`\n")
    return "\n".join(lines)


def render_schema_json(version: str, clusters: list[dict]) -> dict:
    hard_or_l2 = [c for c in clusters if c.get("_render_level") in ("L1", "L2")]

    rules = []
    for c in hard_or_l2:
        rules.append({
            "cluster_id": c.get("cluster_id"),
            "rule_subject": c.get("rule_subject"),
            "canonical_claim": c.get("canonical_claim"),
            "theme": c.get("canonical_theme"),
            "category_primary": c.get("category_primary"),
            "categories_secondary": c.get("categories_secondary", []),
            "layer0_severity": c.get("_layer0_severity"),
            "layer0_threshold": c.get("_layer0_threshold"),
            "layer0_operator": c.get("_layer0_operator"),
            "layer0_data_field": c.get("_layer0_data_field"),
            "variant_seeds_by_master": {
                v.get("master"): {
                    "seed_id": v.get("seed_id"),
                    "claim": v.get("claim"),
                    "threshold": v.get("threshold"),
                    "severity": v.get("severity"),
                    "category": v.get("category"),
                    "supporting_section_id": v.get("supporting_section_id"),
                }
                for v in c.get("variant_seeds", [])
            },
            "support_count": c.get("support_count"),
            "render_level": c.get("_render_level"),
        })

    return {
        "version": version,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "schema_version": "v1.1",
        "hard_rules": rules,
        "total_hard_count": len(rules),
    }


def render_soul_level_md(version: str, clusters: list[dict]) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    l3_clusters = [c for c in clusters if c.get("_render_level") == "L3"]
    singleton_clusters = [c for c in clusters
                           if c.get("support_count") == 1 and c.get("_render_level") != "L1"
                           and c.get("_render_level") != "L2"]

    lines = [
        f"# Soul-Level Preferences {version}",
        "",
        f"> Generated: {now}",
        f"> Contains: L3 (qualitative disagreement) + singletons (1/3 support)",
        f"> These are NOT Layer 0. Layer 1 Agent may consult for broader methodology context.",
        "",
        f"Total: {len(l3_clusters) + len(singleton_clusters)}",
        "",
    ]

    if l3_clusters:
        lines.append("## L3 — Qualitative Disagreement (< 2/3 support)")
        lines.append("")
        for c in l3_clusters:
            lines.append(f"### `{c.get('cluster_id')}` — {c.get('canonical_claim')}")
            lines.append(f"- rule_subject: {c.get('rule_subject')}")
            lines.append(f"- support_count: {c.get('support_count')}")
            lines.append(f"- masters: {[v.get('master') for v in c.get('variant_seeds', [])]}")
            lines.append("")

    if singleton_clusters:
        lines.append("## Singletons — Only one master proposed this")
        lines.append("")
        for c in singleton_clusters:
            lines.append(f"### `{c.get('cluster_id')}` — {c.get('canonical_claim')}")
            # Defensive: variant_seeds could be None, empty list, or missing
            variants = c.get("variant_seeds") or []
            v0 = variants[0] if variants else {}
            lines.append(f"- master: {v0.get('master')}")
            lines.append(f"- rule_subject: {c.get('rule_subject')}")
            lines.append(f"- severity: {v0.get('severity')}")
            lines.append("")

    return "\n".join(lines)


# ─────────── Main entry ───────────

def phase3c_render_and_gate(debate_id: str) -> dict:
    """Main Phase 3c entry.

    Reads:
      prep/phase3a_clusters.jsonl
      prep/phase3b_qual_votes.jsonl
      prep/phase3b_quant_votes.jsonl
      prep/phase3b_sev_votes.jsonl
      prep/phase2_5_summary.json (for fallback_count)

    Writes:
      Principles/v{N}.md (or v{N}_quarantine.md if circuit breaker fails)
      Principles/v{N}.schema.json
      Principles/soul-level-preferences-v{N}.md
      Principles/critique_matrix_v{N}.jsonl
    Updates:
      Principles/follow_up_agenda.md
      Principles/dropped-archive.md
      Principles/current.md (symlink, if circuit breaker passes)
    """
    clusters = load_clusters()
    qual_votes = {v["cluster_id"]: v for v in load_jsonl(PREP_DIR / "phase3b_qual_votes.jsonl")}
    quant_votes = {v["cluster_id"]: v for v in load_jsonl(PREP_DIR / "phase3b_quant_votes.jsonl")}
    sev_votes = {v["cluster_id"]: v for v in load_jsonl(PREP_DIR / "phase3b_sev_votes.jsonl")}

    phase2_5_summary = {}
    if (PREP_DIR / "phase2_5_summary.json").exists():
        phase2_5_summary = json.loads(
            (PREP_DIR / "phase2_5_summary.json").read_text(encoding="utf-8"))
    fallback_count = phase2_5_summary.get("fallback_count", 0)

    # Decorate clusters with their final render_level + layer0 values
    for c in clusters:
        cid = c.get("cluster_id")
        qv = qual_votes.get(cid)
        if not qv:
            # No qual vote → singleton or drop candidate
            c["_render_level"] = "L3" if c.get("support_count", 1) >= 2 else "singleton"
            continue

        decision = qv.get("decision", "L3")
        c["_render_level"] = decision

        if decision in ("L1", "L2"):
            qtv = quant_votes.get(cid)
            if qtv:
                consensus = qtv.get("consensus", {})
                c["_layer0_threshold"] = consensus.get("layer0_threshold")
                c["thresholds_variants_by_master"] = consensus.get("variant_thresholds_by_master", {})
                # Pick operator and data_field from any master's proposal
                for m, prop in qtv.get("proposals_by_master", {}).items():
                    if prop.get("proposed_operator") and not c.get("_layer0_operator"):
                        c["_layer0_operator"] = prop.get("proposed_operator")
                        c["_layer0_data_field"] = prop.get("proposed_data_field")
                        break
            sv = sev_votes.get(cid)
            if sv:
                c["_layer0_severity"] = sv.get("consensus", {}).get("layer0_severity", "warning")
            else:
                c["_layer0_severity"] = "warning"

    # Determine version number
    version = determine_next_version()

    # Render
    md_text = render_principles_md(version, clusters)
    schema = render_schema_json(version, clusters)
    soul_level_md = render_soul_level_md(version, clusters)

    # Circuit breaker
    prev_current = PRINCIPLES_DIR / "current.md"
    prev_resolved = None
    if prev_current.exists() and prev_current.is_symlink():
        try:
            prev_resolved = prev_current.resolve()
        except Exception:
            prev_resolved = None
    elif prev_current.exists():
        prev_resolved = prev_current

    cb = circuit_breaker(clusters, md_text, prev_resolved, fallback_count)

    # Write outputs
    PRINCIPLES_DIR.mkdir(parents=True, exist_ok=True)
    principles_filename = f"{version}.md" if cb["all_pass"] else f"{version}_quarantine.md"
    schema_filename = f"{version}.schema.json" if cb["all_pass"] else f"{version}_quarantine.schema.json"

    principles_path = PRINCIPLES_DIR / principles_filename
    schema_path = PRINCIPLES_DIR / schema_filename
    soul_level_path = PRINCIPLES_DIR / f"soul-level-preferences-{version}.md"

    principles_path.write_text(md_text, encoding="utf-8")
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    soul_level_path.write_text(soul_level_md, encoding="utf-8")

    # critique_matrix
    cm_path = PRINCIPLES_DIR / f"critique_matrix_{version}.jsonl"
    with cm_path.open("w", encoding="utf-8") as f:
        for c in clusters:
            cid = c.get("cluster_id")
            entry = {
                "cluster_id": cid,
                "canonical_claim": c.get("canonical_claim"),
                "render_level": c.get("_render_level"),
                "qual_vote": qual_votes.get(cid),
                "quant_vote": quant_votes.get(cid),
                "sev_vote": sev_votes.get(cid),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Symlink current.md only if passed.
    # Downgrade to "quarantine" if symlink creation fails (Windows without
    # elevation, unsupported filesystem, etc.) — never let the pipeline claim
    # "published" when the symlink is actually broken.
    symlink_failed = False
    symlink_error_msg = None
    if cb["all_pass"]:
        current_link = PRINCIPLES_DIR / "current.md"
        current_schema_link = PRINCIPLES_DIR / "current.schema.json"
        try:
            if current_link.is_symlink() or current_link.exists():
                current_link.unlink()
            os.symlink(principles_filename, current_link)
            if current_schema_link.is_symlink() or current_schema_link.exists():
                current_schema_link.unlink()
            os.symlink(schema_filename, current_schema_link)
        except OSError as e:
            symlink_failed = True
            symlink_error_msg = str(e)
            print(f"[phase3c] Symlink creation failed, marking quarantine: {e}")
            # Downgrade circuit breaker verdict
            cb["all_pass"] = False
            cb["symlink_failure"] = {"error": symlink_error_msg}
            # Rename published files to quarantine counterparts
            try:
                new_pr = PRINCIPLES_DIR / f"{version}_quarantine.md"
                new_sc = PRINCIPLES_DIR / f"{version}_quarantine.schema.json"
                principles_path.rename(new_pr)
                schema_path.rename(new_sc)
                principles_path = new_pr
                schema_path = new_sc
            except OSError as rename_err:
                print(f"[phase3c] Quarantine rename failed (non-fatal): {rename_err}")

    # Update agenda — full lifecycle: resolve, add new, demote stale
    at = AgendaTracker()

    # Step 1: try to RESOLVE any pre-existing agenda items whose cluster reached
    # the upgraded threshold/severity in this debate.
    for cid, qtv in quant_votes.items():
        consensus = qtv.get("consensus", {}) or {}
        layer0_t = consensus.get("layer0_threshold")
        if layer0_t is not None:
            at.resolve_item(cid, "quant_upgrade", str(layer0_t),
                            debate_id, "new consensus threshold reached")
    for cid, sv in sev_votes.items():
        consensus = sv.get("consensus", {}) or {}
        layer0_s = consensus.get("layer0_severity")
        if layer0_s:
            at.resolve_item(cid, "severity_upgrade", layer0_s,
                            debate_id, "new consensus severity reached")

    # Step 2: ADD new upgrade items for this debate's remaining variants
    for cid, qtv in quant_votes.items():
        for item in qtv.get("consensus", {}).get("follow_up_items", []):
            cluster = next((c for c in clusters if c.get("cluster_id") == cid), None)
            if not cluster:
                continue
            at.add_quant_upgrade(
                cluster_id=cid,
                current_threshold=qtv["consensus"].get("layer0_threshold"),
                proposed_by_master={item["master"]: item["to_threshold"]},
                proposed_rationale={item["master"]: item.get("rationale", "")},
                canonical_claim=cluster.get("canonical_claim", ""),
                rule_subject=cluster.get("rule_subject", ""),
                current_debate_id=debate_id,
            )
    for cid, sv in sev_votes.items():
        for item in sv.get("consensus", {}).get("upgrade_agenda_items", []):
            cluster = next((c for c in clusters if c.get("cluster_id") == cid), None)
            if not cluster:
                continue
            at.add_severity_upgrade(
                cluster_id=cid,
                current_severity=sv["consensus"].get("layer0_severity"),
                proposed_by_master={item["master"]: item["to_severity"]},
                proposed_rationale={item["master"]: ""},
                canonical_claim=cluster.get("canonical_claim", ""),
                rule_subject=cluster.get("rule_subject", ""),
                current_debate_id=debate_id,
            )

    # Step 3: DEMOTE stale (4 quarters unresolved → dormant)
    demote_result = at.mark_stale_and_demote(debate_id)

    at.save()

    # Update dropped tracker: for L3 clusters, record drop
    dt = DroppedTracker()
    for c in clusters:
        if c.get("_render_level") == "L3":
            cid = c.get("cluster_id")
            qv = qual_votes.get(cid) or {}
            support = (qv.get("final_outcome") or {}).get("support_count", 0)
            # Check if this was re-introduced — if so, record as re-intro failure
            is_reintro = any(v.get("_reintroduced_from") or False
                             for v in c.get("variant_seeds", []))
            if is_reintro and dt.is_archived(cid):
                dt.record_reintroduction_failure(cid, debate_id, support)
            else:
                dt.record_drop(
                    cluster_id=cid,
                    debate_id=debate_id,
                    support_count=support,
                    canonical_claim=c.get("canonical_claim", ""),
                    rule_subject=c.get("rule_subject", "target"),
                    category=c.get("category_primary", "quantitative_hard"),
                )
        elif c.get("_render_level") in ("L1", "L2"):
            # If this cluster was previously archived but now passes, promote
            cid = c.get("cluster_id")
            if dt.is_archived(cid):
                dt.promote_from_dropped(cid)
    dt.save()

    result = {
        "debate_id": debate_id,
        "version": version,
        "published": cb["all_pass"],
        "circuit_breaker": cb,
        "principles_path": str(principles_path),
        "schema_path": str(schema_path),
        "soul_level_path": str(soul_level_path),
        "critique_matrix_path": str(cm_path),
        "quarantine_path": None if cb["all_pass"] else str(principles_path),
        "quarantine_reasons": [
            k for k, v in cb.items()
            if isinstance(v, dict) and not v.get("pass", True) and k != "symlink_failure"
        ] + (["symlink_failure"] if symlink_failed else [])
        if not cb["all_pass"] else [],
        "hard_count": sum(1 for c in clusters if c.get("_render_level") in ("L1", "L2")),
        "l3_count": sum(1 for c in clusters if c.get("_render_level") == "L3"),
    }
    (PREP_DIR / "phase3c_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
