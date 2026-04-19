#!/usr/bin/env python3
"""
Retry fetch for missing articles from value-investing-gurus, using curl subprocess
(more robust than urllib against Cloudflare's chunked responses).

Idempotent: skips articles already in sources.jsonl.
Updates sources.jsonl + source_masters.jsonl in place.
"""

import hashlib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://value-investing-gurus.pages.dev"

RAW_DIR = PROJECT_ROOT / "Resources/Sources/raw"
NORM_DIR = PROJECT_ROOT / "Resources/Sources/normalized"
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
VIEW_DIR = PROJECT_ROOT / "Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04"
SCAN_ID = "scan_2026-04-19_vig"


def curl_get(url: str, retries: int = 5) -> bytes:
    """Fetch via curl subprocess. Returns bytes, raises on failure."""
    last_err = None
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["curl", "-s", "-f", "--compressed", "-L", "--max-time", "30",
                 "-A", "Mozilla/5.0 (valueinvestor-ai-scanner/1.0)", url],
                capture_output=True, timeout=45, check=True)
            if len(result.stdout) < 1200:
                head = result.stdout[:200].decode("utf-8", errors="replace")
                if "<!doctype" in head.lower():
                    raise RuntimeError(f"got_spa_shell_fallback bytes={len(result.stdout)}")
            return result.stdout
        except Exception as e:
            last_err = e
            time.sleep(1.5 ** attempt)
    raise RuntimeError(f"curl failed for {url}: {last_err}")


def parse_frontmatter(md: str) -> tuple[dict, str]:
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
        k = k.strip(); v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            meta[k] = [x.strip().strip('"\'') for x in inner.split(",")] if inner else []
        else:
            meta[k] = v.strip('"\'')
    return meta, body


def classify_article(article_type: str) -> dict:
    if article_type == "concept":
        return {"kind": "secondary_synthesis", "tier": "P4",
                "tier_rationale": "Editorial concept page synthesizing multiple primary sources"}
    if article_type == "synthesis":
        return {"kind": "secondary_synthesis", "tier": "P4",
                "tier_rationale": "Editor's cross-document thematic analysis"}
    if article_type == "source":
        return {"kind": "secondary_synthesis", "tier": "P3",
                "tier_rationale": "Site's distilled view of a known primary source"}
    if article_type == "entity":
        return {"kind": "tertiary", "tier": "P4",
                "tier_rationale": "Editor's profile write-up of a master"}
    return {"kind": "tertiary", "tier": "P4", "tier_rationale": "Unknown"}


def detect_masters(article_id: str, article_type: str, body: str) -> list[str]:
    if article_type == "entity":
        if "buffett" in article_id: return ["buffett"]
        if "munger" in article_id: return ["munger"]
    if article_type in ("concept", "synthesis"):
        return ["buffett", "munger"]
    text = (article_id + " " + body[:2000]).lower()
    b = any(m in text for m in ["buffett", "berkshire", "omaha", "graham", "partnership_letter", "shareholder_letter"])
    m = any(x in text for x in ["munger", "wesco", "daily_journal", "poor_charlie", "lollapalooza"])
    result = []
    if b: result.append("buffett")
    if m: result.append("munger")
    if not result: result = ["buffett", "munger"]
    return result


def slugify(s: str) -> str:
    return re.sub(r"[^\w\-]+", "_", s)[:80]


def get_existing_source_ids() -> set:
    """Read sources.jsonl to find already-fetched source_ids (dedup)."""
    sfile = REG_DIR / "sources.jsonl"
    if not sfile.exists():
        return set()
    existing = set()
    # Match on public_url to dedup by URL (not hash, since body may slightly differ)
    url_map = {}
    for line in sfile.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        existing.add(r["source_id"])
        url_map[r["origin"]["public_url"]] = r["source_id"]
    return existing, url_map


