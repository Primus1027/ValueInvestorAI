#!/usr/bin/env python3
"""Pre-A: Principles Board Debate — main pipeline.

Orchestrates Phase 1 (seed drafts) → Phase 2 (comparative analysis, Opus)
→ Phase 2.5 (revise round) → Phase 3 (synthesis, via principles_synthesizer)
→ Phase E (compliance scan, via compliance_scan).

Writes intermediate state to prep/ for resumability.

Model assignment (per plan):
  Phase 1 W/C/Y seed drafters:   claude-sonnet-4-6
  Phase 2 neutral researcher:    claude-opus-4-7 ⭐ (strongest, critical step)
  Phase 2.5 revise decisions:    claude-sonnet-4-6
  Phase 3a semantic dedup:       claude-sonnet-4-6
"""

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import robust parser
sys.path.insert(0, str(Path(__file__).parent))
from _json_utils import parse_claude_cli_result

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREP_DIR = PROJECT_ROOT / "prep"
PRINCIPLES_DIR = PROJECT_ROOT / "Principles"

PROFILE_PATHS = {
    "buffett": PROJECT_ROOT / "src/souls/profiles/buffett.json",
    "munger": PROJECT_ROOT / "src/souls/profiles/munger.json",
    "duan": PROJECT_ROOT / "src/souls/profiles/duan.json",
}

SOUL_PATHS = {
    "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.1.md",
    "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.1.md",
    "duan": PROJECT_ROOT / "src/souls/documents/Y-duan-soul-v1.0.md",
}

# Framework anonymization: Phase 2 sees frameworks by letter, not by master.
# Randomized each session to prevent reviewer from learning a stable mapping.
import random
import hashlib


def build_anonymous_mapping() -> Dict[str, str]:
    """Generate a fresh master ↔ framework letter mapping per run."""
    masters = list(PROFILE_PATHS.keys())
    letters = ["A", "B", "C"]
    random.shuffle(letters)
    return dict(zip(masters, letters))


def call_claude(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    expected_keys: Optional[List[str]] = None,
    timeout: int = 360,
) -> Dict[str, Any]:
    """Call claude CLI, return parsed JSON response (or error dict)."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "json"],
            capture_output=True, timeout=timeout, text=True, check=True,
        )
        parsed = parse_claude_cli_result(result.stdout, expected_keys=expected_keys)
        if parsed is None:
            return {
                "error": "JSON parse failed after all fallback strategies",
                "stdout_head": result.stdout[:500],
            }
        return parsed
    except subprocess.CalledProcessError as e:
        return {
            "error": f"subprocess failed: {e}",
            "stderr": (e.stderr or "")[:300],
            "stdout_head": (e.stdout or "")[:300],
        }
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


def call_claude_raw(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    timeout: int = 360,
) -> str:
    """Call claude CLI, return raw response text (not JSON-parsed)."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "json"],
            capture_output=True, timeout=timeout, text=True, check=True,
        )
        outer = json.loads(result.stdout)
        return outer.get("result", "")
    except Exception:
        return ""


# ---------- Shared context loading ----------

def load_profile(master: str) -> str:
    """Load profile.json as JSON string (preserves structure for Agent)."""
    return PROFILE_PATHS[master].read_text(encoding="utf-8")


def load_soul_toc(master: str) -> str:
    """Load the prompt-friendly TOC for this master's soul doc."""
    toc_path = PREP_DIR / f"soul_prompt_toc_{master}.json"
    if not toc_path.exists():
        raise FileNotFoundError(
            f"Run build_soul_index.py first to generate {toc_path}"
        )
    return toc_path.read_text(encoding="utf-8")


def load_full_soul_index() -> Dict:
    """Load the full soul_index.json for @retrieve() resolution."""
    idx_path = PREP_DIR / "soul_index.json"
    return json.loads(idx_path.read_text(encoding="utf-8"))


