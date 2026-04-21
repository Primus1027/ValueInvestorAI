"""Compliance scanner (Phase E).

Scans all debate artifacts for:
1. Identity-impersonation language ("你是 Buffett", etc.) — FAIL
2. qualitative_claim containing digits — WARNING (trigger retry)
3. Compound-claim connectives in seeds — WARNING
4. Fingerprint words in Phase 2+ inputs (post-sanitize) — FAIL (re-sanitize)
5. Prompt-file de-anonymization ("W — 分别对应 buffett") — FAIL (block debate)

Usage (CLI):
    python3 -m scripts.soul.board.compliance --debate-id 2026-04-21_manual
    python3 -m scripts.soul.board.compliance --file <path>
    python3 -m scripts.soul.board.compliance --prompts-dir  # scan prompt templates
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

from scripts.soul.board import (
    PROJECT_ROOT, PROMPTS_DIR, FINGERPRINT_DICT_PATH, PREP_DIR, HISTORY_DIR,
)


# ─── Rule definitions ───

IMPERSONATION_PATTERNS = [
    re.compile(r"你是\s*(Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格|Duan)", re.IGNORECASE),
    re.compile(r"你扮演\s*(Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格)", re.IGNORECASE),
    re.compile(r"You\s+are\s+(Warren|Charlie|Duan|Buffett|Munger)", re.IGNORECASE),
    re.compile(r"(保持|keep).{0,20}(风格|口吻|personality|voice).{0,40}(Buffett|Munger|段永平|巴菲特|芒格)", re.IGNORECASE),
    re.compile(r"(像|think\s+like|impersonate|as\s+if\s+you\s+were).{0,20}(Buffett|Munger|段永平|巴菲特|芒格)", re.IGNORECASE),
]

DE_ANONYMIZATION_PATTERNS = [
    # "W/C/Y 分别对应 buffett / munger / duan" 这类 de-anon 语句
    re.compile(r"(W|C|Y|A|B|C)\s*[—\-]\s*(buffett|munger|duan)", re.IGNORECASE),
    re.compile(r"(W|C|Y|A|B|C)\s*=\s*(buffett|munger|duan)", re.IGNORECASE),
    re.compile(r"分别对应.{0,20}(buffett|munger|duan)", re.IGNORECASE),
    re.compile(r"(buffett|munger|duan).{0,20}(分别对应|对应的是|i\.?e\.?).{0,20}(W|C|Y|A|B|C)", re.IGNORECASE),
]

DIGIT_IN_CLAIM_RE = re.compile(r"\d")
COMPOUND_CLAIM_PATTERNS = [
    re.compile(r"既.{1,30}又"),
    re.compile(r"不但.{1,40}而且"),
    re.compile(r"同意.{1,40}但反对"),
    re.compile(r"在.{1,30}同时.{1,30}还要求"),
]


def _load_fingerprint_dict() -> tuple[dict, list[re.Pattern]]:
    """Return (replacements_dict, scan_patterns_compiled)."""
    if not FINGERPRINT_DICT_PATH.exists():
        return {}, []
    data = json.loads(FINGERPRINT_DICT_PATH.read_text(encoding="utf-8"))
    replacements = data.get("replacements", {})
    scan_pats_raw = data.get("_scan_patterns", {}).get("patterns", [])
    scan_pats = [re.compile(p, re.IGNORECASE) for p in scan_pats_raw]
    return replacements, scan_pats


def _violation(rule_id: str, severity: str, file: str, line: int,
               match: str, context: str) -> dict:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "file": str(file),
        "line": line,
        "match": match[:200],
        "context": context[:500],
    }


def scan_text_for_patterns(text: str, file: Path, patterns: list[re.Pattern],
                            rule_id: str, severity: str) -> list[dict]:
    violations: list[dict] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        for pat in patterns:
            m = pat.search(line)
            if m:
                violations.append(_violation(
                    rule_id, severity, file, line_num, m.group(0), line,
                ))
    return violations


def scan_impersonation(file: Path) -> list[dict]:
    """Any artifact — check for identity-impersonation language."""
    try:
        text = file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    return scan_text_for_patterns(text, file, IMPERSONATION_PATTERNS,
                                   "impersonation", "fail")


def scan_de_anonymization(file: Path) -> list[dict]:
    """Prompt files and orchestration code — check for W/C/Y → master mapping leaks."""
    try:
        text = file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    return scan_text_for_patterns(text, file, DE_ANONYMIZATION_PATTERNS,
                                   "de_anonymization", "fail")


def scan_seed_file_qualitative_claims(file: Path) -> list[dict]:
    """JSONL files — check each seed's qualitative_claim for digits and compounds."""
    violations: list[dict] = []
    try:
        text = file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            seed = json.loads(line)
        except json.JSONDecodeError:
            continue
        claim = seed.get("qualitative_claim", "")
        if not isinstance(claim, str):
            continue
        # Check digits
        if DIGIT_IN_CLAIM_RE.search(claim):
            violations.append(_violation(
                "qual_claim_has_digit", "warning", file, line_num,
                DIGIT_IN_CLAIM_RE.search(claim).group(0), claim,
            ))
        # Check compound
        for pat in COMPOUND_CLAIM_PATTERNS:
            m = pat.search(claim)
            if m:
                violations.append(_violation(
                    "seed_compound", "warning", file, line_num,
                    m.group(0), claim,
                ))
                break  # one compound finding per claim is enough
    return violations


