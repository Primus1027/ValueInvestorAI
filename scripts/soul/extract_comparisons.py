#!/usr/bin/env python3
"""
Extract master_comparisons and concept_investment_links from synthesis + concept pages.

Strategy:
  - For each synthesis page: LLM extracts (a) Buffett/Munger positions on key topics,
    (b) consensus points, (c) divergence points, (d) investment cases mentioned with outcomes.
  - For concept pages with clear Buffett/Munger angles: similar extraction.

Output:
  Resources/Sources/registry/master_comparisons.jsonl
  Resources/Sources/registry/concept_investment_links.jsonl
"""

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
VIEW_DIR = PROJECT_ROOT / "Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04"
NOW = datetime.now(timezone.utc).isoformat()


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end+5:]
    return text


def get_article_meta(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm = text[4:end]
    meta = {}
    for line in fm.split("\n"):
        if ":" not in line: continue
        k, v = line.split(":", 1)
        k = k.strip(); v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            meta[k] = [x.strip().strip('"\'') for x in inner.split(",")] if inner else []
        else:
            meta[k] = v.strip('"\'')
    return meta


def claude_extract(article_path: Path, article_id: str, article_type: str) -> dict:
    """Use Claude CLI to extract comparisons and investment links."""
    body = strip_frontmatter(article_path.read_text(encoding="utf-8"))
    body = body[:15000]  # cap

    prompt = f"""任务：从以下关于巴菲特+芒格投资哲学的文章中，抽取决策相关的结构化信息。

文章 ID: {article_id}
文章类型: {article_type}

文章内容：
---
{body}
---

请输出一个 JSON 对象，包含以下字段（如果某些信息文章未涉及，对应数组保持为空 []）：

{{
  "master_comparisons": [
    {{
      "topic": "<议题名称，中文，如'护城河理解' '估值方法' '资本配置'>",
      "consensus": ["<双方共识点 1>", "<共识点 2>"],
      "differences": [
        {{"dimension": "<比较维度>", "buffett": "<巴菲特立场>", "munger": "<芒格立场>"}}
      ],
      "synthesis_statement": "<1-2 句总结两人如何构成完整体系>"
    }}
  ],
  "concept_investment_links": [
    {{
      "concept": "<概念名，中文>",
      "investment_case": "<具体投资标的名称，如'喜诗糖果'>",
      "year": <整数年份或 null>,
      "master": "buffett|munger|both",
      "outcome_description": "<简短描述投资结果或其启示性，含数字如可得>",
      "supporting_quote": "<原文引用，最多150字>"
    }}
  ],
  "decision_insights": [
    {{
      "claim": "<决策相关的具体主张，不是空泛哲学>",
      "master": "buffett|munger",
      "concept_tag": "<对应决策概念，如'pricing_power' '能力圈' '安全边际'>",
      "supporting_quote": "<原文引用，最多150字>",
      "decision_impact": "factor_weight_evidence|red_flag|green_flag|case_study|evolution"
    }}
  ]
}}

严格要求：
1. 只输出 JSON，不要其他文字。
2. 所有引用必须来自文章原文，不要编造。
3. master_comparisons 只有文章明确讨论两人比较时才抽取；不要凭空构造。
4. concept_investment_links 要有具体案例名+年份+结果，不要泛泛的"伯克希尔投资"。
5. decision_insights 过滤掉仅有哲学意义的观点，只保留能直接映射到决策 factor 的。如果某主张只是"重要"但不能落地到 red_flag/green_flag/evaluation，跳过。"""

    from _json_utils import parse_claude_cli_result

    # For this extractor, regex fallback is NOT appropriate (array-of-objects can't be salvaged)
    # — we prefer to let it fail and retry manually.
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=240, text=True, check=True)
        parsed = parse_claude_cli_result(result.stdout, expected_keys=None)
        if parsed is None:
            return {
                "error": "JSON parse failed after all fallback strategies",
                "_source_article_id": article_id,
                "stdout_head": result.stdout[:300],
            }
        parsed["_source_article_id"] = article_id
        parsed["_article_path"] = str(article_path.relative_to(PROJECT_ROOT))
        return parsed
    except subprocess.CalledProcessError as e:
        return {
            "error": f"subprocess failed: {e}",
            "_source_article_id": article_id,
            "stderr": (e.stderr or "")[:300],
        }
    except Exception as e:
        return {"error": str(e), "_source_article_id": article_id}


