#!/usr/bin/env python3
"""
For each high-priority verification, search the vig corpus for relevant articles
via keyword matching, then call Claude CLI to evaluate whether the article
supports, contradicts, or is silent on the claim.

Output: verifications_resolved.jsonl with resolution per verification.
"""

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
VIEW_DIR = PROJECT_ROOT / "Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04"


def load_verifications_priority() -> list[dict]:
    """Load priorities: 9 NEEDS VERIFICATION markers + HIGH-confidence GPT findings."""
    items = []
    with (REG_DIR / "verifications.jsonl").open() as f:
        for line in f:
            v = json.loads(line)
            # Priority 1: explicit NEEDS VERIFICATION markers
            if not v.get("source"):
                v["_priority"] = 1
                items.append(v)
            # Priority 2: HIGH confidence GPT findings
            elif v["gpt_review_finding"] and v["gpt_review_finding"].get("confidence") == "HIGH":
                v["_priority"] = 2
                items.append(v)
    return sorted(items, key=lambda x: (x["_priority"], x["master_id"]))


def extract_keywords(v: dict) -> list[str]:
    """Extract searchable keywords from a verification record."""
    kws = set()
    texts = []
    if v.get("full_line"): texts.append(v["full_line"])
    if v.get("context_block"): texts.append(v["context_block"])
    if v.get("gpt_review_finding") and v["gpt_review_finding"].get("text"):
        texts.append(v["gpt_review_finding"]["text"])
    full_text = " ".join(texts)

    # Company / entity names
    for m in re.finditer(r"\b(Apple|Coca-Cola|See's|See's Candies|Berkshire|BNSF|Dexter|GEICO|Salomon|Washington Post|Graham|Munger|Buffett|Goldman|Bank of America|BYD|Wesco|Daily Journal|Wheeler|Partnership|LTCM|Costco|Solomon)\b", full_text, re.I):
        kws.add(m.group(1).lower())

    # Chinese company names (for zh articles)
    for m in re.finditer(r"(苹果|可口可乐|喜诗|伯克希尔|GEICO|所罗门|华盛顿|格雷厄姆|芒格|巴菲特|盖可|比亚迪|高盛|美银|Costco|好市多|迪奇特)", full_text):
        kws.add(m.group(1))

    # Dollar amounts
    for m in re.finditer(r"\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)?", full_text, re.I):
        kws.add(m.group(0))

    # Years
    for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", full_text):
        kws.add(m.group(0))

    # Percentages
    for m in re.finditer(r"\b\d+(?:\.\d+)?%", full_text):
        kws.add(m.group(0))

    return list(kws)


