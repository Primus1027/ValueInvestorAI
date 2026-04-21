#!/usr/bin/env python3
"""Seed schema validator (Phase 1 output validation).

Usage (CLI):
    python3 -m scripts.soul.validate_seed <file.jsonl>
    python3 -m scripts.soul.validate_seed --seed '<json_string>'

Library:
    from scripts.soul.validate_seed import validate_seed, validate_seeds_file

Strictness:
- Uses JSON Schema draft-07 if `jsonschema` package available.
- Falls back to inline checks if jsonschema not installed (same semantics for
  the critical rules: atomicity regex, no-digit qualitative_claim, required
  fields). Keeps this module zero-extra-dependency.

Key checks (all enforced regardless of jsonschema presence):
1. Required fields present
2. Enums valid (rule_subject, theme, category, severity, evidence_strength)
3. qualitative_claim does not contain digits or percent
4. qualitative_claim does not contain compound connectives
5. Either quantitative_rule or qualitative_rule is non-null
6. Re-introduction fields all-or-nothing
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    SCHEMAS_DIR, RULE_SUBJECTS, SEVERITIES, CATEGORIES, THEMES, MASTERS,
    EVIDENCE_STRENGTHS,
)

# ─── Regex: forbidden patterns in qualitative_claim ───
_DIGIT_RE = re.compile(r"\d")
_PERCENT_RE = re.compile(r"%|百分")
# Compound-claim connectives — keep list tight to avoid false positives.
# These are in the order "<a>...<b>" where <a> opens the compound.
_COMPOUND_PATTERNS = [
    re.compile(r"既.{1,30}又"),
    re.compile(r"不但.{1,40}而且"),
    re.compile(r"同意.{1,40}但反对"),
    re.compile(r"支持.{1,40}反对"),
    re.compile(r"在.{1,30}同时.{1,30}还要求"),
]

# ─── Required top-level fields ───
REQUIRED_FIELDS = [
    "seed_id", "_master", "rule_subject", "theme", "category",
    "qualitative_claim", "severity", "anti_scope", "rationale",
    "evidence_strength", "supporting_section_id", "supporting_profile_factor",
]

# ─── Try to import jsonschema; fall back to None ───
try:
    import jsonschema as _jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _jsonschema = None
    _HAS_JSONSCHEMA = False


def _load_schema() -> Optional[dict]:
    path = SCHEMAS_DIR / "seed_v1_1.schema.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _check_enum(errors: list, seed: dict, field: str, allowed: tuple) -> None:
    val = seed.get(field)
    if val is not None and val not in allowed:
        errors.append(f"{field}='{val}' not in {allowed}")


def validate_seed(seed: dict, strict: bool = True) -> tuple[bool, list[str]]:
    """Validate a single seed dict. Returns (is_valid, errors list).

    strict=True runs every check; strict=False skips atomicity regex
    (useful if you want to allow a known-compound seed through for analysis).
    """
    errors: list[str] = []

    # 1. Required fields
    for f in REQUIRED_FIELDS:
        if f not in seed or seed[f] is None:
            errors.append(f"missing required field: {f}")

    # Early exit if seed_id missing (makes downstream checks less useful)
    if "seed_id" not in seed:
        return (False, errors)

    # 2. Enums
    _check_enum(errors, seed, "_master", MASTERS)
    _check_enum(errors, seed, "rule_subject", RULE_SUBJECTS)
    _check_enum(errors, seed, "theme", THEMES)
    _check_enum(errors, seed, "category", CATEGORIES)
    _check_enum(errors, seed, "severity", SEVERITIES)
    _check_enum(errors, seed, "evidence_strength", EVIDENCE_STRENGTHS)

    # 3. qualitative_claim — no digits, no percent
    qc = seed.get("qualitative_claim", "") or ""
    if isinstance(qc, str):
        if _DIGIT_RE.search(qc):
            errors.append("qualitative_claim contains digit (move number to quantitative_rule.threshold)")
        if _PERCENT_RE.search(qc):
            errors.append("qualitative_claim contains percent marker (move to quantitative_rule)")
        if len(qc) < 10:
            errors.append(f"qualitative_claim too short: {len(qc)} chars, need >= 10")
        if len(qc) > 300:
            errors.append(f"qualitative_claim too long: {len(qc)} chars, max 300")

        # 4. Atomicity — no compound connectives
        if strict:
            for pat in _COMPOUND_PATTERNS:
                m = pat.search(qc)
                if m:
                    errors.append(
                        f"qualitative_claim contains compound connective '{m.group()}' — split into multiple seeds"
                    )

    # 5. Either quantitative_rule or qualitative_rule non-null
    qr = seed.get("quantitative_rule")
    qlr = seed.get("qualitative_rule")
    if qr is None and (qlr is None or (isinstance(qlr, str) and not qlr.strip())):
        errors.append("at least one of quantitative_rule or qualitative_rule must be non-null")

    # 6. Re-introduction fields consistency
    reintro_from = seed.get("_reintroduced_from")
    if reintro_from is not None and reintro_from != "":
        for req_field in ["_reintroduction_rationale",
                          "_reintroduced_seed_commit_hash",
                          "_reintroduced_seed_section_id"]:
            if not seed.get(req_field):
                errors.append(f"_reintroduced_from set but {req_field} missing/empty")
        commit_hash = seed.get("_reintroduced_seed_commit_hash", "")
        if commit_hash and not re.match(r"^[a-f0-9]{7,40}$", commit_hash):
            errors.append(f"_reintroduced_seed_commit_hash format invalid (expect 7-40 hex chars)")

    # 7. anti_scope non-empty
    anti_scope = seed.get("anti_scope", "") or ""
    if isinstance(anti_scope, str) and len(anti_scope.strip()) < 5:
        errors.append(f"anti_scope too short: {len(anti_scope)} chars, need >= 5")

    # 8. Optional: JSON Schema validation (strict extra layer)
    if _HAS_JSONSCHEMA:
        schema = _load_schema()
        if schema:
            try:
                _jsonschema.validate(seed, schema)
            except _jsonschema.ValidationError as e:
                errors.append(f"jsonschema: {e.message} (at {'/'.join(str(p) for p in e.absolute_path)})")
            except Exception as e:
                # Don't let jsonschema internal errors block validation
                errors.append(f"jsonschema internal: {e}")

    return (len(errors) == 0, errors)


def validate_seeds_file(file_path: str, min_valid: int = 5) -> dict:
    """Validate a jsonl file of seeds. Returns summary dict.

    Args:
        file_path: Path to .jsonl file, one seed per line.
        min_valid: Minimum valid seed count for "passed" flag. Default 5
                   matches Phase 1 minimum threshold.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"file not found: {file_path}", "passed": False}

    total = 0
    valid_count = 0
    invalid_seeds: list[dict] = []

    with path.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                seed = json.loads(line)
            except json.JSONDecodeError as e:
                invalid_seeds.append({
                    "line": line_num,
                    "seed_id": None,
                    "errors": [f"JSON parse error: {e}"],
                })
                continue
            ok, errs = validate_seed(seed, strict=True)
            if ok:
                valid_count += 1
            else:
                invalid_seeds.append({
                    "line": line_num,
                    "seed_id": seed.get("seed_id"),
                    "errors": errs,
                })

    return {
        "file": file_path,
        "total": total,
        "valid": valid_count,
        "invalid": total - valid_count,
        "invalid_seeds": invalid_seeds,
        "passed": valid_count >= min_valid,
        "min_valid_threshold": min_valid,
    }


