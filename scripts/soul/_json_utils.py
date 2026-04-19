"""Robust JSON parsing for Claude CLI output.

Claude's JSON output is imperfect: sometimes wrapped in markdown, sometimes
contains unescaped quotes in Chinese strings, sometimes trailing commentary.
This module provides layered fallbacks so 30% of calls don't fail to parse.

Strategy (try in order, return first success):
1. Strip markdown fences, try plain json.loads
2. Apply best-effort cleanup (smart quotes, trailing commas), retry
3. Extract first balanced {...} block, retry
4. Regex-extract common expected fields (decision, reasoning, etc.) as last resort
"""

import json
import re
from typing import Any, Optional, List, Dict, Tuple


# Smart quote → ASCII quote mapping; LLMs sometimes output these.
_SMART_QUOTE_MAP = {
    "\u201c": '"',  # left double
    "\u201d": '"',  # right double
    "\u2018": "'",  # left single
    "\u2019": "'",  # right single
    "\u300c": '"',  # 「
    "\u300d": '"',  # 」
}


def _strip_markdown_fences(s: str) -> str:
    """Remove ```json ... ``` wrapping if present."""
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*\n?", "", s)
    s = re.sub(r"\n?\s*```\s*$", "", s)
    return s.strip()


def _normalize_quotes(s: str) -> str:
    """Replace smart quotes with ASCII quotes."""
    for bad, good in _SMART_QUOTE_MAP.items():
        s = s.replace(bad, good)
    return s


def _remove_trailing_commas(s: str) -> str:
    """Remove trailing commas before ] or }"""
    return re.sub(r",(\s*[\]}])", r"\1", s)


def _extract_balanced_block(s: str) -> Optional[str]:
    """Find the first balanced {...} block (handles nesting)."""
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"' and not escape:
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def _regex_extract_fallback(s: str, expected_keys: List[str]) -> Optional[Dict]:
    """Last-resort: regex-extract string/enum values for the expected keys.

    Only works for flat string/enum fields. Lists and nested objects need full parsing.
    Returns None if no key extracted.
    """
    out = {}
    for key in expected_keys:
        # Match "key": "value" or "key": value (for enums like strong_buy)
        m = re.search(
            rf'"{re.escape(key)}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
            s,
            re.DOTALL,
        )
        if m:
            # Unescape common JSON escapes
            val = m.group(1).replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
            out[key] = val
    return out if out else None


def parse_llm_json(
    raw: str,
    expected_keys: Optional[List[str]] = None,
    debug: bool = False,
) -> Optional[Dict[str, Any]]:
    """Parse LLM-generated JSON with layered fallbacks.

    Args:
        raw: Raw LLM output (may have markdown fences, chinese quotes, etc.)
        expected_keys: If full parse fails, try regex-extract these keys only.
                       Set to None to disable regex fallback.
        debug: If True, return a dict with `_parse_method` annotation.

    Returns:
        Parsed dict, or None if all strategies failed.
    """
    if not raw or not raw.strip():
        return None

    attempts: List[Tuple[str, str]] = []

    # Step 1: plain, after fence strip
    stripped = _strip_markdown_fences(raw)
    attempts.append(("plain", stripped))

    # Step 2: cleanup — smart quotes + trailing commas
    cleaned = _remove_trailing_commas(_normalize_quotes(stripped))
    if cleaned != stripped:
        attempts.append(("cleaned", cleaned))

    # Step 3: balanced block extraction
    balanced = _extract_balanced_block(stripped)
    if balanced and balanced != stripped:
        attempts.append(("balanced", balanced))
    balanced_cleaned = _extract_balanced_block(cleaned) if cleaned != stripped else None
    if balanced_cleaned and balanced_cleaned != cleaned:
        attempts.append(("balanced_cleaned", balanced_cleaned))

    # Try each attempt
    for method, candidate in attempts:
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                if debug:
                    result["_parse_method"] = method
                return result
        except (json.JSONDecodeError, ValueError):
            continue

    # Step 4: regex fallback if caller specified expected keys
    if expected_keys:
        fallback = _regex_extract_fallback(cleaned or stripped, expected_keys)
        if fallback:
            if debug:
                fallback["_parse_method"] = "regex_fallback"
            return fallback

    return None


def parse_claude_cli_result(stdout: str, expected_keys: Optional[List[str]] = None) -> Optional[Dict]:
    """Convenience wrapper for Claude CLI --output-format json.

    Claude CLI wraps the response in {"result": "...", ...}. This function
    unwraps and parses the inner result.

    Args:
        stdout: Raw stdout from `claude -p ... --output-format json`
        expected_keys: Regex-fallback target keys

    Returns:
        Parsed dict from the inner result, or None if unparseable.
    """
    if not stdout:
        return None
    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    inner_raw = outer.get("result", "")
    if not isinstance(inner_raw, str):
        return None
    return parse_llm_json(inner_raw, expected_keys=expected_keys)