def fetch_one(lang: str, article: dict, idx: int) -> dict:
    article_id = article["id"]
    article_type = article["type"]
    path_field = article["path"]
    dir_part = path_field.split("/")[0]
    api_url = f"{BASE_URL}/api/{lang}/articles/{dir_part}/{article_id}.txt"
    public_url = f"{BASE_URL}/{lang}/{article_type}/{article_id}/"

    try:
        content_bytes = curl_get(api_url)
    except Exception as e:
        return {"error": str(e), "url": api_url, "article_id": article_id, "lang": lang}

    sha = hashlib.sha256(content_bytes).hexdigest()
    sha_prefix = sha[:2]

    raw_dir = RAW_DIR / sha_prefix / sha
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "payload.md").write_bytes(content_bytes)

    now = datetime.now(timezone.utc).isoformat()
    fetch_meta = {
        "source_id": f"src_sha256_{sha}",
        "content_sha256": sha,
        "url": api_url,
        "fetched_at": now,
        "http_status": 200,
        "byte_size": len(content_bytes),
        "scan_id": SCAN_ID,
        "source_article": {"lang": lang, "id": article_id, "type": article_type, "path": path_field, "index_order": idx},
    }
    (raw_dir / "fetch.json").write_text(json.dumps(fetch_meta, ensure_ascii=False, indent=2))

    text = content_bytes.decode("utf-8", errors="replace")
    meta, body = parse_frontmatter(text)

    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    body_with_anchors = []
    for p in paragraphs:
        anchor = "p:" + hashlib.sha256(p.encode("utf-8")).hexdigest()[:6]
        body_with_anchors.append(f"<!-- {anchor} -->\n{p}")
    normalized_body = "\n\n".join(body_with_anchors)

    classification = classify_article(article_type)
    tags = meta.get("tags", []) if isinstance(meta.get("tags"), list) else []
    sources_list = meta.get("sources", []) if isinstance(meta.get("sources"), list) else []
    masters = detect_masters(article_id, article_type, body)
    title = ""
    for ln in body.split("\n"):
        if ln.strip().startswith("# "):
            title = ln.strip().lstrip("# ").strip()
            break

    fm = {
        "source_id": f"src_sha256_{sha}",
        "scan_id": SCAN_ID,
        "source_url": api_url,
        "public_url": public_url,
        "lang": lang,
        "article_type": article_type,
        "article_id": article_id,
        "article_date": meta.get("date", ""),
        "tier": classification["tier"],
        "kind": classification["kind"],
        "masters": masters,
        "cross_master": len(masters) > 1,
        "title": title,
        "site_tags": tags,
        "site_sources": sources_list,
        "word_count_approx": len(body),
        "paragraph_count": len(paragraphs),
        "fetched_at": now,
    }
    fm_yaml = "---\n"
    for k, v in fm.items():
        if isinstance(v, list):
            fm_yaml += f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
        elif isinstance(v, bool):
            fm_yaml += f"{k}: {str(v).lower()}\n"
        elif isinstance(v, (int, float)):
            fm_yaml += f"{k}: {v}\n"
        else:
            fm_yaml += f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
    fm_yaml += "---\n\n"

    norm_sub = NORM_DIR / sha_prefix
    norm_sub.mkdir(parents=True, exist_ok=True)
    (norm_sub / f"{sha}.md").write_text(fm_yaml + normalized_body, encoding="utf-8")

    view_record = None
    if lang == "zh":
        view_sub = VIEW_DIR / article_type
        view_sub.mkdir(parents=True, exist_ok=True)
        view_path = view_sub / f"{slugify(article_id)}.zh.md"
        view_path.write_text(fm_yaml + normalized_body, encoding="utf-8")
        view_record = str(view_path.relative_to(PROJECT_ROOT))

    return {
        "source_record": {
            "source_id": f"src_sha256_{sha}",
            "content_sha256": sha,
            "raw_path": str((raw_dir / "payload.md").relative_to(PROJECT_ROOT)),
            "normalized_path": str((norm_sub / f"{sha}.md").relative_to(PROJECT_ROOT)),
            "view_path": view_record,
            "mime": "text/markdown",
            "byte_size": len(content_bytes),
            "fetched_by_scan": SCAN_ID,
            "first_seen_at": now,
            "origin": {"url": api_url, "public_url": public_url, "http_status": 200},
            "metadata": {
                "title": title, "language": lang,
                "article_type": article_type, "article_id": article_id,
                "site_tags": tags, "site_cited_sources": sources_list,
                "word_count_approx": len(body),
            },
            "classification": {
                "kind": classification["kind"], "tier": classification["tier"],
                "tier_rationale": classification["tier_rationale"],
                "masters": masters, "cross_master": len(masters) > 1,
            },
            "lineage": {"supersedes": None, "also_seen_in_scans": []},
            "status": "active",
        },
        "master_links": [
            {"source_id": f"src_sha256_{sha}", "master_id": m, "role": "primary_subject",
             "tier": classification["tier"], "added_by_scan": SCAN_ID, "added_at": now}
            for m in masters
        ],
    }


def main():
    zh_idx = json.loads(curl_get(f"{BASE_URL}/api/zh/articles.json"))
    en_idx = json.loads(curl_get(f"{BASE_URL}/api/en/articles.json"))

    to_fetch = []
    for i, a in enumerate(zh_idx["articles"]):
        to_fetch.append(("zh", a, i))
    for i, a in enumerate(en_idx["articles"]):
        if a["type"] in ("entity", "synthesis"):
            to_fetch.append(("en", a, i))

    existing_ids, url_map = get_existing_source_ids()
    # Skip articles whose public_url already in registry
    pending = []
    for lang, a, idx in to_fetch:
        public_url = f"{BASE_URL}/{lang}/{a['type']}/{a['id']}/"
        if public_url in url_map:
            continue
        pending.append((lang, a, idx))

    print(f"Total target: {len(to_fetch)}, already in registry: {len(to_fetch) - len(pending)}, retrying: {len(pending)}")

    new_records = []
    new_links = []
    failures = []
    success = 0

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(fetch_one, lang, a, idx) for lang, a, idx in pending]
        for f in as_completed(futures):
            r = f.result()
            if "error" in r:
                failures.append(r)
                print(f"  STILL FAIL {r['article_id']} ({r.get('lang')}): {r['error']}")
                continue
            new_records.append(r["source_record"])
            new_links.extend(r["master_links"])
            success += 1
            if success % 20 == 0:
                print(f"  progress: {success}/{len(pending)}")

    if new_records:
        with (REG_DIR / "sources.jsonl").open("a", encoding="utf-8") as f:
            for sr in new_records:
                f.write(json.dumps(sr, ensure_ascii=False) + "\n")
        with (REG_DIR / "source_masters.jsonl").open("a", encoding="utf-8") as f:
            for ml in new_links:
                f.write(json.dumps(ml, ensure_ascii=False) + "\n")

    # Update scan record
    scan_rec = {
        "scan_id": SCAN_ID,
        "event": "retry_batch",
        "retry_at": datetime.now(timezone.utc).isoformat(),
        "retried_count": len(pending),
        "succeeded_in_retry": success,
        "still_failing": len(failures),
    }
    with (REG_DIR / "scans.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(scan_rec, ensure_ascii=False) + "\n")

    if failures:
        (REG_DIR / f"{SCAN_ID}-failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=2))

    print(f"\nRetry summary: {success} new, {len(failures)} still failing")
    total_in_registry = len(existing_ids) + success
    print(f"Total in registry now: {total_in_registry} / {len(to_fetch)} ({total_in_registry*100//len(to_fetch)}%)")


if __name__ == "__main__":
    main()
