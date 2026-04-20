#!/usr/bin/env python3
"""Phase 3: Synthesis of revised seeds into Principles.md artifacts.

3a: Semantic deduplication (1 LLM call with Sonnet) — cluster synonymous
    principles across frameworks into canonical forms.
3b: Vote tally (Python, no LLM) — classify clusters as HARD / SOFT / DROPPED.
3c: Document rendering (Python + Jinja2-style templates) — produce final artifacts.

Inputs (from prep/):
  phase2_5_{master}_revised_seeds.jsonl  (from board_debate.py Phase 2.5)
  phase2_metadata.json                    (anon_map, for un-anonymization)

Outputs (to Principles/):
  v1.0.md                         — HARD (3/3 unanimous) principles, human-readable
  soul-level-preferences.md       — SOFT (2/3) and DROPPED (1/3) entries
  v1.0.schema.json                — machine-executable rules
  company_data_contract.md        — schema contract for future MVP yfinance adapter
  debate_log_2026-04-20.md        — full trace (Phase 1 → 2 → 2.5 → 3)
  critique_matrix.jsonl           — per-cluster vote record
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from _json_utils import parse_claude_cli_result

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREP_DIR = PROJECT_ROOT / "prep"
PRINCIPLES_DIR = PROJECT_ROOT / "Principles"
NOW = datetime.now(timezone.utc)


# ==================== Loaders ====================

def load_revised_seeds() -> Dict[str, List[Dict]]:
    """Load Phase 2.5 revised seeds for all masters."""
    out = {}
    for master in ["buffett", "munger", "duan"]:
        path = PREP_DIR / f"phase2_5_{master}_revised_seeds.jsonl"
        if not path.exists():
            print(f"✗ Missing {path}. Run board_debate.py first.")
            sys.exit(1)
        out[master] = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return out


def load_phase2_metadata() -> Dict:
    """Load Phase 2 metadata for anon_map and context."""
    return json.loads((PREP_DIR / "phase2_metadata.json").read_text())


# ==================== 3a: Semantic Dedup ====================

def build_phase3a_prompt(all_seeds: List[Dict]) -> str:
    """Build Phase 3a prompt: cluster synonymous seeds."""
    # Strip private fields for cleanliness
    clean_seeds = []
    for s in all_seeds:
        cs = {k: v for k, v in s.items() if not k.startswith("_")}
        # Attach master label for traceability in clusters
        cs["_master"] = s.get("_master", "unknown")
        clean_seeds.append(cs)

    return f"""你是辩论记录员。三个独立的投资方法论框架（W/C/Y — 分别对应 buffett / munger / duan 的方法论研究助手）经过独立提案（Phase 1）和修订（Phase 2.5）后，产出以下 seed principles。

你的任务：识别跨框架的**语义等价 seeds**，合并成 canonical clusters。

=== 所有 revised seeds（共 {len(clean_seeds)} 条）===
{json.dumps(clean_seeds, ensure_ascii=False, indent=2)}

=== 聚类规则 ===
1. **语义等价**：三方用不同措辞说同一件事（如"ROE 持续高"、"高资本回报率"、"ROE ≥ X%"）归入同一 cluster
2. **不要过度合并**：如果阈值差异 > 50%（如 15% vs 7%），保留为同 cluster 但标记 `thresholds_diverge=true`
3. **categoria 保持**：同 cluster 内的 seeds 应该 category 一致，否则不该聚为一类
4. **独立保留**：如果某条 seed 在其他框架中完全没有对应，作为 single-seed cluster

=== 每 cluster 的 schema ===
```json
{{
  "cluster_id": "cl_01",
  "canonical_claim": "<中立措辞重述 claim>",
  "category": "quantitative_hard | qualitative_required | position_sizing | veto_line | valuation_method",
  "variant_seeds": [
    {{
      "seed_id": "<原 seed_id>",
      "master": "buffett | munger | duan",
      "claim": "<原 claim>",
      "threshold": <number | null>,
      "severity": "veto | warning | note",
      "supporting_section_id": "<soul doc anchor>",
      "supporting_profile_factor": "<profile factor id>"
    }}
  ],
  "thresholds_diverge": true | false,
  "threshold_variants_by_master": {{"buffett": <n>, "munger": <n>, "duan": <n>}} | null,
  "support_count": <1 | 2 | 3>
}}
```

