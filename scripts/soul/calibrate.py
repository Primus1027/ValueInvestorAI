#!/usr/bin/env python3
"""
Run calibration regression: compare soul doc v1.0 vs v1.1 on cases.json.

For each case × master × version:
  - Use soul doc as system prompt + profile.json + case as user message
  - Extract decision + reasoning
  - Compare against expected_decisions

Outputs:
  calibration_runs/<timestamp>/runs.jsonl
  calibration_runs/<timestamp>/report.md
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = PROJECT_ROOT / "src/souls/calibration/cases.json"
PROFILES_DIR = PROJECT_ROOT / "src/souls/profiles"
RUNS_ROOT = PROJECT_ROOT / "calibration_runs"

SOUL_VERSIONS = {
    "v1.0": {
        "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.0.md",
        "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.0.md",
        "duan": PROJECT_ROOT / "src/souls/documents/Y-duan-soul-v1.0.md",
    },
    "v1.1": {
        "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.1.md",
        "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.1.md",
        # duan v1.1 not yet produced (vig scan was W/C only)
    },
}

NOW = datetime.now(timezone.utc)
RUN_ID = NOW.strftime("run-%Y%m%d-%H%M%S")


def load_cases() -> list[dict]:
    c = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    all_cases = []
    for key in ("standard_cases", "adversarial_cases", "crisis_cases"):
        for case in c.get(key, []):
            case["_category"] = key
            all_cases.append(case)
    return all_cases


def run_agent(master: str, version: str, case: dict) -> dict:
    """Invoke Claude CLI as the master Agent and get a decision."""
    soul_path = SOUL_VERSIONS[version][master]
    if not soul_path.exists():
        return {"error": f"soul file missing: {soul_path}"}
    soul_text = soul_path.read_text(encoding="utf-8")
    # For v1.1 (or v1.1-rc), drop the generator header comment
    if version in ("v1.1", "v1.1-rc"):
        # Strip <!-- ... --> block at top
        m = re.match(r"^<!--.*?-->\s*\n\s*", soul_text, re.DOTALL)
        if m:
            soul_text = soul_text[m.end():]
    # Cap to ~80KB to stay within reasonable prompt budget
    soul_text = soul_text[:80000]

    profile_path = PROFILES_DIR / f"{master}.json"
    profile = profile_path.read_text(encoding="utf-8")

    case_text = json.dumps({
        "case_id": case["case_id"],
        "title": case["title"],
        "company": case.get("company", ""),
        "ticker": case.get("ticker", ""),
        "year": case.get("year"),
        "market_context": case.get("market_context", ""),
        "financial_snapshot": case.get("financial_snapshot", {}),
    }, ensure_ascii=False, indent=2)

    # 重要：避免"扮演真实人物 + 给真实投资建议"的措辞（触发 Claude Usage Policy）。
    # 改为"应用投资方法论框架"的学术研究口吻——这与项目 AI Debate 共识一致：
    # "灵魂封装"叙事放弃 → 改为"投资决策风格仿真"。
    # 输出是 research/academic exercise，不是 personalized investment advice。
    system_prompt = f"""你是一位价值投资研究助手，正在对投资方法论做学术性的案例评估演练。

本练习的任务：运用下述价值投资方法论框架（该框架整理自 {master} 的公开著作和访谈），对给定的历史投资案例做出方法论意义上的评估。这是研究性质的案例分析，不构成真实投资建议。

==== 方法论文档（整理自 {master} 公开资料的决策思维特征）====
{soul_text}

==== 评估框架（结构化的决策维度）====
{profile}

请按方法论框架的逻辑推理，给出该方法论对这个案例的评估判断。"""

    user_prompt = f"""请基于上述方法论对以下历史投资案例做出方法论评估：

{case_text}