def resolve_retrieve_placeholders(seeds: List[Dict], full_index: Dict) -> List[Dict]:
    """Replace @retrieve(section_id) placeholders in seeds with actual text.

    Scans seed's `supporting_evidence` field (and similar fields) for the pattern,
    pulls section text from full_index, stores as dict with id + text.

    P0 fix: single-pass replacement only — if retrieved text itself contains
    @retrieve() syntax (e.g., appendix cross-refs), strip those rather than
    recursively resolving, to prevent infinite loops.
    """
    # Build section_id → text map for fast lookup
    sec_map = {}
    for master, doc in full_index["docs"].items():
        for sec in doc["sections"]:
            sec_map[sec["section_id"]] = sec["text"]

    retrieve_re = re.compile(r"@retrieve\(([^)]+)\)")

    def resolve_value(v: Any) -> Any:
        if isinstance(v, str):
            # Track whether we're in first-pass resolution; if so, sanitize
            # nested @retrieve in retrieved content rather than recurse.
            def sub(m):
                sec_id = m.group(1).strip()
                text = sec_map.get(sec_id, f"[SECTION NOT FOUND: {sec_id}]")
                # Neutralize any nested @retrieve() in retrieved text — they
                # become literal `[retrieve:xxx]` markers, not triggers for
                # further replacement
                text = retrieve_re.sub(
                    lambda m2: f"[retrieve:{m2.group(1)}]", text,
                )
                # Truncate to ~500 chars for brevity
                if len(text) > 600:
                    text = text[:600] + "..."
                return f"[{sec_id}]: {text}"
            return retrieve_re.sub(sub, v)
        if isinstance(v, dict):
            return {k: resolve_value(vv) for k, vv in v.items()}
        if isinstance(v, list):
            return [resolve_value(x) for x in v]
        return v

    return [resolve_value(s) for s in seeds]


# ==================== PHASE 1: Seed Drafts ====================

def build_phase1_prompt(master: str, profile_json: str, soul_toc_json: str) -> str:
    """Build the Phase 1 seed draft prompt (strict compliance)."""
    return f"""你是一位价值投资方法论研究助手。本练习的任务：从整理自某位投资大师公开资料的方法论框架中，提炼出可以被 Python if/else 执行的硬约束规则。这是方法论研究练习，不构成投资建议。

=== 被研究的方法论框架 ===
{profile_json}

=== Soul Doc 章节目录（用于引用证据）===
{soul_toc_json}

=== 你的任务 ===
从上述方法论框架中识别出 8-15 条可以被机器执行的硬约束规则。每条规则必须：

1. **是"拒绝某类投资"的规则（negative filter），不是"推荐某类"（positive bias）**
   好例子：「ROE 连续 5 年低于 10% 的公司拒绝投资」
   坏例子：「ROE 高的公司优先考虑」
2. **有量化阈值 OR 可自动化的定性判断**
3. **直接来源于上述框架**（不编造，不扩展）
4. **尽量附上 soul doc 章节锚点** — 从章节目录里选最相关的 section_id，放在 supporting_section_id 字段

=== 每条 seed 的 schema ===
```json
{{
  "seed_id": "seed_01",
  "category": "quantitative_hard | qualitative_required | position_sizing | veto_line | valuation_method",
  "claim": "简短一句话描述这条规则",
  "rationale": "1-3 句说明为什么这条规则在本方法论中成立（引用 profile factor 或 soul doc 段落）",
  "supporting_section_id": "<soul doc 章节目录里的 section_id，如果有>",
  "supporting_profile_factor": "<profile.json 里的 factor id，如果有>",
  "quantitative_rule": {{
    "metric": "指标名（英文标识符）",
    "operator": ">=|<=|==|!=|between",
    "threshold": <数字>,
    "data_field": "company_data.xxx 的字段名"
  }} | null,
  "qualitative_rule": "<定性规则的一句话描述> | null",
  "severity_if_violated": "veto | warning | note"
}}
```

**severity 说明**：
- `veto`: 违反即直接拒绝投资，不进入 LLM 分析
- `warning`: 违反则标记风险，但可继续分析
- `note`: 供参考的细则

**Category 覆盖要求**：至少覆盖 3 个不同 category。建议分布：
- quantitative_hard: 4-6 条（ROE, 盈利持续性, 杠杆, FCF 等）
- qualitative_required: 2-3 条（能力圈, 可解释商业模式等）
- position_sizing: 1-2 条（单只上限, 集中度）
- veto_line: 2-3 条（直接拒绝的硬条件）
- valuation_method: 1-2 条（用什么/不用什么估值方法）

=== 输出要求 ===
只输出一个 JSON 对象，schema 如下：
```json
{{"seeds": [<seed 1>, <seed 2>, ...]}}
```
不要输出其他文字、markdown 围栏等。"""


