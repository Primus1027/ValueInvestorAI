#!/usr/bin/env python3
"""Phase 0 of Pre-A Principles Board Debate: build soul doc index.

Parses W / C / Y soul docs into section-level blocks (by H1/H2/H3 headers)
and extracts keywords for each. The index enables RAG retrieval in Phase 1+,
keeping soul doc full text out of the system prompt (which only gets the
section titles + keywords).

Output: prep/soul_index.json
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREP_DIR = PROJECT_ROOT / "prep"

SOUL_SOURCES = {
    "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.1.md",
    "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.1.md",
    "duan": PROJECT_ROOT / "src/souls/documents/Y-duan-soul-v1.0.md",
}

# Minimal stopwords (EN + ZH). Good enough for keyword extraction.
STOPWORDS = set("""
a an and are as at be by for from has have he his her it its of on or that the
this to was were will with you your i we they them their there which who what
how when where why one two three first second last next new also just still
only into about after before between over under above below than then so very
all any some most many much few little more less same other such both each
every no not but if as while because since until unless although though however
do does did doing done done get got getting getting gets go going gone made
make making making made say said says saying see seen saw seeing look looked
looking come came coming coming know knew known knowing think thought thinking
want wanted wanting give gave given giving take took taken taking find found
finding work worked working call called calling ask asked asking try tried
trying need needed needing feel felt feeling become became becoming leave left
leaving put puts puting set sets seen used using like likes liked
""".split())

STOPWORDS_ZH = set("""
的 了 在 是 和 就 都 而 及 与 或 但 并 也 又 上 下 中 为 之 有 无 不 很 更 最 将 可
这 那 里 以 于 从 到 对 被 把 让 使 比 能 会 要 说 看 想 做 用 过 去 来 她 他 它
我 你 您 们 个 只 还 又 等 多 少 些 什么 怎么 为什么 如何 所以 因此 但是 然后
这样 那样 即 则 已 仍 者 里 所 其 某 这些 那些 同 就是 可以 需要 应该
""".split())

# Header regex
H1_RE = re.compile(r"^# (.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^### (.+?)\s*$", re.MULTILINE)
ANY_HEADER_RE = re.compile(r"^(#{1,3}) (.+?)\s*$", re.MULTILINE)


def slugify(text: str) -> str:
    """Turn '## Module 1: Identity & Origins' title into 'module-1-identity-origins'."""
    text = text.lower().strip()
    # Remove punctuation except Chinese chars
    text = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text[:80]  # cap length


def strip_frontmatter_and_html_comments(text: str) -> str:
    """Remove HTML comments and generator headers that aren't real content."""
    # Remove <!-- ... --> blocks
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text


def tokenize(text: str) -> List[str]:
    """Simple tokenizer: words (EN) + single chars (ZH)."""
    # EN words
    en_tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    # ZH characters (single chars are too noisy; use 2-grams)
    zh_chars = re.findall(r"[\u4e00-\u9fff]", text)
    zh_bigrams = ["".join(zh_chars[i:i+2]) for i in range(len(zh_chars) - 1)]
    return en_tokens + zh_bigrams


def extract_keywords(title: str, body: str, top_n: int = 10) -> List[str]:
    """Extract top-N keywords for a section.

    Strategy:
    - Title words always included (high weight)
    - Bold/italic emphasized (**word** or *word*)
    - Top frequent content words (TF)
    """
    keywords = []

    # Title words
    title_tokens = tokenize(title)
    keywords.extend(t for t in title_tokens if t not in STOPWORDS and t not in STOPWORDS_ZH)

    # Emphasized
    emphasized = re.findall(r"\*\*([^*]+)\*\*|\*([^*]+)\*", body)
    for grp in emphasized:
        for phrase in grp:
            if phrase and len(phrase) < 30:
                for tok in tokenize(phrase):
                    if tok not in STOPWORDS and tok not in STOPWORDS_ZH:
                        keywords.append(tok)

    # Content frequency
    body_tokens = tokenize(body)
    filtered = [t for t in body_tokens if t not in STOPWORDS and t not in STOPWORDS_ZH]
    freq = Counter(filtered)
    # Top frequent (but not already in title/emphasized)
    existing = set(keywords)
    for word, _ in freq.most_common(top_n * 2):
        if word not in existing and len(word) >= 2:
            keywords.append(word)
            if len(keywords) >= top_n:
                break

    # Dedupe while preserving order
    seen = set()
    result = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            result.append(k)
        if len(result) >= top_n:
            break

    return result