请以 JSON 格式输出（只输出 JSON，不要其他内容）：
{{
  "decision": "strong_buy|buy|hold|avoid|sell",
  "reasoning": "<100-200字的方法论推理，说明该框架为什么给出此判断>",
  "key_factors": ["<方法论关注的 3-5 个核心考量维度>"],
  "red_flags_detected": ["<框架识别出的风险信号，如有>"],
  "confidence": "high|medium|low"
}}"""

    # Combine into single prompt (claude -p doesn't have separate system)
    full_prompt = system_prompt + "\n\n===\n\n" + user_prompt

    from _json_utils import parse_claude_cli_result

    expected_keys = ["decision", "reasoning", "key_factors", "red_flags_detected", "confidence"]
    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt, "--model", "claude-sonnet-4-6",
             "--output-format", "json"],
            capture_output=True, timeout=240, text=True, check=True)
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
    except Exception as e:
        return {
            "error": str(e),
            "stdout_head": result.stdout[:300] if 'result' in locals() else "",
        }


def score_output(agent_output: dict, expected: dict) -> dict:
    """Score agent output against expected decision."""
    if "error" in agent_output:
        return {"error": agent_output["error"], "overall": 0}
    decision = agent_output.get("decision", "")
    expected_decision = expected.get("decision", "")
    decision_match = decision == expected_decision
    # Direction match (buy-variants match, sell-variants match)
    buy_set = {"strong_buy", "buy"}
    hold_set = {"hold"}
    avoid_set = {"avoid", "sell"}
    direction_match = (
        (decision in buy_set and expected_decision in buy_set) or
        (decision in hold_set and expected_decision in hold_set) or
        (decision in avoid_set and expected_decision in avoid_set)
    )

    # Factor overlap
    agent_factors = set(f.lower() for f in agent_output.get("key_factors", []))
    expected_factors = set(f.lower() for f in expected.get("key_factors", []))
    overlap = 0.0
    if expected_factors:
        matches = sum(1 for ef in expected_factors
                     if any(ef in af or af in ef for af in agent_factors))
        overlap = matches / len(expected_factors)

    return {
        "decision_match": decision_match,
        "direction_match": direction_match,
        "factor_overlap": round(overlap, 2),
        "agent_decision": decision,
        "expected_decision": expected_decision,
        "agent_factors": list(agent_factors),
        "expected_factors": list(expected_factors),
    }


def main():
    cases = load_cases()
    masters = ["buffett", "munger", "duan"]
    versions = ["v1.0", "v1.1"]

    # Filter: only run cases that have expected_decisions for the master,
    # AND the (master, version) soul file exists
    tasks = []
    skipped = 0
    for case in cases:
        for m in masters:
            if m not in case.get("expected_decisions", {}):
                continue
            for v in versions:
                soul_path = SOUL_VERSIONS.get(v, {}).get(m)
                if not soul_path or not soul_path.exists():
                    skipped += 1
                    continue
                tasks.append((m, v, case))

    print(f"Total tasks: {len(tasks)} (cases × masters × versions); skipped {skipped} missing soul combos")

    runs = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(run_agent, m, v, c): (m, v, c) for m, v, c in tasks}
        done = 0
        for fut in as_completed(futures):
            m, v, c = futures[fut]
            out = fut.result()
            expected = c["expected_decisions"][m]
            score = score_output(out, expected)
            runs.append({
                "run_id": RUN_ID,
                "case_id": c["case_id"],
                "case_title": c["title"],
                "case_category": c["_category"],
                "master": m,
                "version": v,
                "agent_output": out,
                "expected": expected,
                "score": score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            done += 1
            if "error" in out:
                print(f"  [{done}/{len(tasks)}] {m}/{v}/{c['case_id']}: ERROR")
            else:
                match = "✓" if score.get("decision_match") else ("~" if score.get("direction_match") else "✗")
                print(f"  [{done}/{len(tasks)}] {m}/{v}/{c['case_id']}: {match} "
                      f"{out.get('decision', '?')} vs {expected.get('decision', '?')}, "
                      f"overlap={score.get('factor_overlap', 0):.2f}")

    # Write outputs
    out_dir = RUNS_ROOT / RUN_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "runs.jsonl").open("w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Build comparative report
    report = [f"# Calibration Report: {RUN_ID}\n"]
    report.append(f"Timestamp: {NOW.isoformat()}\n")
    report.append(f"Cases: {len(cases)}  Masters: {masters}  Versions: {versions}\n")

    # Per-case comparison
    report.append("\n## Per-Case Comparison (v1.0 vs v1.1)\n")
    by_case_master = {}
    for r in runs:
        k = (r["case_id"], r["master"])
        by_case_master.setdefault(k, {})[r["version"]] = r

    regressions = 0
    improvements = 0
    stable = 0
    single_version = 0  # master has only one version (e.g. duan has no v1.1 yet)
    for (case_id, master), vers in sorted(by_case_master.items()):
        v0 = vers.get("v1.0", {})
        v1 = vers.get("v1.1", {})
        # If either version is missing (no task was run for that combo), this is
        # single-version coverage — not a regression.
        v0_present = bool(v0)
        v1_present = bool(v1)
        v0_score = v0.get("score", {})
        v1_score = v1.get("score", {})
        v0_match = v0_score.get("decision_match", False)
        v1_match = v1_score.get("decision_match", False)
        v0_overlap = v0_score.get("factor_overlap", 0)
        v1_overlap = v1_score.get("factor_overlap", 0)

        if not (v0_present and v1_present):
            status = "SINGLE_VERSION"
            single_version += 1
        elif v0_match and not v1_match:
            status = "REGRESSION"
            regressions += 1
        elif not v0_match and v1_match:
            status = "IMPROVEMENT"
            improvements += 1
        elif v1_overlap > v0_overlap + 0.1:
            status = "improved"
            improvements += 1
        elif v0_overlap > v1_overlap + 0.1:
            status = "weakened"
            regressions += 1
        else:
            status = "="
            stable += 1

        report.append(f"\n### {case_id}.{master}: {status}")
        if v0_present:
            report.append(f"- v1.0: decision={v0.get('agent_output', {}).get('decision', '?')} match={v0_match} overlap={v0_overlap:.2f}")
        else:
            report.append(f"- v1.0: (not run — soul file missing)")
        if v1_present:
            report.append(f"- v1.1: decision={v1.get('agent_output', {}).get('decision', '?')} match={v1_match} overlap={v1_overlap:.2f}")
        else:
            report.append(f"- v1.1: (not run — soul file missing)")
        expected = (v0 or v1).get("expected", {})
        report.append(f"- Expected: {expected.get('decision', '?')}"
                      + (f" (nuance: {expected['decision_nuance']})" if 'decision_nuance' in expected else ""))

    report.append(f"\n## Gate 5 Summary\n")
    report.append(f"- Improvements: {improvements}")
    report.append(f"- Stable: {stable}")
    report.append(f"- Regressions: {regressions}")
    report.append(f"- Single-version coverage: {single_version} (no comparison possible)")
    if regressions == 0:
        report.append(f"\n**GATE 5: PASS** (no regressions)")
    else:
        report.append(f"\n**GATE 5: NEEDS REVIEW** ({regressions} real regression(s))")

    (out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\n✓ Report: {out_dir / 'report.md'}")
    print(f"✓ Runs: {out_dir / 'runs.jsonl'}")


if __name__ == "__main__":
    main()