def phase1_seed_draft_one(master: str) -> Dict:
    """Generate seeds for one master."""
    profile = load_profile(master)
    toc = load_soul_toc(master)
    prompt = build_phase1_prompt(master, profile, toc)
    print(f"  [Phase 1] {master}: calling Sonnet (prompt ~{len(prompt)//4} tokens)...")
    result = call_claude(prompt, model="claude-sonnet-4-6", expected_keys=["seeds"])
    if "error" in result:
        print(f"  [Phase 1] {master}: ERROR — {result['error'][:200]}")
        return {"master": master, "error": result["error"], "seeds": []}
    seeds = result.get("seeds", [])
    # Add master attribution to each seed (not sent to Phase 2 — anonymized there)
    for i, s in enumerate(seeds):
        if "seed_id" not in s:
            s["seed_id"] = f"{master}_{i+1:02d}"
        s["_master"] = master  # private field, stripped before Phase 2
    print(f"  [Phase 1] {master}: got {len(seeds)} seeds")
    return {"master": master, "seeds": seeds}


def phase1_seed_draft_all() -> Dict[str, List]:
    """Run Phase 1 for all 3 masters in parallel."""
    print("\n=== Phase 1: Independent Seed Drafts (3 parallel calls, Sonnet) ===")
    results: Dict[str, List] = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(phase1_seed_draft_one, m): m for m in PROFILE_PATHS.keys()}
        for fut in as_completed(futures):
            m = futures[fut]
            r = fut.result()
            results[m] = r.get("seeds", [])

    # Persist to prep/
    for m, seeds in results.items():
        out = PREP_DIR / f"phase1_{m}_seeds.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for s in seeds:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"  ✓ {out.name}: {len(seeds)} seeds")

    return results


# ==================== PHASE 2: Comparative Analysis (Opus) ====================

def build_phase2_prompt(anonymized_seeds: Dict[str, List]) -> str:
    """Build Phase 2 prompt: neutral researcher with anonymized frameworks."""
    seeds_display = {}
    for letter, seeds in anonymized_seeds.items():
        # Strip private fields before showing to Phase 2
        clean = []
        for s in seeds:
            clean.append({k: v for k, v in s.items() if not k.startswith("_")})
        seeds_display[f"framework_{letter}"] = clean

    seeds_json = json.dumps(seeds_display, ensure_ascii=False, indent=2)

    return f"""你是价值投资方法论对照研究员。你的工作是**中立地对照**三个独立的投资方法论框架（匿名标签 A、B、C）各自提出的 principle seeds。

**重要**：你不是这三个框架的任何一个。你的任务不是评价哪个"对"，而是做结构化对照映射。不要在输出中引用或猜测具体投资大师的名字。

=== 三个框架的 seed principles ===
{seeds_json}

=== 你的任务 ===
对每一条 seed（来自任何框架），判断它与**其他两个框架**的 seeds 之间的关系：

- **supported_by**: 哪些框架有**语义上等价或强相似**的 seed？（引用对方的 seed_id）
- **conflicts_with**: 哪些框架有与本 seed **明确矛盾**的 seed？（引用对方的 seed_id + 冲突类型）
- **framework_specific_aspects**: 本 seed 是否只在这个框架下存在？如果有跨框架变体（如相同原则但不同阈值），标注差异。

**严禁**：
- 在输出中使用 "Buffett / Munger / 段永平 / 大师" 等具体人名
- 对任何框架做价值判断（"framework A 更好"）
- 编造 seed 池中不存在的 principle

=== 输出 schema ===
只输出一个 JSON 对象：
```json
{{
  "stances": [
    {{
      "seed_id": "<来自输入的 seed_id>",
      "framework": "A | B | C",
      "claim_normalized": "<用一句中立语言重述 claim，不带框架特色>",
      "supported_by": ["<其他框架名>"],
      "supporting_seed_ids": ["<对方的 seed_id>"],
      "conflicts_with": ["<其他框架名>"],
      "conflicting_seed_ids": ["<对方的 seed_id>"],
      "framework_specific_aspects": ["<该 seed 的独特之处，如特定阈值、特定应用场景>"],
      "synthesis_note": "<1-2 句中立总结三个框架在这个议题上的对照>"
    }},
    ...
  ]
}}
```

不要输出其他文字。"""


