#!/usr/bin/env python3
"""
Fetch all articles from value-investing-gurus.pages.dev.

API structure:
  /api/<lang>/articles.json        -> index with id/type/path/size
  /api/<lang>/articles/<dir>/<id>.txt -> actual markdown content (YAML frontmatter + body)

Selective download policy:
  - zh all (120 articles) -- tier A
  - en entity + synthesis (14 articles) -- tier B
  - skip en sources, en concepts (we have primaries and zh is enough)

Writes:
  Resources/Sources/raw/<sha[:2]>/<sha>/payload.md  (immutable content)
  Resources/Sources/raw/<sha[:2]>/<sha>/fetch.json  (fetch metadata)
  Resources/Sources/normalized/<sha[:2]>/<sha>.md   (same content, for Phase B)
  Resources/Sources/registry/sources.jsonl         (append-only)
  Resources/Sources/registry/scans.jsonl           (this scan record)
  Resources/Sources/cross-master/views/.../<dir>/<id>.zh.md  (human-readable view)
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://value-investing-gurus.pages.dev"
UA = "Mozilla/5.0 (valueinvestor-ai-scanner/1.0)"

RAW_DIR = PROJECT_ROOT / "Resources/Sources/raw"
NORM_DIR = PROJECT_ROOT / "Resources/Sources/normalized"
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
VIEW_DIR = PROJECT_ROOT / "Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04"

SCAN_ID = "scan_2026-04-19_vig"
SCAN_STARTED = datetime.now(timezone.utc).isoformat()


def http_get(url: str, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed {url}: {last_err}")


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def parse_frontmatter(md: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown. Returns (meta, body)."""
    if not md.startswith("---\n"):
        return {}, md
    end = md.find("\n---\n", 4)
    if end == -1:
        return {}, md
    fm_raw = md[4:end]
    body = md[end + 5:]
    meta = {}
    for line in fm_raw.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        # Parse simple yaml lists [a, b, c]
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                meta[k] = []
            else:
                meta[k] = [x.strip().strip('"\'') for x in inner.split(",")]
        else:
            meta[k] = v.strip('"\'')
    return meta, body


def classify_article(article_type: str, masters_from_content: list[str]) -> dict:
    """Assign tier + kind based on article type."""
    if article_type == "concept":
        return {"kind": "secondary_synthesis", "tier": "P4",
                "tier_rationale": "Editorial concept page synthesizing multiple primary sources; decision relevance via primary_source_pointer"}
    if article_type == "synthesis":
        return {"kind": "secondary_synthesis", "tier": "P4",
                "tier_rationale": "Editor's cross-document thematic analysis; most decision-relevant when quotes trace back to P0"}
    if article_type == "source":
        # The site's view of a primary source (not the primary itself)
        return {"kind": "secondary_synthesis", "tier": "P3",
                "tier_rationale": "Site's distilled/summarized view of a known primary source; we may already own the P0"}
    if article_type == "entity":
        return {"kind": "tertiary", "tier": "P4",
                "tier_rationale": "Editor's profile write-up of a master"}
    return {"kind": "tertiary", "tier": "P4", "tier_rationale": "Unknown"}


def detect_masters(article_id: str, article_type: str, body: str, tags: list[str]) -> list[str]:
    """Heuristic: which master(s) does this article primarily concern."""
    masters = set()
    text = (article_id + " " + body[:2000]).lower()
    # Entity pages are explicit
    if article_type == "entity":
        if "buffett" in article_id:
            return ["buffett"]
        if "munger" in article_id:
            return ["munger"]
    # Others: content-driven
    buffett_markers = ["buffett", "berkshire", "omaha", "graham", "partnership_letter", "shareholder_letter"]
    munger_markers = ["munger", "wesco", "daily_journal", "poor_charlie", "lollapalooza", "mental_model"]
    b_score = sum(1 for m in buffett_markers if m in text)
    m_score = sum(1 for m in munger_markers if m in text)
    # Always include both for concept/synthesis pages (they are cross-master by design)
    if article_type in ("concept", "synthesis"):
        return ["buffett", "munger"]
    if b_score > 0:
        masters.add("buffett")
    if m_score > 0:
        masters.add("munger")
    if not masters:
        masters = {"buffett", "munger"}  # safe default for uncertain
    return sorted(masters)


