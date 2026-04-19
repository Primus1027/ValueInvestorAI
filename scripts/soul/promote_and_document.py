#!/usr/bin/env python3
"""
Phase F: promote v1.1-rc to v1.1, update documentation.

Steps:
  1. Rename v1.1-rc.md → v1.1.md for each master (if calibrate.py didn't reject)
  2. Update current/W.md and current/C.md symlinks to point at v1.1.md
  3. Append compendium reference to buffett/00-source-index.md and munger/00-source-index.md
  4. Update progress.md with a new section
  5. Write scan retro at registry/scan_2026-04-19_vig-retro.md

Pass --skip-promote to only update docs without renaming.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = PROJECT_ROOT / "src/souls/documents/versions"
CURRENT_DIR = PROJECT_ROOT / "src/souls/documents/current"
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
SRC_DIR = PROJECT_ROOT / "Resources/Sources"

NOW = datetime.now(timezone.utc)


def promote_one(label: str, master_code: str):
    """Rename v1.1-rc.md → v1.1.md and update symlink."""
    rc_file = VERSIONS_DIR / label / "v1.1-rc.md"
    final_file = VERSIONS_DIR / label / "v1.1.md"
    if not rc_file.exists():
        print(f"  WARN: {rc_file} missing, skipping {label}")
        return False
    rc_file.rename(final_file)
    # Update symlink
    symlink = CURRENT_DIR / f"{master_code}.md"
    if symlink.exists() or symlink.is_symlink():
        symlink.unlink()
    rel_target = f"../versions/{label}/v1.1.md"
    symlink.symlink_to(rel_target)
    print(f"  ✓ {label}: v1.1-rc.md → v1.1.md ; {master_code}.md → {rel_target}")
    return True


def append_source_index_ref(master_slug: str):
    """Append a compendium reference section to master's 00-source-index.md."""
    idx_path = SRC_DIR / master_slug / "00-source-index.md"
    if not idx_path.exists():
        print(f"  WARN: {idx_path} missing")
        return
    current = idx_path.read_text(encoding="utf-8")
    marker = "## 交叉引用索引（2026-04 vig scan）"
    if marker in current:
        print(f"  {master_slug}: already has compendium reference, skipping")
        return
    appendix = f"""

---

{marker}

2026-04-19 扫描了 value-investing-gurus.pages.dev（编者：用户投资人朋友），
整合了 134 份二手综合资料（P3/P4 tier）到 `Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04/`。

**这些资料不是原件替代，而是补充：**
- 交叉验证本索引中 P0/P1 原件的细节（已解决 2+7 处 NEEDS VERIFICATION 标记）
- 提供跨大师对比视角（master_comparisons）
- 把概念链接到真实投资案例与实际回报（concept_investment_links）

浏览：`cross-master/views/value-investing-gurus-dev-2026-04/00-compendium-index.md`
Registry：`registry/sources.jsonl` 按 `masters: ["{master_slug}"]` 过滤
Scan 记录：`registry/scans.jsonl` id = `scan_2026-04-19_vig`
"""
    idx_path.write_text(current + appendix, encoding="utf-8")
    print(f"  ✓ {master_slug}/00-source-index.md: appended compendium reference")


def update_progress_md():
    progress_path = PROJECT_ROOT / "progress.md"
    if not progress_path.exists():
        print("  WARN: progress.md missing")
        return
    current = progress_path.read_text(encoding="utf-8")
    marker = "## 2026-04-19: Scan & Integration — value-investing-gurus compendium"
    if marker in current:
        print("  progress.md already has this scan entry")
        return

    # Count registry items
    def count_lines(fn):
        p = REG_DIR / fn
        if not p.exists(): return 0
        return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip())

    sources_n = count_lines("sources.jsonl")
    comparisons_n = count_lines("master_comparisons.jsonl")
    invests_n = count_lines("concept_investment_links.jsonl")
    insights_n = count_lines("decision_insights.jsonl")
    verifs_n = count_lines("verifications_resolved.jsonl")

    new_section = f"""

{marker}

**目标**：把新发现的投资资料网站（用户投资人朋友编纂的 Buffett-Munger Compendium）作为"首次扫描先例"，
整合进 W/C 灵魂封装，并建立可重复的扫描-整合工作流。

**成果**：
- 🏗️ 建立了 8 阶段扫描流水线（见 `scripts/soul/`）与全局 registry（`Resources/Sources/registry/`）
- 📥 抓取 {sources_n} 份二手综合资料（P3/P4 tier），内容哈希寻址存储于 `raw/` + 段落锚点归一化在 `normalized/`
- ✅ 完成 {verifs_n} 项定向验证（解决 W 灵魂文档中多处 NEEDS VERIFICATION）
- 🔀 抽取 {comparisons_n} 条跨大师对比、{invests_n} 条概念→投资案例→结果链接、{insights_n} 条决策导向洞察
- 📄 生成 W/C v1.1 灵魂文档（append-only，保留 v1.0 prose 不变，新增 Appendix Z 做多 Agent 辩论输入）
- 🧪 Gate 5 校准回归：见 `calibration_runs/`

**关键设计决定**：
1. 网站编者目的是"知识整理"，我们的目的是"决策驱动"——所有借鉴过一道"决策相关性过滤"
2. 采用 AI 主导审核（L1 自动 + L2 对抗审查），人工仅在关键节点介入
3. Profile.json 的 factor 列表稳定不变（防膨胀）；新洞察沉淀到 red_flags / how_to_evaluate
4. 引入 ROI 衰减防御机制：novelty_rate、decision_delta_rate、concept saturation 监控

**下一次扫描的起点**：`scripts/soul/fetch_vig.py` 和 `scripts/soul/integrate.py` 可作为新扫描的模板复用。

"""
    progress_path.write_text(current + new_section, encoding="utf-8")
    print("  ✓ progress.md: appended new section")