def phase2_comparative_analysis(
    seeds_by_master: Dict[str, List],
    anon_map: Dict[str, str],
    double_run: bool = True,
) -> Dict:
    """Phase 2: neutral researcher (Opus) with anonymized frameworks.

    Double-run: call Opus twice with different random seeds (via prompt suffix)
    and compare consistency.
    """
    print("\n=== Phase 2: Comparative Analysis (Opus, anonymized A/B/C) ===")
    print(f"  anon_map: {anon_map}")

    # Build anonymized seed pool: {letter: [seeds]}
    anonymized = {}
    for master, letter in anon_map.items():
        anonymized[letter] = seeds_by_master.get(master, [])

    prompt_base = build_phase2_prompt(anonymized)
    print(f"  prompt size: ~{len(prompt_base)//4} tokens")

    runs = []
    n_runs = 2 if double_run else 1
    for run_idx in range(n_runs):
        # Slight prompt variation to get fresh samples (forces different random seeds)
        salt = f"\n\n[internal run marker: {run_idx}]" if run_idx > 0 else ""
        prompt = prompt_base + salt
        print(f"  [Phase 2] run {run_idx+1}/{n_runs}: calling Opus...")
        result = call_claude(
            prompt, model="claude-opus-4-7",
            expected_keys=["stances"], timeout=480,
        )
        if "error" in result:
            print(f"  [Phase 2] run {run_idx+1}: ERROR — {result['error'][:200]}")
            runs.append({"error": result["error"], "stances": []})
        else:
            stances = result.get("stances", [])
            print(f"  [Phase 2] run {run_idx+1}: got {len(stances)} stances")
            runs.append({"stances": stances})

    # Merge runs: use run 1 as primary, flag inconsistencies with run 2
    primary = runs[0].get("stances", [])
    secondary = runs[1].get("stances", []) if len(runs) > 1 else []

    # Build seed_id → stance map for comparison
    p_map = {s.get("seed_id"): s for s in primary}
    s_map = {s.get("seed_id"): s for s in secondary}

    merged = []
    inconsistencies = 0
    for seed_id, pstance in p_map.items():
        sstance = s_map.get(seed_id)
        flag = None
        if sstance:
            # Compare supported_by sets
            p_sup = set(pstance.get("supported_by", []))
            s_sup = set(sstance.get("supported_by", []))
            if p_sup != s_sup:
                flag = f"double_run_disagreement: run1 supported_by={sorted(p_sup)}, run2={sorted(s_sup)}"
                inconsistencies += 1
        merged_stance = dict(pstance)
        if flag:
            merged_stance["_double_run_flag"] = flag
        merged.append(merged_stance)

    consistency_rate = 1 - (inconsistencies / max(len(merged), 1))
    print(f"  [Phase 2] consistency rate: {consistency_rate:.0%} "
          f"({len(merged) - inconsistencies}/{len(merged)} stances agree)")

    # Persist
    out = PREP_DIR / "phase2_comparative_analysis.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for st in merged:
            f.write(json.dumps(st, ensure_ascii=False) + "\n")
    print(f"  ✓ {out.name}: {len(merged)} stances")

    # Save anon_map + raw runs for traceability
    (PREP_DIR / "phase2_metadata.json").write_text(json.dumps({
        "anon_map": anon_map,
        "n_runs": n_runs,
        "consistency_rate": consistency_rate,
        "inconsistencies": inconsistencies,
        "raw_runs": runs,
    }, ensure_ascii=False, indent=2))

    return {"stances": merged, "consistency_rate": consistency_rate, "anon_map": anon_map}


# ==================== PHASE 2.5: Revise Round ====================

