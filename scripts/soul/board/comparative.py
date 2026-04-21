"""Phase 2: Three-layer semantic equivalence detection.

Layer 1: Pairwise Sonnet — for each (seed_i, seed_j), ask "equivalent? yes/no".
Layer 2: Opus critic — arbitrate low-confidence pairs.
Layer 3: Consistency critic — check transitivity (A≡B ∧ B≡C → A≡C); re-run
         violating triples.

Output: prep/phase2_final_matrix.jsonl — final equivalence matrix.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
from typing import Optional

from scripts.soul.board import (
    PROJECT_ROOT, PREP_DIR, PROMPTS_DIR,
)

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "soul"))
from _json_utils import parse_claude_cli_result  # noqa: E402

SONNET_TIMEOUT = 90
OPUS_TIMEOUT = 180


# ─── Defensive coercion helpers ───
# LLM JSON can come through regex-fallback path as strings.
# bool("false") == True in Python, so we need explicit string handling.

_TRUTHY_STRINGS = {"true", "yes", "1", "等价", "是", "t", "y"}
_FALSY_STRINGS = {"false", "no", "0", "不等价", "否", "f", "n", ""}


def _coerce_bool(val, default: bool = False) -> bool:
    """Robust bool coercion. Handles real booleans and common string tokens."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in _TRUTHY_STRINGS:
            return True
        if s in _FALSY_STRINGS:
            return False
    return default