def main():
    # Select high-signal articles: synthesis pages + top concept pages
    synthesis_files = list((VIEW_DIR / "synthesis").rglob("*.zh.md"))

    # Top concept pages: those most relevant to decisions
    priority_concepts = [
        "competitive_moat", "pricing_power", "circle_of_competence",
        "margin_of_safety", "capital_allocation", "business_quality",
        "management_integrity", "owner_earnings", "valuation",
        "compounding", "inversion", "lollapalooza_effect",
        "mental_models", "cognitive_biases", "temperament_and_discipline",
        "concentrated_investing", "long_term_thinking", "accounting_quality",
        "simplicity"
    ]
    concept_files = []
    for c in priority_concepts:
        p = VIEW_DIR / "concept" / f"{c}.zh.md"
        if p.exists():
            concept_files.append(p)

    all_files = synthesis_files + concept_files
    print(f"Processing {len(synthesis_files)} synthesis + {len(concept_files)} concept = {len(all_files)} articles")

    # Extract in parallel
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {}
        for f in all_files:
            meta = get_article_meta(f.read_text(encoding="utf-8"))
            article_id = meta.get("article_id", f.stem)
            article_type = meta.get("article_type", "concept")
            futures[ex.submit(claude_extract, f, article_id, article_type)] = (f, article_id)
        done = 0
        for fut in as_completed(futures):
            f, article_id = futures[fut]
            r = fut.result()
            done += 1
            if "error" in r:
                print(f"  [{done}/{len(all_files)}] {article_id}: ERROR {r['error'][:80]}")
            else:
                mc = len(r.get("master_comparisons", []))
                cil = len(r.get("concept_investment_links", []))
                di = len(r.get("decision_insights", []))
                print(f"  [{done}/{len(all_files)}] {article_id}: {mc} comparisons, {cil} invest_links, {di} insights")
            results.append(r)

    # Flatten and write to registries
    all_comparisons = []
    all_invest_links = []
    all_insights = []

    for r in results:
        if "error" in r:
            continue
        sid = r["_source_article_id"]
        spath = r["_article_path"]
        for i, mc in enumerate(r.get("master_comparisons", [])):
            mc["comparison_id"] = f"cmp_{sid}_{i+1:02d}"
            mc["masters_compared"] = ["buffett", "munger"]
            mc["source_article_id"] = sid
            mc["source_article_path"] = spath
            mc["extracted_at"] = NOW
            mc["extracted_by"] = "extract_comparisons.py+claude-sonnet-4-6"
            all_comparisons.append(mc)
        for i, cil in enumerate(r.get("concept_investment_links", [])):
            cil["link_id"] = f"cil_{sid}_{i+1:02d}"
            cil["source_article_id"] = sid
            cil["source_article_path"] = spath
            cil["extracted_at"] = NOW
            all_invest_links.append(cil)
        for i, di in enumerate(r.get("decision_insights", [])):
            di["insight_id"] = f"di_{sid}_{i+1:02d}"
            di["source_article_id"] = sid
            di["source_article_path"] = spath
            di["extracted_at"] = NOW
            all_insights.append(di)

    with (REG_DIR / "master_comparisons.jsonl").open("w", encoding="utf-8") as f:
        for mc in all_comparisons:
            f.write(json.dumps(mc, ensure_ascii=False) + "\n")
    with (REG_DIR / "concept_investment_links.jsonl").open("w", encoding="utf-8") as f:
        for cil in all_invest_links:
            f.write(json.dumps(cil, ensure_ascii=False) + "\n")
    with (REG_DIR / "decision_insights.jsonl").open("w", encoding="utf-8") as f:
        for di in all_insights:
            f.write(json.dumps(di, ensure_ascii=False) + "\n")

    print(f"\n=== Summary ===")
    print(f"master_comparisons: {len(all_comparisons)}")
    print(f"concept_investment_links: {len(all_invest_links)}")
    print(f"decision_insights: {len(all_insights)}")
    print(f"\nRegistries written to {REG_DIR}")


if __name__ == "__main__":
    main()