def build_phase2_5_prompt(
    master: str,
    own_seeds: List[Dict],
    comparative_analysis: List[Dict],
    anon_map: Dict[str, str],
) -> str:
    """Build revise prompt for one master."""
    own_letter = anon_map[master]

    # Extract stances that refer to this master's seeds (as primary) or mention
    # the other frameworks (for context).
    own_seed_ids = {s["seed_id"] for s in own_seeds}
    relevant_stances = [
        st for st in comparative_analysis
        if st.get("seed_id") in own_seed_ids or own_letter in (
            st.get("supported_by", []) + st.get("conflicts_with", [])
        )
    ]

    # De-anonymize for this master's view (show them their own framework as "your framework")
    # but keep others anonymized
    stances_display = []
    for st in relevant_stances:
        disp = dict(st)
        if disp.get("framework") == own_letter:
            disp["framework"] = "YOUR_FRAMEWORK"
        stances_display.append(disp)

    own_seeds_clean = [{k: v for k, v in s.items() if not k.startswith("_")} for s in own_seeds]

    return f"""你是价值投资方法论研究助手。在上一轮（Phase 1）你为所研究的方法论框架提出了以下 seed principles；在 Phase 2 中立研究员对三个框架做了对照分析。现在你有一次修订（revise）的机会。

=== 你之前提出的 seeds (YOUR_FRAMEWORK) ===
{json.dumps(own_seeds_clean, ensure_ascii=False, indent=2)}

=== 中立对照研究员的分析 ===
{json.dumps(stances_display, ensure_ascii=False, indent=2)}

=== 你的任务 ===
基于对照分析，对**你的每一条 seed** 做一个决策：
- **keep**: 保留原 seed 不变
- **modify**: 修改 seed（调整 threshold / 改 claim / 改 rationale / 扩 edge_cases）。给出 modified seed 的完整 JSON。
- **withdraw**: 撤回 seed（如果对照分析指出的问题让这条不再适合作为硬约束）
- **new**: 如果对照过程启发了新想法，可以额外提出 1-3 条新 seed

每个决策**必须附 rationale**。

**严格要求**：
- 不要在输出中用 "Buffett / Munger / 段永平 / 大师" 等具体人名
- 修改后的 seeds 仍符合 Phase 1 的 schema
- keep 也要给 rationale（一句话）

=== 输出 schema ===
```json
{{
  "revisions": [
    {{
      "seed_id": "<原 seed_id>",
      "action": "keep | modify | withdraw",
      "rationale": "<为什么这样决策，1-2 句>",
      "modified_seed": {{<完整 seed>}} | null
    }}
  ],
  "new_seeds": [<完整 seed 结构>, ...] | []
}}
```

不要输出其他文字。"""


def phase2_5_revise_one(
    master: str,
    own_seeds: List[Dict],
    comparative_analysis: List[Dict],
    anon_map: Dict[str, str],
) -> Dict:
    """Revise round for one master."""
    prompt = build_phase2_5_prompt(master, own_seeds, comparative_analysis, anon_map)
    print(f"  [Phase 2.5] {master}: calling Sonnet (prompt ~{len(prompt)//4} tokens)...")
    # Phase 2.5 uses longer timeout; revise calls can be slow for larger seed sets
    result = call_claude(prompt, model="claude-sonnet-4-6",
                         expected_keys=["revisions", "new_seeds"], timeout=540)
    if "error" in result:
        print(f"  [Phase 2.5] {master}: ERROR — {result['error'][:200]}")
        print(f"  [Phase 2.5] {master}: FALLBACK — keeping all original seeds")
        # Fallback: keep all original seeds verbatim rather than withdrawing them.
        # Losing all of a master's voice in synthesis is worse than skipping revise.
        fallback_revisions = [
            {"seed_id": s["seed_id"], "action": "keep",
             "rationale": "Phase 2.5 call failed; preserved original seed as fallback."}
            for s in own_seeds
        ]
        return {"master": master, "revisions": fallback_revisions, "new_seeds": [],
                "error": result["error"], "_fallback_used": True}
    revisions = result.get("revisions", [])
    new_seeds = result.get("new_seeds", []) or []
    print(f"  [Phase 2.5] {master}: {len(revisions)} revisions, {len(new_seeds)} new seeds")
    return {"master": master, "revisions": revisions, "new_seeds": new_seeds}