def _coerce_float(val, default: float = 0.0) -> float:
    """Robust float coercion. Returns default on any conversion error."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.strip())
        except (ValueError, TypeError):
            return default
    return default
PAIRWISE_BATCH_SIZE = 10
PAIRWISE_BATCH_SLEEP = 20  # seconds between batches
LOW_CONF_THRESHOLD = 0.7


# ─────────── Layer 1: Pairwise Sonnet ───────────

def render_pairwise_prompt(seed_a: dict, seed_b: dict) -> str:
    template = (PROMPTS_DIR / "phase2_pairwise.md").read_text(encoding="utf-8")
    return template.format(
        claim_a=seed_a.get("qualitative_claim", ""),
        rule_subject_a=seed_a.get("rule_subject", ""),
        theme_a=seed_a.get("theme", ""),
        claim_b=seed_b.get("qualitative_claim", ""),
        rule_subject_b=seed_b.get("rule_subject", ""),
        theme_b=seed_b.get("theme", ""),
    )


def _pair_id(seed_a: dict, seed_b: dict) -> str:
    """Globally-unique pair identifier that survives cross-master seed_id collisions."""
    ma = seed_a.get("_master", "?")
    mb = seed_b.get("_master", "?")
    return f"{ma}/{seed_a.get('seed_id', '?')}__{mb}/{seed_b.get('seed_id', '?')}"


def _base_matrix_record(seed_a: dict, seed_b: dict) -> dict:
    """Common fields every matrix record must carry for namespace-safe downstream lookup."""
    return {
        "pair_id": _pair_id(seed_a, seed_b),
        "seed_ids": [seed_a["seed_id"], seed_b["seed_id"]],
        "masters": [seed_a.get("_master"), seed_b.get("_master")],
    }


def call_pairwise(seed_a: dict, seed_b: dict) -> dict:
    prompt = render_pairwise_prompt(seed_a, seed_b)
    base = _base_matrix_record(seed_a, seed_b)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=SONNET_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {**base, "equivalent": False, "confidence": 0.0,
                    "brief_reason": "error",
                    "error": f"exit {res.returncode}"}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["equivalent", "confidence", "brief_reason"])
        if not parsed:
            return {**base, "equivalent": False, "confidence": 0.0,
                    "brief_reason": "parse_fail"}
        return {
            **base,
            "equivalent": _coerce_bool(parsed.get("equivalent"), default=False),
            "confidence": _coerce_float(parsed.get("confidence"), default=0.0),
            "brief_reason": str(parsed.get("brief_reason", ""))[:200],
        }
    except subprocess.TimeoutExpired:
        return {**base, "equivalent": False, "confidence": 0.0,
                "brief_reason": "timeout"}
    except Exception as e:
        return {**base, "equivalent": False, "confidence": 0.0,
                "brief_reason": f"err:{e}"}


def pairwise_layer1(all_seeds: list[dict], batch_size: int = PAIRWISE_BATCH_SIZE,
                     sleep_between: int = PAIRWISE_BATCH_SLEEP) -> list[dict]:
    """Run pairwise in batches of `batch_size` concurrent calls.

    Pairs with different rule_subject are assigned equivalent=False automatically
    (hard constraint), skipping LLM call.
    """
    pairs = list(combinations(all_seeds, 2))
    print(f"[phase2.L1] Running pairwise on {len(pairs)} pairs "
          f"(batch={batch_size}, sleep={sleep_between}s)")

    matrix: list[dict] = []

    # Filter: different rule_subject → auto non-equivalent
    llm_pairs = []
    for a, b in pairs:
        if a.get("rule_subject") != b.get("rule_subject"):
            matrix.append({
                **_base_matrix_record(a, b),
                "equivalent": False,
                "confidence": 1.0,
                "brief_reason": "different_rule_subject",
                "skipped_llm": True,
            })
        else:
            llm_pairs.append((a, b))

    print(f"[phase2.L1] {len(matrix)} pairs skipped (different rule_subject), "
          f"{len(llm_pairs)} pairs for LLM")

    # Batched concurrent calls
    for batch_idx in range(0, len(llm_pairs), batch_size):
        batch = llm_pairs[batch_idx:batch_idx + batch_size]
        with ThreadPoolExecutor(max_workers=batch_size) as ex:
            results = list(ex.map(lambda pair: call_pairwise(pair[0], pair[1]), batch))
        matrix.extend(results)
        done = min(batch_idx + batch_size, len(llm_pairs))
        print(f"[phase2.L1] progress: {done}/{len(llm_pairs)}")
        if batch_idx + batch_size < len(llm_pairs):
            time.sleep(sleep_between)

    return matrix


# ─────────── Layer 2: Opus critic ───────────

def render_opus_critic_prompt(seed_a: dict, seed_b: dict, sonnet_result: dict) -> str:
    template = (PROMPTS_DIR / "phase2_opus_critic.md").read_text(encoding="utf-8")
    return template.format(
        sonnet_equivalent=sonnet_result.get("equivalent"),
        sonnet_confidence=sonnet_result.get("confidence"),
        sonnet_brief_reason=sonnet_result.get("brief_reason", ""),
        claim_a=seed_a.get("qualitative_claim", ""),
        rule_subject_a=seed_a.get("rule_subject", ""),
        theme_a=seed_a.get("theme", ""),
        quantitative_rule_a=json.dumps(seed_a.get("quantitative_rule"), ensure_ascii=False),
        severity_a=seed_a.get("severity", ""),
        rationale_a=seed_a.get("rationale", ""),
        anti_scope_a=seed_a.get("anti_scope", ""),
        claim_b=seed_b.get("qualitative_claim", ""),
        rule_subject_b=seed_b.get("rule_subject", ""),
        theme_b=seed_b.get("theme", ""),
        quantitative_rule_b=json.dumps(seed_b.get("quantitative_rule"), ensure_ascii=False),
        severity_b=seed_b.get("severity", ""),
        rationale_b=seed_b.get("rationale", ""),
        anti_scope_b=seed_b.get("anti_scope", ""),
    )


def call_opus_critic(seed_a: dict, seed_b: dict, sonnet_result: dict) -> dict:
    prompt = render_opus_critic_prompt(seed_a, seed_b, sonnet_result)
    pair_id = sonnet_result.get("pair_id")
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-opus-4-7",
             "--output-format", "json"],
            capture_output=True, timeout=OPUS_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return {"pair_id": pair_id, "arbitration_error": f"exit {res.returncode}"}
        parsed = parse_claude_cli_result(res.stdout,
                                          expected_keys=["equivalent_final", "rationale"])
        if not parsed:
            return {"pair_id": pair_id, "arbitration_error": "parse_fail"}
        return {
            "pair_id": pair_id,
            "equivalent_final": _coerce_bool(parsed.get("equivalent_final"), default=False),
            "opus_rationale": str(parsed.get("rationale", ""))[:500],
        }
    except subprocess.TimeoutExpired:
        return {"pair_id": pair_id, "arbitration_error": "timeout"}
    except Exception as e:
        return {"pair_id": pair_id, "arbitration_error": str(e)}


def _matrix_record_uids(record: dict) -> tuple[tuple, tuple]:
    """Extract ((master_a, seed_id_a), (master_b, seed_id_b)) tuples from a matrix record.

    Falls back to (None, seed_id) when `masters` is absent (legacy records).
    """
    seed_ids = record.get("seed_ids") or [None, None]
    masters = record.get("masters") or [None, None]
    return (masters[0], seed_ids[0]), (masters[1], seed_ids[1])


def opus_arbitrate_low_conf(matrix: list[dict], all_seeds: list[dict],
                              threshold: float = LOW_CONF_THRESHOLD) -> list[dict]:
    """For every pair with confidence < threshold, run Opus arbitration."""
    # Key by (master, seed_id) so cross-master collisions on bare seed_id don't clobber.
    seeds_by_uid: dict[tuple, dict] = {
        (s.get("_master"), s["seed_id"]): s for s in all_seeds
    }
    low_conf = [p for p in matrix if not p.get("skipped_llm") and p.get("confidence", 0) < threshold]
    print(f"[phase2.L2] Opus arbitration on {len(low_conf)} low-confidence pairs")

    arbitrations = {}
    # Concurrent but gentler — Opus is expensive, use batch of 3
    for batch_idx in range(0, len(low_conf), 3):
        batch = low_conf[batch_idx:batch_idx + 3]

        def _arbitrate(p):
            uid_a, uid_b = _matrix_record_uids(p)
            sa = seeds_by_uid.get(uid_a)
            sb = seeds_by_uid.get(uid_b)
            if sa is None or sb is None:
                return {"pair_id": p.get("pair_id"),
                        "arbitration_error": f"uid_miss a={uid_a} b={uid_b}"}
            return call_opus_critic(sa, sb, p)

        with ThreadPoolExecutor(max_workers=3) as ex:
            batch_results = list(ex.map(_arbitrate, batch))
        for r in batch_results:
            arbitrations[r["pair_id"]] = r
        done = min(batch_idx + 3, len(low_conf))
        print(f"[phase2.L2] progress: {done}/{len(low_conf)}")
        if batch_idx + 3 < len(low_conf):
            time.sleep(10)

    # Merge
    merged = []
    for p in matrix:
        arb = arbitrations.get(p["pair_id"])
        if arb and "equivalent_final" in arb:
            p = dict(p)  # don't mutate original
            p["equivalent"] = arb["equivalent_final"]
            p["confidence"] = 0.95  # Opus arbitration promotes confidence
            p["arbitrated_by_opus"] = True
            p["opus_rationale"] = arb["opus_rationale"]
        elif arb and "arbitration_error" in arb:
            p = dict(p)
            p["arbitration_error"] = arb["arbitration_error"]
            p["low_confidence_flag"] = True
        merged.append(p)
    return merged


# ─────────── Layer 3: Consistency (transitivity) ───────────

def build_equivalence_map(matrix: list[dict]) -> dict[tuple[tuple, tuple], bool]:
    """Build ((master_x, seed_id_x), (master_y, seed_id_y)) → equivalent mapping.

    UID-keyed to survive cross-master seed_id collisions. Both orderings stored.
    """
    m: dict[tuple[tuple, tuple], bool] = {}
    for p in matrix:
        uid_a, uid_b = _matrix_record_uids(p)
        equiv = p.get("equivalent", False)
        m[(uid_a, uid_b)] = equiv
        m[(uid_b, uid_a)] = equiv
    return m


def find_transitivity_violations(matrix: list[dict],
                                   all_seeds: list[dict]) -> list[dict]:
    """Find triples (A, B, C) where A≡B ∧ B≡C but A≢C (or vice versa).

    Triples are keyed by (master, seed_id) tuples so that bare seed_id collisions
    across masters never produce spurious same-triple violations.
    """
    equiv_map = build_equivalence_map(matrix)
    seed_uids = [(s.get("_master"), s["seed_id"]) for s in all_seeds]

    violations = []
    for uid_a, uid_b, uid_c in combinations(seed_uids, 3):
        ab = equiv_map.get((uid_a, uid_b), False)
        bc = equiv_map.get((uid_b, uid_c), False)
        ac = equiv_map.get((uid_a, uid_c), False)
        # Violation: 2 of the 3 are equivalent but third is not (i.e. not all True, not all False, not 1-true)
        count_true = sum([ab, bc, ac])
        if count_true == 2:
            # Two equal, one not — transitivity violated.
            # Report both master-qualified UIDs AND bare seed_ids for human readability.
            violations.append({
                "triple_uids": [list(uid_a), list(uid_b), list(uid_c)],
                "triple": [uid_a[1], uid_b[1], uid_c[1]],
                "ab_equivalent": ab,
                "bc_equivalent": bc,
                "ac_equivalent": ac,
            })
    return violations


def render_consistency_prompt(violations: list[dict], all_seeds: list[dict]) -> str:
    template = (PROMPTS_DIR / "phase2_consistency.md").read_text(encoding="utf-8")
    # Key seeds by (master, seed_id) tuple — bare seed_id is not unique across masters.
    seeds_by_uid: dict[tuple, dict] = {
        (s.get("_master"), s["seed_id"]): s for s in all_seeds
    }
    # Build summary of only seeds involved (violations carry triple_uids when available).
    involved_uids: set = set()
    for v in violations:
        uids = v.get("triple_uids")
        if uids:
            for uid in uids:
                involved_uids.add(tuple(uid))
        else:
            # Legacy records without UIDs — fall back to bare seed_id scan.
            for sid in v.get("triple", []):
                for (m, sid2), seed in seeds_by_uid.items():
                    if sid2 == sid:
                        involved_uids.add((m, sid2))
    seeds_summary = []
    for uid in involved_uids:
        s = seeds_by_uid.get(uid)
        if not s:
            continue
        seeds_summary.append({
            "seed_id": uid[1],
            "master": uid[0],
            "qualitative_claim": s.get("qualitative_claim", ""),
            "rule_subject": s.get("rule_subject", ""),
        })
    return template.format(
        violations_json=json.dumps(violations, ensure_ascii=False, indent=2),
        seeds_summary=json.dumps(seeds_summary, ensure_ascii=False, indent=2),
    )


def consistency_sonnet_review(violations: list[dict],
                                all_seeds: list[dict]) -> list[dict]:
    """Ask Sonnet for suggestions on which pairs to re-run."""
    if not violations:
        return []
    prompt = render_consistency_prompt(violations, all_seeds)
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=SONNET_TIMEOUT, text=True,
        )
        if res.returncode != 0:
            return []
        parsed = parse_claude_cli_result(res.stdout, expected_keys=["suggestions"])
        if parsed and isinstance(parsed.get("suggestions"), list):
            return parsed["suggestions"]
    except Exception:
        pass
    return []


def _parse_uid_token(token: str) -> tuple:
    """Parse a `"<master>/<seed_id>"` token into a (master, seed_id) tuple.

    Accepts legacy bare `seed_id` tokens as `(None, seed_id)` so the caller
    can decide whether to resolve or reject.
    """
    if isinstance(token, str) and "/" in token:
        master, _, seed_id = token.partition("/")
        return master, seed_id
    return None, token


def apply_consistency_fixes(matrix: list[dict], suggestions: list[dict],
                             all_seeds: list[dict]) -> list[dict]:
    """Re-run suggested pairs via Opus for final judgement.

    Suggestions carry `"suspicious_pair": ["<master>/<seed_id>", ...]` per the
    updated phase2_consistency.md prompt. Bare seed_id tokens are rejected
    because they collide across masters.
    """
    if not suggestions:
        return matrix
    seeds_by_uid: dict[tuple, dict] = {
        (s.get("_master"), s["seed_id"]): s for s in all_seeds
    }
    matrix_by_pair = {p["pair_id"]: p for p in matrix}

    for sug in suggestions:
        pair_tokens = sug.get("suspicious_pair", [])
        if len(pair_tokens) != 2:
            continue
        uid_a = _parse_uid_token(pair_tokens[0])
        uid_b = _parse_uid_token(pair_tokens[1])
        if not (uid_a[0] and uid_b[0]):
            # Skip legacy bare-id suggestions to avoid cross-master ambiguity
            continue
        a = seeds_by_uid.get(uid_a)
        b = seeds_by_uid.get(uid_b)
        if not a or not b:
            continue
        # pair_id is globally unique via _pair_id helper; try both orderings.
        pair_id_1 = _pair_id(a, b)
        pair_id_2 = _pair_id(b, a)
        target_p = matrix_by_pair.get(pair_id_1) or matrix_by_pair.get(pair_id_2)
        if not target_p:
            continue
        arb = call_opus_critic(a, b, target_p)
        if arb and "equivalent_final" in arb:
            target_p["equivalent"] = arb["equivalent_final"]
            target_p["confidence"] = 0.95
            target_p["arbitrated_by_opus"] = True
            target_p["consistency_revised"] = True
            target_p["opus_rationale"] = arb.get("opus_rationale", "")
    return matrix


# ─────────── Main orchestration ───────────

def load_sanitized_seeds() -> list[dict]:
    """Load all sanitized seeds from prep/phase1_5_*_sanitized.jsonl."""
    all_seeds = []
    for p in sorted(PREP_DIR.glob("phase1_5_*_sanitized.jsonl")):
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    all_seeds.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return all_seeds


def phase2_comparative(all_seeds: Optional[list[dict]] = None) -> dict:
    """Phase 2 main entry. Returns summary dict; writes prep/phase2_final_matrix.jsonl."""
    if all_seeds is None:
        all_seeds = load_sanitized_seeds()
    if len(all_seeds) < 2:
        print("[phase2] Not enough seeds for pairwise comparison")
        return {"error": "insufficient_seeds", "total_seeds": len(all_seeds)}

    # Layer 1
    layer1_matrix = pairwise_layer1(all_seeds)
    layer1_stats = {
        "total_pairs": len(layer1_matrix),
        "skipped_different_subject": sum(1 for p in layer1_matrix if p.get("skipped_llm")),
        "equivalent_after_l1": sum(1 for p in layer1_matrix if p.get("equivalent")),
        "low_conf_after_l1": sum(1 for p in layer1_matrix
                                  if not p.get("skipped_llm") and p.get("confidence", 0) < LOW_CONF_THRESHOLD),
    }

    # Layer 2
    layer2_matrix = opus_arbitrate_low_conf(layer1_matrix, all_seeds)
    layer2_stats = {
        "arbitrated_count": sum(1 for p in layer2_matrix if p.get("arbitrated_by_opus")),
        "arbitration_errors": sum(1 for p in layer2_matrix if p.get("arbitration_error")),
        "equivalent_after_l2": sum(1 for p in layer2_matrix if p.get("equivalent")),
    }

    # Layer 3
    violations = find_transitivity_violations(layer2_matrix, all_seeds)
    print(f"[phase2.L3] Transitivity violations: {len(violations)}")
    layer3_suggestions = consistency_sonnet_review(violations, all_seeds) if violations else []
    layer3_matrix = apply_consistency_fixes(layer2_matrix, layer3_suggestions, all_seeds)

    layer3_stats = {
        "violations_detected": len(violations),
        "suggestions_from_sonnet": len(layer3_suggestions),
        "pairs_revised": sum(1 for p in layer3_matrix if p.get("consistency_revised")),
    }

    # Write final matrix
    final_path = PREP_DIR / "phase2_final_matrix.jsonl"
    with final_path.open("w", encoding="utf-8") as f:
        for p in layer3_matrix:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Consistency report
    report_path = PREP_DIR / "phase2_consistency_report.md"
    report_lines = [
        "# Phase 2 Consistency Report", "",
        f"Layer 1 stats: {json.dumps(layer1_stats, ensure_ascii=False)}",
        f"Layer 2 stats: {json.dumps(layer2_stats, ensure_ascii=False)}",
        f"Layer 3 stats: {json.dumps(layer3_stats, ensure_ascii=False)}",
        "",
        f"Violations found: {len(violations)}",
    ]
    for v in violations[:20]:
        report_lines.append(f"- Triple {v['triple']}: AB={v['ab_equivalent']} BC={v['bc_equivalent']} AC={v['ac_equivalent']}")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "final_matrix_path": str(final_path),
        "total_seeds": len(all_seeds),
        "layer1_stats": layer1_stats,
        "layer2_stats": layer2_stats,
        "layer3_stats": layer3_stats,
        "final_equivalent_pairs": sum(1 for p in layer3_matrix if p.get("equivalent")),
    }