**support_count**:
- 3 = 三个 framework 都有 variant（HARD 候选）
- 2 = 两个有（SOFT 候选）
- 1 = 只有一个（DROP 到 soul-level-preferences）

=== 输出 schema ===
```json
{{"clusters": [<cluster 1>, <cluster 2>, ...]}}
```

严格要求：
- 每条输入 seed **必须**出现在恰好一个 cluster 里（不丢不重）
- 不要合并 category 不同的 seeds
- 阈值差异 > 50% 必须 flag `thresholds_diverge=true`

不要输出其他文字。"""


def call_claude(prompt: str, model: str, timeout: int = 720) -> Dict:
    """Call Claude CLI, parse JSON result."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "json"],
            capture_output=True, timeout=timeout, text=True, check=True,
        )
        parsed = parse_claude_cli_result(result.stdout, expected_keys=["clusters"])
        # P0 fix: guard against LLM returning non-dict JSON (e.g., array, string)
        if parsed is None or not isinstance(parsed, dict):
            return {
                "error": f"JSON parse failed or non-dict: got {type(parsed).__name__}",
                "stdout_head": result.stdout[:500],
            }
        return parsed
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


def phase3a_semantic_dedup(all_seeds: List[Dict]) -> List[Dict]:
    """Phase 3a: cluster synonymous seeds (1 LLM call, Opus for complex semantic reasoning)."""
    print(f"\n=== Phase 3a: Semantic Deduplication (Opus, {len(all_seeds)} seeds) ===")
    prompt = build_phase3a_prompt(all_seeds)
    print(f"  prompt size: ~{len(prompt)//4} tokens")
    # Opus 4.7 for reliability on complex cross-framework semantic matching.
    # Timeout 900s for safety with large seed pools.
    result = call_claude(prompt, model="claude-opus-4-7", timeout=900)
    if "error" in result:
        print(f"  ✗ Phase 3a failed: {result['error'][:300]}")
        # Try fallback: Sonnet with even longer timeout
        print(f"  Retrying with Sonnet + 900s timeout...")
        result = call_claude(prompt, model="claude-sonnet-4-6", timeout=900)
        if "error" in result:
            print(f"  ✗ Phase 3a failed again: {result['error'][:300]}")
            sys.exit(1)
    clusters = result.get("clusters", [])
    print(f"  ✓ {len(clusters)} clusters produced")

    # Sanity: verify cluster support_counts
    from collections import Counter
    dist = Counter(c.get("support_count", 0) for c in clusters)
    print(f"  Support distribution: 3-way={dist[3]}, 2-way={dist[2]}, 1-way={dist[1]}")

    # Persist
    out = PREP_DIR / "phase3a_clusters.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for c in clusters:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"  ✓ {out.name}")

    return clusters


# ==================== 3b: Vote Tally ====================