def phase2_5_revise_all(
    seeds_by_master: Dict[str, List],
    comparative_analysis: List[Dict],
    anon_map: Dict[str, str],
) -> Dict[str, List]:
    """Run Phase 2.5 for all 3 masters in parallel. Returns revised seed sets."""
    print("\n=== Phase 2.5: Revise Round (3 parallel, Sonnet) ===")
    results: Dict[str, Dict] = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(phase2_5_revise_one, m, seeds_by_master[m],
                      comparative_analysis, anon_map): m
            for m in seeds_by_master
        }
        for fut in as_completed(futures):
            m = futures[fut]
            results[m] = fut.result()

    # Apply revisions to produce final revised seed set per master
    revised: Dict[str, List] = {}
    for master, r in results.items():
        original = seeds_by_master[master]
        orig_map = {s["seed_id"]: s for s in original}
        final: List[Dict] = []

        for rev in r.get("revisions", []):
            sid = rev.get("seed_id")
            action = rev.get("action", "keep")
            orig = orig_map.get(sid)
            if not orig:
                continue
            if action == "keep":
                kept = dict(orig)
                kept["_revise_action"] = "keep"
                kept["_revise_rationale"] = rev.get("rationale", "")
                final.append(kept)
            elif action == "modify":
                mod = rev.get("modified_seed")
                if mod:
                    mod["_revise_action"] = "modify"
                    mod["_revise_rationale"] = rev.get("rationale", "")
                    mod["_master"] = master
                    if "seed_id" not in mod:
                        mod["seed_id"] = sid
                    final.append(mod)
            elif action == "withdraw":
                # Not included in final
                pass

        for i, new in enumerate(r.get("new_seeds", [])):
            new["_revise_action"] = "new"
            new["_master"] = master
            if "seed_id" not in new:
                new["seed_id"] = f"{master}_new_{i+1:02d}"
            final.append(new)

        revised[master] = final

        # Persist revision log
        log_path = PREP_DIR / f"phase2_5_{master}_revisions.json"
        log_path.write_text(json.dumps(r, ensure_ascii=False, indent=2))

        # Persist final revised seed set
        out = PREP_DIR / f"phase2_5_{master}_revised_seeds.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for s in final:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        n_keep = sum(1 for s in final if s.get("_revise_action") == "keep")
        n_mod = sum(1 for s in final if s.get("_revise_action") == "modify")
        n_new = sum(1 for s in final if s.get("_revise_action") == "new")
        n_withdrawn = len(original) - n_keep - n_mod
        print(f"  {master}: keep={n_keep} modified={n_mod} new={n_new} "
              f"withdrawn={n_withdrawn} → total={len(final)}")

    return revised


# ==================== MAIN ====================