def slugify_for_view(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s)
    return s[:80]


def fetch_one(lang: str, article: dict, index_order: int) -> dict:
    """Fetch a single article, write raw + normalized + view, return source record."""
    article_id = article["id"]
    article_type = article["type"]
    path_field = article["path"]  # e.g. "concepts/accounting_quality.md"
    dir_part = path_field.split("/")[0]  # e.g. "concepts"
    expected_size = article.get("size", 0)

    api_url = f"{BASE_URL}/api/{lang}/articles/{dir_part}/{article_id}.txt"

    try:
        content_bytes = http_get(api_url)
    except Exception as e:
        return {"error": str(e), "url": api_url, "article_id": article_id, "lang": lang}

    # Sanity: reject if size is suspicious shell (~934 bytes is the SPA fallback)
    if len(content_bytes) < 1200:
        # Inspect - may be SPA shell
        head = content_bytes[:200].decode("utf-8", errors="replace")
        if "<!doctype" in head.lower():
            return {"error": "got_spa_shell_fallback", "url": api_url, "article_id": article_id,
                    "lang": lang, "bytes": len(content_bytes)}

    sha = sha256_hex(content_bytes)
    sha_prefix = sha[:2]

    # Write raw
    raw_dir = RAW_DIR / sha_prefix / sha
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "payload.md").write_bytes(content_bytes)

    fetch_meta = {
        "source_id": f"src_sha256_{sha}",
        "content_sha256": sha,
        "url": api_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": 200,
        "byte_size": len(content_bytes),
        "user_agent": UA,
        "scan_id": SCAN_ID,
        "source_article": {
            "lang": lang,
            "id": article_id,
            "type": article_type,
            "path": path_field,
            "index_expected_size": expected_size,
            "index_order": index_order,
        },
    }
    (raw_dir / "fetch.json").write_text(json.dumps(fetch_meta, ensure_ascii=False, indent=2))

    # Normalize: parse YAML frontmatter, keep as-is (already markdown)
    content_text = content_bytes.decode("utf-8", errors="replace")
    meta, body = parse_frontmatter(content_text)

    # Compute stable paragraph anchors (hash of each paragraph text)
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    body_with_anchors = []
    for p in paragraphs:
        anchor = "p:" + hashlib.sha256(p.encode("utf-8")).hexdigest()[:6]
        body_with_anchors.append(f"<!-- {anchor} -->\n{p}")
    normalized_body = "\n\n".join(body_with_anchors)

    # Frontmatter we'll add on top of normalized file
    norm_dir = NORM_DIR / sha_prefix
    norm_dir.mkdir(parents=True, exist_ok=True)
    classification = classify_article(article_type, [])
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    masters = detect_masters(article_id, article_type, body, tags)
    norm_frontmatter = {
        "source_id": f"src_sha256_{sha}",
        "scan_id": SCAN_ID,
        "source_url": api_url,
        "public_url": f"{BASE_URL}/{lang}/{article_type}/{article_id}/",
        "lang": lang,
        "article_type": article_type,
        "article_id": article_id,
        "article_date": meta.get("date", ""),
        "tier": classification["tier"],
        "kind": classification["kind"],
        "masters": masters,
        "cross_master": len(masters) > 1,
        "title": body.split("\n")[0].lstrip("# ").strip() if body else "",
        "site_tags": tags,
        "site_sources": meta.get("sources", []) if isinstance(meta.get("sources"), list) else [],
        "word_count_approx": len(body),
        "paragraph_count": len(paragraphs),
        "fetched_at": fetch_meta["fetched_at"],
    }
    fm_yaml = "---\n"
    for k, v in norm_frontmatter.items():
        if isinstance(v, list):
            fm_yaml += f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
        elif isinstance(v, bool):
            fm_yaml += f"{k}: {str(v).lower()}\n"
        elif isinstance(v, (int, float)):
            fm_yaml += f"{k}: {v}\n"
        else:
            fm_yaml += f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
    fm_yaml += "---\n\n"

    (norm_dir / f"{sha}.md").write_text(fm_yaml + normalized_body, encoding="utf-8")

    # Write human-readable view (only for zh)
    view_record = None
    if lang == "zh":
        view_subdir = VIEW_DIR / article_type
        view_subdir.mkdir(parents=True, exist_ok=True)
        safe_id = slugify_for_view(article_id)
        view_path = view_subdir / f"{safe_id}.zh.md"
        view_path.write_text(fm_yaml + normalized_body, encoding="utf-8")
        view_record = str(view_path.relative_to(PROJECT_ROOT))

    # Return source record for registry
    return {
        "source_record": {
            "source_id": f"src_sha256_{sha}",
            "content_sha256": sha,
            "raw_path": str((raw_dir / "payload.md").relative_to(PROJECT_ROOT)),
            "normalized_path": str((norm_dir / f"{sha}.md").relative_to(PROJECT_ROOT)),
            "view_path": view_record,
            "mime": "text/markdown",
            "byte_size": len(content_bytes),
            "fetched_by_scan": SCAN_ID,
            "first_seen_at": fetch_meta["fetched_at"],
            "origin": {
                "url": api_url,
                "public_url": f"{BASE_URL}/{lang}/{article_type}/{article_id}/",
                "http_status": 200,
            },
            "metadata": {
                "title": norm_frontmatter["title"],
                "language": lang,
                "article_type": article_type,
                "article_id": article_id,
                "site_tags": tags,
                "site_cited_sources": norm_frontmatter["site_sources"],
                "word_count_approx": len(body),
            },
            "classification": {
                "kind": classification["kind"],
                "tier": classification["tier"],
                "tier_rationale": classification["tier_rationale"],
                "masters": masters,
                "cross_master": len(masters) > 1,
            },
            "lineage": {"supersedes": None, "also_seen_in_scans": []},
            "status": "active",
        },
        "master_links": [
            {"source_id": f"src_sha256_{sha}", "master_id": m, "role": "primary_subject",
             "tier": classification["tier"], "added_by_scan": SCAN_ID,
             "added_at": fetch_meta["fetched_at"]}
            for m in masters
        ],
    }