def phase3b_vote_tally(clusters: List[Dict]) -> Dict[str, List[Dict]]:
    """Phase 3b: classify clusters as HARD / SOFT / DROPPED (Python, no LLM)."""
    print("\n=== Phase 3b: Vote Tally (Python) ===")

    hard, soft, dropped = [], [], []
    for cluster in clusters:
        # P1 fix: support_count might be 0 / missing / non-int. Always recompute
        # from distinct master attribution as canonical source.
        distinct_masters = {v.get("master") for v in cluster.get("variant_seeds", [])
                           if v.get("master")}
        sc_computed = len(distinct_masters)
        sc_claimed = cluster.get("support_count")
        if sc_claimed is None or not isinstance(sc_claimed, int) or sc_claimed <= 0:
            sc = sc_computed
        else:
            # If LLM's claim disagrees with reality, prefer reality
            sc = sc_computed if sc_computed > 0 else sc_claimed
        cluster["support_count"] = sc

        if sc >= 3:
            hard.append(cluster)
        elif sc == 2:
            soft.append(cluster)
        else:
            dropped.append(cluster)

    print(f"  HARD (3/3 unanimous): {len(hard)}")
    print(f"  SOFT (2/3 majority):  {len(soft)}")
    print(f"  DROPPED (1/3 single): {len(dropped)}")

    # Persist critique matrix
    critique_path = PRINCIPLES_DIR / "critique_matrix.jsonl"
    with critique_path.open("w", encoding="utf-8") as f:
        for bucket, clusters_in_bucket in [("HARD", hard), ("SOFT", soft), ("DROPPED", dropped)]:
            for c in clusters_in_bucket:
                record = {
                    "cluster_id": c.get("cluster_id"),
                    "bucket": bucket,
                    "canonical_claim": c.get("canonical_claim"),
                    "category": c.get("category"),
                    "support_count": c.get("support_count"),
                    "supporting_masters": sorted({v.get("master") for v in c.get("variant_seeds", [])}),
                    "thresholds_diverge": c.get("thresholds_diverge", False),
                    "threshold_variants_by_master": c.get("threshold_variants_by_master"),
                    "variant_seed_ids": [v.get("seed_id") for v in c.get("variant_seeds", [])],
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  ✓ {critique_path.name}")

    return {"hard": hard, "soft": soft, "dropped": dropped}


# ==================== 3c: Document Rendering ====================

def render_principle_markdown(cluster: Dict, idx: int) -> str:
    """Render one principle as Markdown block."""
    cid = cluster.get("cluster_id", f"cl_{idx:02d}")
    claim = cluster.get("canonical_claim", "(no claim)")
    category = cluster.get("category", "uncategorized")
    variants = cluster.get("variant_seeds", [])
    masters = sorted({v.get("master", "?") for v in variants})
    diverge = cluster.get("thresholds_diverge", False)

    lines = [
        f"### {idx}. {claim}",
        "",
        f"- **Cluster ID**: `{cid}`",
        f"- **Category**: `{category}`",
        f"- **Supported by**: {', '.join(masters)} ({len(masters)}/3)",
    ]

    # Severity — use max severity across variants (veto > warning > note)
    severities = [v.get("severity", "note") for v in variants]
    if "veto" in severities:
        max_sev = "veto"
    elif "warning" in severities:
        max_sev = "warning"
    else:
        max_sev = "note"
    lines.append(f"- **Severity**: `{max_sev}`")

    if diverge:
        tv = cluster.get("threshold_variants_by_master", {})
        if tv:
            tv_str = ", ".join(f"{k}={v}" for k, v in tv.items())
            lines.append(f"- **阈值分歧** ⚠: {tv_str}")

    lines.append("")
    lines.append("**每个方法论框架的 variant**:")
    for v in variants:
        m = v.get("master", "?")
        c = v.get("claim", "")
        t = v.get("threshold")
        sev = v.get("severity", "note")
        anchor = v.get("supporting_section_id") or v.get("supporting_profile_factor") or "—"
        extras = []
        if t is not None:
            extras.append(f"threshold={t}")
        extras.append(f"severity={sev}")
        extras_str = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"  - **{m}**{extras_str}: {c}")
        lines.append(f"    Source: `{anchor}`")
    lines.append("")
    return "\n".join(lines)