def scan_fingerprints_in_text_field_file(file: Path) -> list[dict]:
    """Sanitized jsonl (Phase 1.5 output onwards) — should NOT contain fingerprint words."""
    _, scan_pats = _load_fingerprint_dict()
    if not scan_pats:
        return []
    violations: list[dict] = []
    try:
        text = file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return []
    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            seed = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Check sanitized seeds - scan qualitative_claim, rationale, anti_scope
        for field in ("qualitative_claim", "rationale", "anti_scope"):
            val = seed.get(field, "")
            if not isinstance(val, str):
                continue
            for pat in scan_pats:
                m = pat.search(val)
                if m:
                    violations.append(_violation(
                        "fingerprint_leak", "fail", file, line_num,
                        f"field={field}: {m.group(0)}", val,
                    ))
    return violations


def scan_file(file: Path, scan_types: Optional[list[str]] = None) -> list[dict]:
    """Run applicable scans based on filename / path conventions.

    scan_types can be a list of strings like ["impersonation", "de_anon", ...]
    to restrict. Default: infer from filename.
    """
    name = file.name
    path_str = str(file)

    # Always scan for impersonation
    violations: list[dict] = []
    if scan_types is None or "impersonation" in scan_types:
        violations.extend(scan_impersonation(file))

    # De-anon: scan if file is in _prompts/ or board/ or is a python file
    if (scan_types is None and ("/_prompts/" in path_str or "/board/" in path_str
                                 or name.endswith(".py"))) or (scan_types and "de_anon" in scan_types):
        violations.extend(scan_de_anonymization(file))

    # Seed-level checks for *_seeds.jsonl or phase1_*.jsonl files
    if (scan_types is None and name.endswith(".jsonl") and "seed" in name) or \
       (scan_types and "seed_qual" in scan_types):
        violations.extend(scan_seed_file_qualitative_claims(file))

    # Fingerprint checks for post-sanitize artifacts
    if (scan_types is None and "phase1_5_" in name and name.endswith(".jsonl")) or \
       (scan_types is None and name.startswith("phase2_") and name.endswith(".jsonl")) or \
       (scan_types and "fingerprint" in scan_types):
        violations.extend(scan_fingerprints_in_text_field_file(file))

    return violations


def scan_directory(directory: Path, glob_pattern: str = "**/*") -> dict:
    """Scan all matching files in a directory."""
    all_violations: list[dict] = []
    files_scanned = 0
    if not directory.exists():
        return {"directory": str(directory), "error": "directory not found",
                "violations": [], "summary": {}}

    for f in directory.glob(glob_pattern):
        if not f.is_file():
            continue
        if f.suffix not in (".md", ".jsonl", ".json", ".py", ".txt"):
            continue
        if "__pycache__" in f.parts:
            continue
        files_scanned += 1
        all_violations.extend(scan_file(f))

    fail_count = sum(1 for v in all_violations if v["severity"] == "fail")
    warning_count = sum(1 for v in all_violations if v["severity"] == "warning")
    return {
        "directory": str(directory),
        "files_scanned": files_scanned,
        "violations": all_violations,
        "summary": {
            "fail_count": fail_count,
            "warning_count": warning_count,
            "total": len(all_violations),
        },
        "passed": fail_count == 0,
    }


def scan_debate_artifacts(debate_id: str) -> dict:
    """Scan all artifacts for one debate run (prep + history/{debate_id})."""
    history_debate = HISTORY_DIR / debate_id
    prep_result = scan_directory(PREP_DIR) if PREP_DIR.exists() else {
        "directory": str(PREP_DIR), "files_scanned": 0, "violations": [], "summary": {}
    }
    history_result = scan_directory(history_debate) if history_debate.exists() else {
        "directory": str(history_debate), "files_scanned": 0, "violations": [], "summary": {}
    }
    all_violations = prep_result.get("violations", []) + history_result.get("violations", [])
    fail_count = sum(1 for v in all_violations if v["severity"] == "fail")
    return {
        "debate_id": debate_id,
        "prep_scan": prep_result,
        "history_scan": history_result,
        "fail_count": fail_count,
        "total_violations": len(all_violations),
        "passed": fail_count == 0,
    }


def scan_prompts_dir() -> dict:
    """Scan all prompt templates — used before debate start to block de-anon leaks."""
    return scan_directory(PROMPTS_DIR)


def main():
    ap = argparse.ArgumentParser(description="Compliance scanner for debate artifacts")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--debate-id", help="Scan all artifacts for one debate run")
    g.add_argument("--file", help="Scan a single file")
    g.add_argument("--dir", help="Scan a directory")
    g.add_argument("--prompts-dir", action="store_true", help="Scan prompt templates")
    ap.add_argument("--json-output", action="store_true")
    args = ap.parse_args()

    if args.debate_id:
        result = scan_debate_artifacts(args.debate_id)
    elif args.file:
        violations = scan_file(Path(args.file))
        fail_count = sum(1 for v in violations if v["severity"] == "fail")
        result = {"file": args.file, "violations": violations,
                  "fail_count": fail_count,
                  "passed": fail_count == 0}
    elif args.dir:
        result = scan_directory(Path(args.dir))
    elif args.prompts_dir:
        result = scan_prompts_dir()
    else:
        ap.print_help()
        sys.exit(2)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        passed = result.get("passed", False)
        print(f"Passed: {passed}")
        print(f"Violations: {result.get('total_violations', result.get('summary', {}).get('total', len(result.get('violations', []))))}")
        for v in result.get("violations", []) or \
                (result.get("prep_scan", {}).get("violations", []) +
                 result.get("history_scan", {}).get("violations", [])):
            print(f"  [{v['severity'].upper()}] {v['rule_id']} at {v['file']}:{v['line']}")
            print(f"    match: {v['match']}")
    sys.exit(0 if result.get("passed") else 1)


if __name__ == "__main__":
    main()