def parse_soul_doc(master: str, path: Path) -> Dict:
    """Parse one soul doc into section list."""
    raw = path.read_text(encoding="utf-8")
    raw = strip_frontmatter_and_html_comments(raw)

    # Find all headers with positions
    headers = []
    for m in ANY_HEADER_RE.finditer(raw):
        level = len(m.group(1))
        title = m.group(2).strip()
        pos = m.start()
        headers.append((level, title, pos))

    # Build sections: each section = from one header to next (or EOF)
    sections = []
    for i, (level, title, pos) in enumerate(headers):
        # Skip level 1 that are document title or nav (e.g., "# Table of Contents")
        if level == 1 and ("table of contents" in title.lower() or "目录" in title):
            continue

        end_pos = headers[i + 1][2] if i + 1 < len(headers) else len(raw)
        # Content starts after the header line itself
        content_start = raw.find("\n", pos) + 1
        section_body = raw[content_start:end_pos].strip()

        # Skip empty or trivially short sections
        # (Chinese content: len() = char count; 100 chars ≈ 1 paragraph worth of content)
        if len(section_body) < 100:
            continue

        # Build path ancestors: slug chain for H2 under H1, etc.
        ancestors = []
        for j in range(i - 1, -1, -1):
            anc_level, anc_title, _ = headers[j]
            if anc_level < level:
                ancestors.insert(0, slugify(anc_title))
                if anc_level == 1:
                    break
        path_slug = "/".join(ancestors + [slugify(title)]) if ancestors else slugify(title)

        keywords = extract_keywords(title, section_body, top_n=10)
        # Use char count as substantive metric (Chinese text has no whitespace)
        char_count = len(re.sub(r"\s", "", section_body))

        sections.append({
            "section_id": f"{master}/{path_slug}",
            "title": title,
            "level": level,
            "anchor": f"{path.relative_to(PROJECT_ROOT)}#{slugify(title)}",
            "keywords": keywords,
            "char_count": char_count,
            "text": section_body,
        })

    return {
        "master": master,
        "source_path": str(path.relative_to(PROJECT_ROOT)),
        "total_sections": len(sections),
        "sections": sections,
    }


def build_keyword_inverted_index(all_docs: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Build keyword → [section_id] inverted index for fast RAG retrieval."""
    index = {}
    for master, doc in all_docs.items():
        for sec in doc["sections"]:
            for kw in sec["keywords"]:
                index.setdefault(kw, []).append(sec["section_id"])
    return index


def main():
    PREP_DIR.mkdir(parents=True, exist_ok=True)

    all_docs = {}
    for master, path in SOUL_SOURCES.items():
        if not path.exists():
            print(f"WARN: {path} missing, skipping {master}")
            continue
        print(f"Parsing {master}: {path.relative_to(PROJECT_ROOT)}")
        doc = parse_soul_doc(master, path)
        all_docs[master] = doc
        total_chars = sum(s['char_count'] for s in doc['sections'])
        levels = Counter(s['level'] for s in doc['sections'])
        print(f"  → {doc['total_sections']} sections ({total_chars:,} chars) "
              f"| H1:{levels[1]} H2:{levels[2]} H3:{levels[3]}")

    # Build inverted keyword index
    kw_index = build_keyword_inverted_index(all_docs)
    print(f"\nKeyword index: {len(kw_index)} unique keywords across all masters")

    # Write full index (includes section text — used by retrieval, not by prompt)
    full = {
        "version": "1.0",
        "generated_at": "phase0_of_pre-a",
        "masters": list(all_docs.keys()),
        "docs": all_docs,
        "keyword_to_sections": kw_index,
    }
    full_path = PREP_DIR / "soul_index.json"
    full_path.write_text(json.dumps(full, ensure_ascii=False, indent=2))
    size_kb = full_path.stat().st_size / 1024
    print(f"\n✓ Full index: {full_path} ({size_kb:.1f} KB)")

    # Write prompt-friendly summary — PER MASTER.
    # Content structure observation: H1 = module dividers (thin), H2 = section markers
    # (mostly thin), H3 = actual content holders. So filter by char_count, not level.
    # Each prompt TOC entry is lightweight: {section_id, title, level, keywords, char_count}.
    MIN_CHARS_FOR_PROMPT_TOC = 200  # retrieval-worthy threshold
    for master, doc in all_docs.items():
        prompt_sections = [
            {
                "section_id": s["section_id"],
                "title": s["title"],
                "level": s["level"],
                "keywords": s["keywords"][:8],
                "char_count": s["char_count"],
            }
            for s in doc["sections"]
            if s["char_count"] >= MIN_CHARS_FOR_PROMPT_TOC
        ]
        summary = {
            "master": master,
            "source": doc["source_path"],
            "total_retrievable_sections": doc["total_sections"],
            "toc_sections": prompt_sections,
            "note": "Use @retrieve(section_id) in your output to pull specific section text. "
                    "Full retrievable sections (including short ones) in "
                    f"soul_index.json → docs[{master}].sections",
        }
        summary_path = PREP_DIR / f"soul_prompt_toc_{master}.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        size_kb = summary_path.stat().st_size / 1024
        levels = Counter(s["level"] for s in prompt_sections)
        print(f"✓ TOC for {master}: {summary_path.name} "
              f"({size_kb:.1f} KB, {len(prompt_sections)} sections: "
              f"H1:{levels[1]} H2:{levels[2]} H3:{levels[3]})")


if __name__ == "__main__":
    main()