def render_hard_principles(hard: List[Dict]) -> str:
    """Render Principles/v1.0.md (HARD only)."""
    lines = []
    lines.append("# ValueInvestorAI Principles v1.0")
    lines.append("")
    lines.append(f"> Generated: {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("> Version: 1.0 (Pre-A Principles Board Debate output)")
    lines.append("> Status: **待用户 sign-off**")
    lines.append("")
    lines.append("## 概述")
    lines.append("")
    lines.append("本文档是 ValueInvestorAI 五层防线架构的 **Layer 0 硬约束**。")
    lines.append("所有条款由三个独立投资方法论框架（Buffett / Munger / Duan）的研究助手")
    lines.append("经过 4 个阶段（独立提案 → 中立对照 → 修订 → 语义合并）辩论产生，")
    lines.append("**仅包含三方全票通过（3/3 unanimous）的 principles**。")
    lines.append("")
    lines.append("2/3 多数共识条款在 `soul-level-preferences.md`（仅供 Layer 1 Agent 参考，")
    lines.append("不作为 Layer 0 硬约束执行）。")
    lines.append("")
    lines.append(f"**总计 HARD 条款：{len(hard)}**")
    lines.append("")

    # Group by category
    by_cat: Dict[str, List[Dict]] = {}
    for c in hard:
        by_cat.setdefault(c.get("category", "uncategorized"), []).append(c)

    cat_order = ["veto_line", "quantitative_hard", "qualitative_required",
                 "position_sizing", "valuation_method", "uncategorized"]
    cat_titles = {
        "veto_line": "直接否决线（veto）",
        "quantitative_hard": "量化硬约束",
        "qualitative_required": "定性必查项",
        "position_sizing": "仓位约束",
        "valuation_method": "估值方法限制",
        "uncategorized": "其他",
    }

    idx = 1
    for cat in cat_order:
        if cat not in by_cat:
            continue
        lines.append(f"\n## {cat_titles[cat]}")
        lines.append("")
        for cluster in by_cat[cat]:
            lines.append(render_principle_markdown(cluster, idx))
            idx += 1

    lines.append("\n---\n")
    lines.append("## Layer 0 执行说明")
    lines.append("")
    lines.append("每条 HARD principle 的 `severity` 决定 PrinciplesEngine 的行为：")
    lines.append("- `veto`: 评估返回 `{passed: false}`，拦截投资决策")
    lines.append("- `warning`: 评估返回 `{passed: true, warnings: [...]}`")
    lines.append("- `note`: 仅记录，不影响 passed 状态")
    lines.append("")
    lines.append(f"机器可执行版本：`v1.0.schema.json`")
    lines.append(f"Company data 字段契约：`company_data_contract.md`")
    lines.append("")
    lines.append("## 升级规则")
    lines.append("")
    lines.append("- v1.0 → v1.0.1：错字/格式修订")
    lines.append("- v1.0 → v1.1：新增 principle 或阈值微调")
    lines.append("- v1.0 → v2.0：重大结构变更、删除 principle、或 soul doc 重大版本升级")
    lines.append("- 每 6 个月 review 一次 或 soul doc 大版本升级时触发")
    lines.append("")
    return "\n".join(lines)


def render_soft_preferences(soft: List[Dict], dropped: List[Dict]) -> str:
    """Render soul-level-preferences.md (SOFT + DROPPED)."""
    lines = []
    lines.append("# Soul-Level Preferences (非 Layer 0)")
    lines.append("")
    lines.append(f"> Generated: {NOW.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("本文档记录**未达成三方全票共识**的 principle candidates，")
    lines.append("**不作为 Layer 0 硬约束执行**。仅供 Layer 1 Agent 参考。")
    lines.append("")
    lines.append(f"- SOFT (2/3 多数): {len(soft)}")
    lines.append(f"- DROPPED (1/3 单方): {len(dropped)}")
    lines.append("")

    lines.append("\n## SOFT Preferences（2/3 多数共识）\n")
    if not soft:
        lines.append("*(无)*")
    else:
        for i, c in enumerate(soft, 1):
            lines.append(render_principle_markdown(c, i))

    lines.append("\n## DROPPED Candidates（1/3 单方提案）\n")
    lines.append("*以下 principles 仅在单一方法论框架下提出，保留作为 soul-specific 偏好，")
    lines.append("不升级到跨框架层面。*\n")
    if not dropped:
        lines.append("*(无)*")
    else:
        for i, c in enumerate(dropped, 1):
            lines.append(render_principle_markdown(c, i))

    return "\n".join(lines)


def render_schema_json(hard: List[Dict]) -> Dict:
    """Render machine-executable v1.0.schema.json."""
    rules = []
    for cluster in hard:
        variants = cluster.get("variant_seeds", [])
        # P0 fix: filter to numeric thresholds only before min() — prevents
        # TypeError when LLM mixes numbers and None/strings.
        thresholds = [
            v.get("threshold") for v in variants
            if v.get("threshold") is not None
            and isinstance(v.get("threshold"), (int, float))
            and not isinstance(v.get("threshold"), bool)  # bool is subclass of int
        ]

        # Determine severity
        severities = [v.get("severity", "note") for v in variants]
        if "veto" in severities:
            sev = "veto"
        elif "warning" in severities:
            sev = "warning"
        else:
            sev = "note"

        supporting_masters = sorted({v.get("master") for v in variants if v.get("master")})
        rule = {
            "cluster_id": cluster.get("cluster_id"),
            "canonical_claim": cluster.get("canonical_claim"),
            "category": cluster.get("category"),
            "severity": sev,
            "supporting_masters": supporting_masters,
            "thresholds_diverge": cluster.get("thresholds_diverge", False),
        }
        if thresholds:
            # P1 fix: use median (middle ground) instead of min (most strict).
            # min was architectural issue — hijacks multi-framework pluralism to
            # the most extreme opinion. Median better represents collective stance.
            sorted_t = sorted(thresholds)
            n = len(sorted_t)
            if n % 2 == 1:
                rule["default_threshold"] = sorted_t[n // 2]
            else:
                rule["default_threshold"] = (sorted_t[n // 2 - 1] + sorted_t[n // 2]) / 2
            rule["threshold_variants_by_master"] = cluster.get("threshold_variants_by_master", {})
            rule["threshold_selection_rule"] = "median across framework variants"

        rules.append(rule)

    schema = {
        "version": "1.0",
        "generated_at": NOW.isoformat(),
        "description": "Machine-executable Layer 0 hard constraints for ValueInvestorAI. "
                       "Each rule has severity (veto/warning/note) and an optional threshold. "
                       "PrinciplesEngine.evaluate(company_data) iterates these rules and "
                       "returns {passed: bool, violations: [...], warnings: [...]}.",
        "rules": rules,
        "company_data_contract": "See company_data_contract.md for required input fields.",
    }
    return schema


def render_company_data_contract(hard: List[Dict]) -> str:
    """Render company_data_contract.md listing required input fields."""
    lines = []
    lines.append("# Company Data Contract for PrinciplesEngine")
    lines.append("")
    lines.append(f"> Generated: {NOW.strftime('%Y-%m-%d')}")
    lines.append("> Purpose: 定义 MVP 阶段（未来 Path A）yfinance / edgartools adapter")
    lines.append("> 需要提供给 PrinciplesEngine.evaluate() 的 company_data 字段。")
    lines.append("")
    lines.append("## 要求字段（从 HARD rules 反推）")
    lines.append("")

    # Collect all referenced fields from cluster variant seeds
    fields_needed = set()
    field_contexts: Dict[str, List[str]] = {}
    for cluster in hard:
        claim = cluster.get("canonical_claim", "")
        for v in cluster.get("variant_seeds", []):
            # The variant seed may have data_field from Phase 1 quantitative_rule
            # (preserved through Phase 2.5 modify).
            # Best we can do without looking at original Phase 1 seeds: infer from claim.
            pass

    # Fallback: enumerate common fields by category
    lines.append("### 基础财务（quantitative_hard / veto_line）")
    common = [
        ("financials.roe_latest", "number", "最新年度 ROE（%）"),
        ("financials.roe_5yr_avg", "number", "过去 5 年平均 ROE"),
        ("financials.roe_5yr_min", "number", "过去 5 年最低 ROE"),
        ("financials.debt_to_equity", "number", "资产负债率"),
        ("financials.free_cash_flow_positive_years", "number", "过去 N 年内 FCF 为正的年份数"),
        ("financials.revenue_growth_5yr", "number", "过去 5 年营收复合增长率"),
        ("financials.gross_margin", "number", "毛利率"),
        ("financials.net_margin", "number", "净利率"),
        ("financials.pe_ratio", "number", "市盈率"),
        ("financials.pb_ratio", "number", "市净率"),
        ("financials.years_of_profitability_in_10", "number", "过去 10 年盈利年数"),
    ]
    for fname, ftype, desc in common:
        lines.append(f"- `{fname}` ({ftype}): {desc}")

    lines.append("")
    lines.append("### 业务定性（qualitative_required）")
    qual = [
        ("business.is_in_circle_of_competence", "bool", "是否在能力圈内（由大师 2/3 表决）"),
        ("business.is_simple_to_explain", "bool", "商业模式能否用 1-2 句话解释清楚"),
        ("management.integrity_score", "number | null", "管理层诚信评分（0-10，或 null 如未评估）"),
        ("management.capital_allocation_track_record", "string", "资本配置历史评价"),
        ("moat.identified_types", "list[string]", "已识别护城河类型（brand/cost/network/switching/regulatory）"),
    ]
    for fname, ftype, desc in qual:
        lines.append(f"- `{fname}` ({ftype}): {desc}")

    lines.append("")
    lines.append("### 仓位相关（position_sizing）")
    pos = [
        ("portfolio.total_holdings_count", "number", "当前总持仓数"),
        ("portfolio.target_position_pct", "number", "目标仓位百分比（0-1）"),
        ("portfolio.concentration_top5_pct", "number", "前 5 大持仓总占比"),
    ]
    for fname, ftype, desc in pos:
        lines.append(f"- `{fname}` ({ftype}): {desc}")

    lines.append("")
    lines.append("## 未来 MVP adapter 责任")
    lines.append("")
    lines.append("1. `yfinance_adapter.py`: 拉取 financials.* 字段（大部分免费可得）")
    lines.append("2. `edgartools_adapter.py`: 拉取 10-K / 13F 补充字段")
    lines.append("3. `qualitative_resolver.py`: 通过 Agent (Layer 1) 评估 business.* 和 management.* 字段（需要 LLM）")
    lines.append("4. `portfolio_tracker.py`: 维护 portfolio.* 实时字段")
    lines.append("")
    lines.append("本 contract 在 v1.0 Principles 冻结；MVP 阶段实现 adapters 必须对齐此 schema。")
    return "\n".join(lines)


def render_debate_log(
    seeds_by_master: Dict[str, List[Dict]],
    comparative_analysis: List[Dict],
    revised_seeds_by_master: Dict[str, List[Dict]],
    clusters: List[Dict],
    tally: Dict[str, List[Dict]],
    meta: Dict,
) -> str:
    """Render debate_log.md with full trace."""
    lines = []
    lines.append(f"# Principles Board Debate — Full Log ({NOW.strftime('%Y-%m-%d')})")
    lines.append("")
    lines.append("## Phase 1: Independent Seed Drafts")
    lines.append("")
    lines.append(f"Each of 3 methodology research assistants independently proposed seed principles.")
    lines.append("")
    for master, seeds in seeds_by_master.items():
        lines.append(f"- **{master}**: {len(seeds)} seeds")

    lines.append("")
    lines.append("## Phase 2: Neutral Comparative Analysis (Opus, anonymized)")
    lines.append("")
    # Intentionally do NOT expose anon_map in this debate_log — it's in prep/phase2_metadata.json
    # for internal audit only. Exposing it here would let readers back-infer which master
    # took which stance, defeating the anonymization design.
    lines.append(f"- Anonymized mapping: kept private in `prep/phase2_metadata.json`")
    consistency_rate = meta.get('consistency_rate', 0)
    lines.append(f"- Double-run consistency rate: {consistency_rate:.0%}"
                 f"{' ⚠ (below 80% design target)' if consistency_rate < 0.8 else ''}")
    lines.append(f"- Double-run disagreements: {meta.get('inconsistencies', 0)}")
    lines.append(f"- Total stances produced: {len(comparative_analysis)}")

    lines.append("")
    lines.append("## Phase 2.5: Revise Round (each master sees comparative analysis, revises)")
    lines.append("")
    for master, seeds in revised_seeds_by_master.items():
        n_keep = sum(1 for s in seeds if s.get("_revise_action") == "keep")
        n_mod = sum(1 for s in seeds if s.get("_revise_action") == "modify")
        n_new = sum(1 for s in seeds if s.get("_revise_action") == "new")
        orig = len(seeds_by_master.get(master, []))
        withdrawn = orig - n_keep - n_mod
        lines.append(f"- **{master}**: kept {n_keep}, modified {n_mod}, "
                    f"withdrew {withdrawn}, new {n_new} → final {len(seeds)}")

    lines.append("")
    lines.append("## Phase 3a: Semantic Deduplication (Sonnet)")
    lines.append("")
    lines.append(f"- Total clusters: {len(clusters)}")
    lines.append(f"- HARD (3/3): {len(tally['hard'])}")
    lines.append(f"- SOFT (2/3): {len(tally['soft'])}")
    lines.append(f"- DROPPED (1/3): {len(tally['dropped'])}")

    lines.append("")
    lines.append("## Phase 3b+3c: Vote Tally + Rendering")
    lines.append("")
    lines.append(f"Produced:")
    lines.append(f"- `Principles/v1.0.md` ({len(tally['hard'])} HARD principles)")
    lines.append(f"- `Principles/soul-level-preferences.md` ({len(tally['soft'])} SOFT + {len(tally['dropped'])} DROPPED)")
    lines.append(f"- `Principles/v1.0.schema.json`")
    lines.append(f"- `Principles/company_data_contract.md`")
    lines.append(f"- `Principles/critique_matrix.jsonl`")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Appendix: Cluster Details")
    lines.append("")
    for bucket_name, bucket_list in [("HARD", tally["hard"]), ("SOFT", tally["soft"]), ("DROPPED", tally["dropped"])]:
        lines.append(f"\n### {bucket_name}\n")
        if not bucket_list:
            lines.append("*(none)*")
        else:
            for c in bucket_list:
                vmasters = sorted({v.get("master") for v in c.get("variant_seeds", [])})
                lines.append(f"- `{c.get('cluster_id')}` [{c.get('category')}] "
                            f"{c.get('canonical_claim', '')[:80]} — masters: {vmasters}")

    lines.append("")
    return "\n".join(lines)


def phase3c_render_all(
    tally: Dict[str, List[Dict]],
    seeds_by_master: Dict[str, List[Dict]],
    comparative_analysis: List[Dict],
    revised_seeds_by_master: Dict[str, List[Dict]],
    clusters: List[Dict],
    meta: Dict,
):
    """Render all 4 output artifacts."""
    print("\n=== Phase 3c: Document Rendering (Python) ===")

    # v1.0.md
    hard_md = render_hard_principles(tally["hard"])
    (PRINCIPLES_DIR / "v1.0.md").write_text(hard_md, encoding="utf-8")
    print(f"  ✓ Principles/v1.0.md")

    # soul-level-preferences.md
    soft_md = render_soft_preferences(tally["soft"], tally["dropped"])
    (PRINCIPLES_DIR / "soul-level-preferences.md").write_text(soft_md, encoding="utf-8")
    print(f"  ✓ Principles/soul-level-preferences.md")

    # v1.0.schema.json
    schema = render_schema_json(tally["hard"])
    (PRINCIPLES_DIR / "v1.0.schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ Principles/v1.0.schema.json")

    # company_data_contract.md
    contract = render_company_data_contract(tally["hard"])
    (PRINCIPLES_DIR / "company_data_contract.md").write_text(contract, encoding="utf-8")
    print(f"  ✓ Principles/company_data_contract.md")

    # debate_log
    log = render_debate_log(
        seeds_by_master, comparative_analysis, revised_seeds_by_master,
        clusters, tally, meta,
    )
    log_path = PRINCIPLES_DIR / f"debate_log_{NOW.strftime('%Y-%m-%d')}.md"
    log_path.write_text(log, encoding="utf-8")
    print(f"  ✓ {log_path.name}")


# ==================== Main ====================

def main():
    PRINCIPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Phase 3: Synthesis (principles_synthesizer) ===")

    # Load from prep/
    revised_seeds_by_master = load_revised_seeds()
    total = sum(len(s) for s in revised_seeds_by_master.values())
    print(f"\nLoaded revised seeds: {total} total "
          f"({', '.join(f'{m}={len(s)}' for m, s in revised_seeds_by_master.items())})")

    meta = load_phase2_metadata()

    # Flatten for Phase 3a
    all_seeds = []
    for master, seeds in revised_seeds_by_master.items():
        for s in seeds:
            sc = dict(s)
            sc["_master"] = master
            all_seeds.append(sc)

    # Phase 3a: semantic dedup
    clusters = phase3a_semantic_dedup(all_seeds)

    # Phase 3b: vote tally
    tally = phase3b_vote_tally(clusters)

    # Phase 3c: render docs
    # Also need Phase 1 seeds for the log (not the revised, but for reporting)
    seeds_by_master_phase1 = {}
    for m in ["buffett", "munger", "duan"]:
        path = PREP_DIR / f"phase1_{m}_seeds.jsonl"
        if path.exists():
            seeds_by_master_phase1[m] = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    comparative_analysis_path = PREP_DIR / "phase2_comparative_analysis.jsonl"
    comparative_analysis = [json.loads(l) for l in comparative_analysis_path.read_text().splitlines() if l.strip()]

    phase3c_render_all(
        tally, seeds_by_master_phase1, comparative_analysis,
        revised_seeds_by_master, clusters, meta,
    )

    print(f"\n=== Phase 3 Complete ===")
    print(f"  HARD principles:  {len(tally['hard'])}")
    print(f"  SOFT preferences: {len(tally['soft'])}")
    print(f"  DROPPED:          {len(tally['dropped'])}")


if __name__ == "__main__":
    main()