def save_state(phase_name: str, data: Any):
    """Save phase state for resumability."""
    state_file = PREP_DIR / "phase_state.json"
    state = {}
    if state_file.exists():
        state = json.loads(state_file.read_text())
    state[phase_name] = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "summary": data if isinstance(data, (int, str, bool)) else "(see phase files)",
    }
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def load_phase_output(phase: str, master: Optional[str] = None) -> Any:
    """Load previously-saved phase output for resume."""
    if phase == "phase1":
        if master:
            path = PREP_DIR / f"phase1_{master}_seeds.jsonl"
            return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        return {m: load_phase_output("phase1", m) for m in PROFILE_PATHS.keys()}
    if phase == "phase2":
        path = PREP_DIR / "phase2_comparative_analysis.jsonl"
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if phase == "phase2_5":
        return {m: [json.loads(l) for l in
                    (PREP_DIR / f"phase2_5_{m}_revised_seeds.jsonl")
                    .read_text().splitlines() if l.strip()]
                for m in PROFILE_PATHS.keys()}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-from", choices=["phase1", "phase2", "phase2_5", "phase3"],
                        help="Skip earlier phases and load their outputs from prep/")
    parser.add_argument("--no-double-run", action="store_true",
                        help="Run Phase 2 only once (saves time for debugging)")
    parser.add_argument("--anon-seed", type=int, default=None,
                        help="Fixed seed for anonymization mapping (reproducibility)")
    args = parser.parse_args()

    PREP_DIR.mkdir(parents=True, exist_ok=True)
    PRINCIPLES_DIR.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now(timezone.utc)
    print(f"=== Pre-A: Principles Board Debate ===")
    print(f"Started: {start_time.isoformat()}")

    # Check that Phase 0 ran
    if not (PREP_DIR / "soul_prompt_toc_buffett.json").exists():
        print("✗ prep/soul_prompt_toc_*.json missing. Run build_soul_index.py first.")
        sys.exit(1)

    # ----- Phase 1 -----
    if args.resume_from in ("phase2", "phase2_5", "phase3"):
        print("\n[Resume] Loading Phase 1 from disk...")
        seeds_by_master = load_phase_output("phase1")
        for m, s in seeds_by_master.items():
            print(f"  {m}: {len(s)} seeds loaded")
    else:
        seeds_by_master = phase1_seed_draft_all()
        save_state("phase1", sum(len(s) for s in seeds_by_master.values()))

    # Sanity: need at least some seeds per master
    for m, seeds in seeds_by_master.items():
        if len(seeds) < 3:
            print(f"✗ Phase 1: {m} produced only {len(seeds)} seeds. "
                  f"Too few to proceed. Check prep/phase1_{m}_seeds.jsonl")
            sys.exit(1)

    # ----- Phase 2 -----
    if args.resume_from in ("phase2_5", "phase3"):
        print("\n[Resume] Loading Phase 2 from disk...")
        comparative_analysis = load_phase_output("phase2")
        meta = json.loads((PREP_DIR / "phase2_metadata.json").read_text())
        anon_map = meta["anon_map"]
        print(f"  {len(comparative_analysis)} stances loaded; anon_map={anon_map}")
    else:
        if args.anon_seed is not None:
            random.seed(args.anon_seed)
        anon_map = build_anonymous_mapping()
        phase2_result = phase2_comparative_analysis(
            seeds_by_master, anon_map, double_run=not args.no_double_run,
        )
        comparative_analysis = phase2_result["stances"]
        save_state("phase2", len(comparative_analysis))

    # ----- Phase 2.5 -----
    if args.resume_from == "phase3":
        print("\n[Resume] Loading Phase 2.5 revised seeds from disk...")
        revised_seeds_by_master = load_phase_output("phase2_5")
        for m, s in revised_seeds_by_master.items():
            print(f"  {m}: {len(s)} revised seeds")
    else:
        revised_seeds_by_master = phase2_5_revise_all(
            seeds_by_master, comparative_analysis, anon_map,
        )
        save_state("phase2_5", sum(len(s) for s in revised_seeds_by_master.values()))

    # ----- Phase 3 delegated to principles_synthesizer.py -----
    print("\n=== Phase 3 delegated to principles_synthesizer.py ===")
    synth_result = subprocess.run(
        ["python3", str(PROJECT_ROOT / "scripts/soul/principles_synthesizer.py")],
        capture_output=True, text=True,
    )
    print(synth_result.stdout)
    if synth_result.returncode != 0:
        print(f"✗ Synthesizer failed: {synth_result.stderr[:500]}")
        sys.exit(1)

    # ----- Phase E compliance scan -----
    print("\n=== Phase E: Compliance Scan ===")
    scan_result = subprocess.run(
        ["python3", str(PROJECT_ROOT / "scripts/soul/compliance_scan.py")],
        capture_output=True, text=True,
    )
    print(scan_result.stdout)
    if scan_result.returncode != 0:
        print(f"⚠ Compliance scan reported violations — see output above.")

    end_time = datetime.now(timezone.utc)
    duration_min = (end_time - start_time).total_seconds() / 60
    print(f"\n=== Pre-A Complete ({duration_min:.1f} min) ===")
    print(f"\n审批 checkpoint:")
    print(f"  请 review: Principles/v1.0.md")
    print(f"  请 review: Principles/debate_log_2026-04-20.md")
    print(f"  Phase 2 匿名映射: {anon_map}")
    print(f"\n确认无误后，执行:")
    print(f"  ln -sf v1.0.md Principles/current.md")
    print(f"以将 v1.0 升级为 Layer 0 生效版本。")


if __name__ == "__main__":
    main()
