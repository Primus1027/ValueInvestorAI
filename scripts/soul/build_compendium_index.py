#!/usr/bin/env python3
"""Build 00-compendium-index.md summarizing the vig scan."""

import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
VIEW_DIR = PROJECT_ROOT / "Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04"


def load_jsonl(p):
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    sources = load_jsonl(REG_DIR / "sources.jsonl")
    master_links = load_jsonl(REG_DIR / "source_masters.jsonl")
    concepts = load_jsonl(REG_DIR / "concepts.jsonl")
    verifs_resolved = load_jsonl(REG_DIR / "verifications_resolved.jsonl")
    comparisons = load_jsonl(REG_DIR / "master_comparisons.jsonl")
    invest_links = load_jsonl(REG_DIR / "concept_investment_links.jsonl")
    insights = load_jsonl(REG_DIR / "decision_insights.jsonl")

    # Group sources by article_type
    by_type = defaultdict(list)
    for s in sources:
        t = s["metadata"]["article_type"]
        by_type[t].append(s)

    # Build index
    idx = []
    idx.append("# Value-Investing-Gurus Compendium — Scan 2026-04-19\n")
    idx.append("\n> 编者：用户的投资人朋友（网站方法论文章：《我用AI整理了巴菲特和芒格69年的思想遗产》）")
    idx.append("> **编辑目的**：知识整理与分享")
    idx.append("> **我们的使用目的**：决策驱动（知识是中间过程，不是终点）")
    idx.append("> **Tier**：本次所有资料默认 P4（二手综合），P3（对原件的提炼）\n")

    idx.append("\n## 抓取统计\n")
    idx.append(f"- 总资料：{len(sources)} 份（{sum(1 for s in sources if s['metadata']['language']=='zh')} zh + {sum(1 for s in sources if s['metadata']['language']=='en')} en）")
    for t, items in sorted(by_type.items()):
        zh_count = sum(1 for s in items if s['metadata']['language'] == 'zh')
        en_count = sum(1 for s in items if s['metadata']['language'] == 'en')
        idx.append(f"- **{t}**: {len(items)} 份（{zh_count} zh + {en_count} en）")
    idx.append(f"\n- 总字数（body）：~{sum(s['metadata']['word_count_approx'] for s in sources):,} 字符")

    idx.append("\n## 抽取产物（本次 scan 新增）\n")
    idx.append(f"- `extractions.jsonl`（暂未运行全量抽取；后续按需）")
    idx.append(f"- `verifications.jsonl`: 103 项待验证（9 NEEDS VERIFICATION markers + 94 GPT review findings）")
    idx.append(f"- `verifications_resolved.jsonl`: {len(verifs_resolved)} 项已完成定向验证")
    resolved_stats = Counter(v["best_status"] for v in verifs_resolved)
    for s, n in resolved_stats.most_common():
        idx.append(f"  - {s}: {n}")
    idx.append(f"- `master_comparisons.jsonl`: {len(comparisons)} 条跨大师对比（Buffett vs Munger）")
    idx.append(f"- `concept_investment_links.jsonl`: {len(invest_links)} 条 概念→投资案例→结果")
    idx.append(f"- `decision_insights.jsonl`: {len(insights)} 条决策导向洞察（可流入 profile.json factor 的 red/green flags）")

    idx.append(f"\n## Concept Taxonomy（bootstrap 结果）\n")
    decision_concepts = [c for c in concepts if c["decision_factor_for"]]
    site_concepts = [c for c in concepts if c["source_lineage"] == "value-investing-gurus.pages.dev"]
    idx.append(f"- 总概念：{len(concepts)}")
    idx.append(f"  - 决策相关（来自 profile factors）：{len(decision_concepts)}")
    idx.append(f"  - 网站增补（supplementary）：{len(site_concepts)}")

    idx.append("\n## 文件浏览\n")
    idx.append("按文章类型分目录展开：\n")
    for t in sorted(by_type.keys()):
        items = [s for s in by_type[t] if s['metadata']['language'] == 'zh']
        items.sort(key=lambda s: s['metadata']['article_id'])
        idx.append(f"\n### {t} ({len(items)})\n")
        for s in items:
            aid = s['metadata']['article_id']
            title = s['metadata'].get('title', '').strip() or aid
            words = s['metadata']['word_count_approx']
            tier = s['classification']['tier']
            masters = s['classification']['masters']
            path_rel = s.get('view_path', '') or f"normalized/{s['content_sha256'][:2]}/{s['content_sha256']}.md"
            idx.append(f"- [{aid}]({path_rel}) — {title} ({words}字, {tier}, {','.join(masters)})")

    idx.append("\n## Registry 文件\n")
    for fn in ["sources.jsonl", "source_masters.jsonl", "concepts.jsonl",
               "concept_aliases.jsonl", "verifications.jsonl", "verifications_resolved.jsonl",
               "master_comparisons.jsonl", "concept_investment_links.jsonl",
               "decision_insights.jsonl", "scans.jsonl"]:
        fp = REG_DIR / fn
        lines = len(load_jsonl(fp)) if fp.exists() else 0
        idx.append(f"- `{fn}`: {lines} records")

    idx.append("\n## 下一步\n")
    idx.append("1. 运行 `scripts/soul/integrate.py` 生成 W/C v1.1-rc.md")
    idx.append("2. 运行 `scripts/soul/calibrate.py` 做 Gate 5 校准回归")
    idx.append("3. 若通过，在 `versions/` 下 promote v1.1-rc → v1.1，并更新 `current/` symlink")

    out = VIEW_DIR / "00-compendium-index.md"
    out.write_text("\n".join(idx), encoding="utf-8")
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