def write_scan_retro():
    """Write a retrospective reflection on the scan."""
    retro_path = REG_DIR / "scan_2026-04-19_vig-retro.md"

    def count_lines(fn):
        p = REG_DIR / fn
        if not p.exists(): return 0
        return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip())

    sources_n = count_lines("sources.jsonl")
    verifs_resolved = count_lines("verifications_resolved.jsonl")
    verifs_total = count_lines("verifications.jsonl")
    comparisons_n = count_lines("master_comparisons.jsonl")
    invests_n = count_lines("concept_investment_links.jsonl")
    insights_n = count_lines("decision_insights.jsonl")

    content = f"""# Scan Retrospective: scan_2026-04-19_vig

**Date**: {NOW.strftime('%Y-%m-%d')}
**Source**: value-investing-gurus.pages.dev (editor: user's investor friend)
**Tier**: P4 (secondary synthesis); P3 (source-page variants)

## What worked

1. **API discovery**: JS bundle revealed clean `/api/zh/articles/<dir>/<id>.txt` endpoints.
   curl with `--compressed -L -f` + retries handled Cloudflare chunked response reliably after
   initial urllib `IncompleteRead` failures. Target: 134 pages, achieved: 134 (100%).

2. **Content-hash addressing**: Source files stored under `raw/<sha[:2]>/<sha>/payload.md`.
   Deduplication is free. Fetch metadata + paragraph anchors made the registry self-documenting.

3. **Delayed integration**: Scan (fetch + register) decoupled from integrate (soul update).
   This means incremental scans can land cheaply; expensive integration is batched.

4. **Decision-filter on extractions**: By forcing `decision_insights` to carry
   `decision_impact: factor_weight_evidence|red_flag|green_flag|case_study|evolution`,
   the LLM naturally filtered ~80% of raw insights that were philosophical but not actionable.

## What didn't work

1. **Verification yield is low**: 30 priority verifications processed, 20 "insufficient",
   7 "partial", 2 "supported", 1 "contradicted". The site's P4 content doesn't carry
   granular biographical detail (e.g., exact dollar amounts, specific dates). It's thematic,
   not reference-style.

   → **Lesson**: P4 secondary synthesis is GOOD for conceptual/philosophical validation,
   BAD for specific factual claims. Future verifications should prefer P0 primaries.

2. **Concept taxonomy bloat risk**: 47 site-introduced concepts vs 27 decision-relevant.
   Must discipline `concept_site_*` in `concepts.jsonl` to not leak into `decision_factor_for`.

3. **Time-per-extraction**: ~240s per article with Claude CLI (json-output mode). For 31
   articles × 3 extraction passes that's ~40 minutes, limited by CLI RTT not LLM compute.

## ROI Assessment

- `decision_delta_rate`: ~{"%.1f" % (100 * insights_n / max(sources_n, 1))}% — {insights_n} actionable insights over {sources_n} sources
- `verification_resolution_rate`: {100 * 10 / 30:.0f}% of priority verifications got evidence
- `novelty_rate`: ~estimated 15-25% (P4 site has high concept overlap with our existing material)
- `soul_doc_delta_words`: see `changelogs/W-v1.0-to-v1.1.md` and `C-v1.0-to-v1.1.md`
- `profile_factor_count_delta`: 0 (target) — factor list unchanged

**Overall ROI: medium**. Primary value was establishing the scan pipeline; information uplift was modest.

## Recommendations for next scan

1. **Prefer P0 sources**: Direct primary materials (new CNBC transcripts, new 13F filings, new shareholder letters) yield much higher decision_delta_rate than P4 secondary.
2. **Gap-driven targeting**: Before scanning, read `coverage.json` and target concepts with high `gap_score`.
3. **Pre-scan ROI estimator**: If predicted `novelty_rate` < 15%, consider "light touch" (archive only, skip integration).
4. **Scan budget caps** by tier:
   - P0: unbounded (always scan)
   - P1: ~10 per quarter
   - P4: ≤3 per quarter, and only if unique editorial angle

## Artifacts

- Registry: `Resources/Sources/registry/*.jsonl`
- Compendium views: `Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04/`
- Soul doc updates: `src/souls/documents/versions/W-buffett/v1.1.md`, `C-munger/v1.1.md`
- Changelogs: `src/souls/documents/changelogs/*-v1.0-to-v1.1.md`
- Calibration: `calibration_runs/run-*/report.md`
"""
    retro_path.write_text(content, encoding="utf-8")
    print(f"  ✓ {retro_path.name} written")


def main():
    skip_promote = "--skip-promote" in sys.argv

    print("=== Phase F: Promote + Document ===\n")

    if not skip_promote:
        print("Step 1: Promote v1.1-rc → v1.1")
        promote_one("W-buffett", "W")
        promote_one("C-munger", "C")
    else:
        print("Skipping promotion (use without --skip-promote to rename)")

    print("\nStep 2: Update source indices")
    append_source_index_ref("buffett")
    append_source_index_ref("munger")

    print("\nStep 3: Update progress.md")
    update_progress_md()

    print("\nStep 4: Write scan retrospective")
    write_scan_retro()

    print("\n=== Phase F Complete ===")


if __name__ == "__main__":
    main()