def main():
    print(f"=== Scan {SCAN_ID} ===")
    print(f"Started: {SCAN_STARTED}")

    # Download indexes
    zh_idx = json.loads(http_get(f"{BASE_URL}/api/zh/articles.json"))
    en_idx = json.loads(http_get(f"{BASE_URL}/api/en/articles.json"))
    zh_arts = zh_idx["articles"]
    en_arts = en_idx["articles"]
    print(f"zh index: {len(zh_arts)} articles")
    print(f"en index: {len(en_arts)} articles")

    # Selective: zh all + en entity/synthesis only
    to_fetch: list[tuple[str, dict, int]] = []
    for i, a in enumerate(zh_arts):
        to_fetch.append(("zh", a, i))
    en_selected = 0
    for i, a in enumerate(en_arts):
        if a["type"] in ("entity", "synthesis"):
            to_fetch.append(("en", a, i))
            en_selected += 1
    print(f"Selected for fetch: {len(to_fetch)} ({len(zh_arts)} zh + {en_selected} en Tier-B)")

    # Fetch with concurrency
    source_records = []
    master_links = []
    failures = []
    fetched = 0
    duplicates = 0
    seen_hashes = set()

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(fetch_one, lang, art, idx) for lang, art, idx in to_fetch]
        for f in as_completed(futures):
            result = f.result()
            if "error" in result:
                failures.append(result)
                print(f"  FAIL {result['article_id']} ({result.get('lang')}): {result['error']}")
                continue
            sr = result["source_record"]
            if sr["content_sha256"] in seen_hashes:
                duplicates += 1
            else:
                seen_hashes.add(sr["content_sha256"])
                source_records.append(sr)
                master_links.extend(result["master_links"])
                fetched += 1
                if fetched % 30 == 0:
                    print(f"  progress: {fetched}/{len(to_fetch)}")

    scan_finished = datetime.now(timezone.utc).isoformat()
    print(f"\n=== Done ===")
    print(f"Fetched unique: {fetched}")
    print(f"Duplicates: {duplicates}")
    print(f"Failures: {len(failures)}")
    print(f"Finished: {scan_finished}")

    # Append to registry
    REG_DIR.mkdir(parents=True, exist_ok=True)
    sources_fp = REG_DIR / "sources.jsonl"
    master_fp = REG_DIR / "source_masters.jsonl"
    scans_fp = REG_DIR / "scans.jsonl"

    with sources_fp.open("a", encoding="utf-8") as f:
        for sr in source_records:
            f.write(json.dumps(sr, ensure_ascii=False) + "\n")
    with master_fp.open("a", encoding="utf-8") as f:
        for ml in master_links:
            f.write(json.dumps(ml, ensure_ascii=False) + "\n")
    with scans_fp.open("a", encoding="utf-8") as f:
        scan_rec = {
            "scan_id": SCAN_ID,
            "started_at": SCAN_STARTED,
            "finished_at": scan_finished,
            "initiator": "yingchen1027@gmail.com",
            "trigger": "user_manual",
            "target_description": "value-investing-gurus.pages.dev full scan (zh all + en synthesis/entity)",
            "target_urls": [BASE_URL],
            "tool": "scripts/soul/fetch_vig.py",
            "scope": {
                "masters": ["buffett", "munger"],
                "tier_hint": "P4 (some P3 for source pages)",
                "content_kind": "secondary_synthesis",
            },
            "counts": {
                "urls_attempted": len(to_fetch),
                "urls_fetched": fetched,
                "duplicate_sources": duplicates,
                "new_sources": fetched,
                "failures": len(failures),
            },
            "notes": "Site has clean API; we fetched .txt endpoints which return markdown+yaml frontmatter. "
                    "zh fully fetched (120); en fetched only synthesis+entity (14). Skipped en source/concept (redundant).",
            "status": "fetch_completed",
        }
        f.write(json.dumps(scan_rec, ensure_ascii=False) + "\n")

    # Write a summary for humans
    (VIEW_DIR / "README.md").write_text(f"""# value-investing-gurus.pages.dev 扫描（{SCAN_ID}）

**抓取时间**：{SCAN_STARTED} → {scan_finished}

**编者**：用户的投资人朋友（见方法论文章《我用AI整理了巴菲特和芒格69年的思想遗产》）

**抓取统计**：
- 尝试：{len(to_fetch)}
- 成功：{fetched}
- 重复：{duplicates}
- 失败：{len(failures)}

**覆盖**：
- zh 全部：{len(zh_arts)} 篇（concept 63 + source 43 + synthesis 12 + entity 2）
- en 选择性：entity + synthesis（{en_selected} 篇，用于双语校对）
- 跳过：en concept/source（与已有 primary 冗余）

**Tier 分级**：
- concept/synthesis/entity：P4（编者综合）
- source：P3（编者对原件的提炼，我们多数已有 P0 原件）

**如何使用**：
- 浏览：`concept/` `synthesis/` `source/` `entity/` 子目录下的 `.zh.md` 文件
- 每个文件含 YAML frontmatter 标注来源 + 主题 + tier + masters
- 段落锚点 `<!-- p:XXXXXX -->` 便于 extraction 回溯

**下一步**：
- Phase B：LLM 按决策导向 prompt 抽取 extractions
- Phase C-E：匹配 → 验证 NEEDS VERIFICATION → 整合到 W/C v1.1

失败列表（如有）：
```json
{json.dumps(failures, ensure_ascii=False, indent=2)}
```
""", encoding="utf-8")

    # Write failure log
    if failures:
        (REG_DIR / f"{SCAN_ID}-failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=2))

    print(f"\nRegistry updated: {sources_fp}")
    print(f"Scan log: {scans_fp}")
    print(f"View: {VIEW_DIR / 'README.md'}")


if __name__ == "__main__":
    main()
