#!/usr/bin/env python3
"""Phase E: Compliance output scan.

Scans all Pre-A intermediate and final outputs for Usage Policy violations
(impersonation patterns of real investment masters). Per
Designs/prompt-framing-guidelines.md.

Usage:
  python3 scripts/soul/compliance_scan.py
  python3 scripts/soul/compliance_scan.py <specific_file>
"""

import re
import sys
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREP_DIR = PROJECT_ROOT / "prep"
PRINCIPLES_DIR = PROJECT_ROOT / "Principles"

# Forbidden patterns (from Designs/prompt-framing-guidelines.md)
FORBIDDEN_PATTERNS = [
    (r"你是\s*(Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格)", "impersonation_zh"),
    (r"You are (Warren|Charlie|Li Lu|Duan)\b", "impersonation_en"),
    (r"\bI, (Buffett|Munger|Duan|Warren|Charlie)\b", "first_person_zh"),
    (r"我作为\s*(巴菲特|芒格|段永平)", "first_person_en"),
    (r"(保持|keep)[^。\.!\?\n]{0,40}(Buffett|Munger|段永平|巴菲特|芒格)[^。\.!\?\n]{0,40}(风格|口吻|personality|voice)", "keep_style"),
    (r"(像|think like|as if you were)\s*(Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格)\s*(一样|一般)?思考", "think_like"),
    (r"impersonate\s+(Buffett|Munger|段永平|Warren|Charlie)", "impersonate_verb"),
]

# Whitelist phrases that would otherwise match (e.g., "think like owners" is
# a value-investing concept about portfolio-company management, not impersonation)
WHITELIST_PHRASES = [
    "think like owners",
    "think like an owner",
    "think like shareholders",
    "does not impersonate",
    "NOT impersonate",
    "不扮演这个人物",
    "不扮演 {master}",
    "严禁扮演",
]


def scan_text(text: str, source: str) -> List[Dict]:
    """Scan one text blob for violations."""
    violations = []
    for pattern, pattern_id in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Context window: 60 chars before + 60 after
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context = text[start:end]

            # Whitelist check
            if any(wl.lower() in context.lower() for wl in WHITELIST_PHRASES):
                continue

            violations.append({
                "source": source,
                "pattern_id": pattern_id,
                "match": match.group(),
                "position": match.start(),
                "context": context.replace("\n", " "),
            })
    return violations


def scan_file(path: Path) -> List[Dict]:
    """Scan a single file (or return [] if not readable)."""
    path = path.resolve() if path.exists() else path
    if not path.exists() or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    try:
        source = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        source = str(path)
    return scan_text(text, source)


def main():
    files_to_scan: List[Path] = []

    if len(sys.argv) > 1:
        files_to_scan = [Path(arg) for arg in sys.argv[1:]]
    else:
        # Default: scan all prep/* and Principles/* and relevant scripts
        for d in [PREP_DIR, PRINCIPLES_DIR]:
            if d.exists():
                for p in d.rglob("*"):
                    if p.is_file() and p.suffix in (".md", ".json", ".jsonl"):
                        files_to_scan.append(p)

    print(f"=== Compliance Scan: {len(files_to_scan)} files ===\n")

    all_violations: List[Dict] = []
    for path in files_to_scan:
        vs = scan_file(path)
        if vs:
            all_violations.extend(vs)

    # Group by file
    by_file: Dict[str, List[Dict]] = {}
    for v in all_violations:
        by_file.setdefault(v["source"], []).append(v)

    if not all_violations:
        print("✓ 0 violations found.")
        # For Principles/v1.0.md specifically, verify it was scanned
        v10 = PRINCIPLES_DIR / "v1.0.md"
        if v10.exists():
            print(f"✓ Principles/v1.0.md scanned clean")
        return 0

    print(f"⚠ {len(all_violations)} violations in {len(by_file)} files:\n")
    for file_path, vs in sorted(by_file.items()):
        print(f"--- {file_path} ({len(vs)} violations) ---")
        for v in vs[:5]:  # show first 5 per file
            print(f"  [{v['pattern_id']}] match='{v['match']}'")
            print(f"    context: ...{v['context']}...")
            print()
        if len(vs) > 5:
            print(f"  ... and {len(vs) - 5} more")

    return 1


if __name__ == "__main__":
    sys.exit(main())