def main():
    ap = argparse.ArgumentParser(description="Validate seed JSON/JSONL against v1.1 schema")
    ap.add_argument("file", nargs="?", help="Path to .jsonl file to validate")
    ap.add_argument("--seed", help="Single seed JSON string to validate")
    ap.add_argument("--min-valid", type=int, default=5, help="Min valid count for pass")
    ap.add_argument("--json-output", action="store_true", help="Emit JSON summary instead of human-readable")
    args = ap.parse_args()

    if args.seed:
        try:
            seed = json.loads(args.seed)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            sys.exit(2)
        ok, errs = validate_seed(seed, strict=True)
        if args.json_output:
            print(json.dumps({"valid": ok, "errors": errs}, ensure_ascii=False, indent=2))
        else:
            print(f"valid: {ok}")
            for e in errs:
                print(f"  - {e}")
        sys.exit(0 if ok else 1)

    if not args.file:
        ap.print_help()
        sys.exit(2)

    summary = validate_seeds_file(args.file, min_valid=args.min_valid)
    if args.json_output:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"File: {summary.get('file')}")
        print(f"Total seeds: {summary.get('total')}")
        print(f"Valid: {summary.get('valid')}")
        print(f"Invalid: {summary.get('invalid')}")
        print(f"Min required: {summary.get('min_valid_threshold')}")
        print(f"Passed: {summary.get('passed')}")
        if summary.get("invalid_seeds"):
            print("\nInvalid seeds:")
            for item in summary["invalid_seeds"]:
                print(f"  line {item['line']} ({item.get('seed_id', '?')}):")
                for e in item["errors"]:
                    print(f"    - {e}")
    sys.exit(0 if summary.get("passed") else 1)


if __name__ == "__main__":
    main()