def find_candidate_articles(keywords: list[str], master_id: str) -> list[Path]:
    """Find zh articles whose body contains multiple keywords."""
    if not keywords:
        return []
    candidates = []
    for md_file in VIEW_DIR.rglob("*.zh.md"):
        text = md_file.read_text(encoding="utf-8")
        # Check master mention
        if master_id == "buffett" and "buffett" not in text.lower() and "巴菲特" not in text and "伯克希尔" not in text:
            continue
        if master_id == "munger" and "munger" not in text.lower() and "芒格" not in text:
            continue
        # Count keyword hits
        hits = 0
        for kw in keywords:
            if kw.lower() in text.lower():
                hits += 1
        if hits >= max(1, len(keywords) // 3):  # at least 1/3 of kws match
            candidates.append((hits, md_file))
    # Return top 5 by hit count
    candidates.sort(reverse=True, key=lambda x: x[0])
    return [c[1] for c in candidates[:5]]


def claude_evaluate(verification: dict, article_path: Path) -> dict:
    """Use Claude CLI to evaluate an article's evidence for a verification."""
    claim_text = (verification.get("gpt_review_finding", {}) or {}).get("text", "") or \
                 verification.get("full_line", "") or \
                 verification.get("context_block", "")[:300]
    if not claim_text:
        return {"error": "no claim text"}

    article_text = article_path.read_text(encoding="utf-8")
    # Strip frontmatter for prompt efficiency
    if article_text.startswith("---\n"):
        end = article_text.find("\n---\n", 4)
        if end != -1:
            article_text = article_text[end+5:]

    # Cap article to 10KB for prompt
    article_text = article_text[:10000]

    prompt = f"""你是一个事实核查助手。任务：给定一条"待验证主张"和一篇"候选证据文章"，判断文章是否支持、反驳或不相关。

待验证主张（来自 {verification['master_id']} 灵魂文档第 {verification.get('line_number', '?')} 行）：
"{claim_text}"

候选证据文章（节选）：
---
{article_text}
---

请以 JSON 格式回复（只输出 JSON，不要其他内容）：
{{
  "relevance": "supports|contradicts|partial|irrelevant",
  "confidence": "high|medium|low",
  "evidence_quote": "<原文关键引用，最多200字，如果 irrelevant 则空字符串>",
  "evidence_paragraph_anchor": "<如果能找到文章里的 <!-- p:XXXXXX --> 锚点，填在这里；否则空>",
  "explanation": "<简短说明，50字以内>"
}}"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=120, text=True, check=True)
        # Claude CLI --output-format json wraps in {"type": "result", "result": "..."}
        outer = json.loads(result.stdout)
        inner_text = outer.get("result", "")
        # Strip markdown code fences if present
        inner_text = re.sub(r"^```json\s*", "", inner_text.strip())
        inner_text = re.sub(r"\s*```$", "", inner_text)
        return json.loads(inner_text)
    except Exception as e:
        return {"error": f"cli_fail: {e}", "stdout_head": result.stdout[:200] if 'result' in locals() else ""}


def process_verification(v: dict) -> dict:
    keywords = extract_keywords(v)
    candidates = find_candidate_articles(keywords, v["master_id"])
    evidence_records = []
    for cpath in candidates[:3]:  # top 3 candidates per verification
        r = claude_evaluate(v, cpath)
        evidence_records.append({
            "article_path": str(cpath.relative_to(PROJECT_ROOT)),
            "evaluation": r,
        })

    # Aggregate: is there any supports/contradicts?
    best_status = "insufficient"
    best_evidence = None
    for er in evidence_records:
        rel = er["evaluation"].get("relevance", "")
        conf = er["evaluation"].get("confidence", "")
        if rel == "supports" and conf in ("high", "medium"):
            best_status = "supported"
            best_evidence = er
            break
        elif rel == "contradicts" and conf in ("high", "medium"):
            best_status = "contradicted"
            best_evidence = er
            break
        elif rel == "partial":
            if best_status not in ("supported", "contradicted"):
                best_status = "partial"
                best_evidence = er

    return {
        "verification_id": v["verification_id"],
        "master_id": v["master_id"],
        "keywords_searched": keywords,
        "candidates_count": len(candidates),
        "evidence_records": evidence_records,
        "best_status": best_status,
        "best_evidence": best_evidence,
        "source_verification": {
            "line_number": v.get("line_number"),
            "section": v.get("section"),
            "claim_text": (v.get("gpt_review_finding", {}) or {}).get("text", "") or v.get("full_line", ""),
        }
    }


def main():
    verifications = load_verifications_priority()
    print(f"Loaded {len(verifications)} priority verifications")
    print(f"  P1 markers: {len([v for v in verifications if v['_priority'] == 1])}")
    print(f"  P2 HIGH-conf GPT findings: {len([v for v in verifications if v['_priority'] == 2])}")

    # Cap to top priorities for first pass; can rerun for more
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    verifications = verifications[:top_n]
    print(f"Processing top {top_n}")

    resolutions = []
    with ThreadPoolExecutor(max_workers=3) as ex:  # CLI calls are slow; modest parallelism
        futures = [ex.submit(process_verification, v) for v in verifications]
        done = 0
        for f in as_completed(futures):
            r = f.result()
            resolutions.append(r)
            done += 1
            status = r["best_status"]
            vid = r["verification_id"]
            print(f"  [{done}/{len(verifications)}] {vid}: {status} (candidates={r['candidates_count']})")

    # Append to registry
    fp = REG_DIR / "verifications_resolved.jsonl"
    with fp.open("w", encoding="utf-8") as f:
        for r in resolutions:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    from collections import Counter
    stat_counter = Counter(r["best_status"] for r in resolutions)
    print(f"\n=== Summary ===")
    for status, n in stat_counter.most_common():
        print(f"  {status}: {n}")
    print(f"\nWritten: {fp}")


if __name__ == "__main__":
    main()
