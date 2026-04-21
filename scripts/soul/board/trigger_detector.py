"""Phase -1: Trigger Detection.

Checks 4 trigger conditions in priority order (T2 > T3 > T4 > T1). Returns
the trigger event to fire, or None if nothing triggered.

No LLM calls. Python only — runs in < 1s.

CLI:
  python3 -m scripts.soul.board.trigger_detector --check
  python3 -m scripts.soul.board.trigger_detector --force T2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from scripts.soul.board import PROJECT_ROOT, PREP_DIR, HISTORY_DIR, PRINCIPLES_DIR
from scripts.soul.board.agenda_tracker import AgendaTracker
from scripts.soul.board.archive import list_past_debate_ids

SOUL_DOC_PATHS = {
    "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.1.md",
    "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.1.md",
    "duan": PROJECT_ROOT / "src/souls/documents/Y-duan-soul-v1.0.md",
}

LAST_DEBATE_STATE_PATH = PREP_DIR / "last_debate_state.json"
TRIGGER_LOG_PATH = PREP_DIR / "trigger_log.jsonl"
MONITORING_PATH = PRINCIPLES_DIR / "monitoring.md"

# T3 phase settings (set via _t3_config.json or default to 'early')
T3_CONFIG_PATH = PREP_DIR / "_t3_config.json"
T3_PHASE_EARLY = "early"
T3_PHASE_MID = "mid"
T3_PHASE_MATURE = "mature"

# T4 threshold
AGENDA_OVERFLOW_THRESHOLD = 10
MIN_DAYS_BETWEEN_SAME_TRIGGER = 30


# ─────────── Soul doc version detection ───────────

def file_content_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_soul_doc_version(path: Path) -> str:
    """Read first 2000 bytes to find a version string like 'v1.1' or 'v2.0'."""
    if not path.exists():
        return "missing"
    head = path.read_text(encoding="utf-8", errors="replace")[:2000]
    import re
    # Look for v{major}.{minor} pattern
    m = re.search(r"[Vv]ersion\s*[:=]?\s*(v?\d+\.\d+(?:\.\d+)?)", head)
    if m:
        return m.group(1).lstrip("Vv")
    m2 = re.search(r"(?:^|\s)(v\d+\.\d+)\b", head)
    if m2:
        return m2.group(1).lstrip("v")
    return "unknown"


def current_soul_doc_states() -> dict:
    """Snapshot of every soul doc's version + content hash."""
    out = {}
    for master, path in SOUL_DOC_PATHS.items():
        out[master] = {
            "version": extract_soul_doc_version(path),
            "hash": file_content_hash(path)[:16],  # short hash for readability
            "path": str(path),
        }
    return out


# ─────────── Trigger checks ───────────

def check_t2_soul_doc_update() -> tuple[bool, str, dict]:
    """T2: soul doc semver minor+ bump or content hash change since last debate."""
    current_states = current_soul_doc_states()

    if not LAST_DEBATE_STATE_PATH.exists():
        # First run — treat as T2 trigger
        return True, "no_prior_state_treat_as_t2", current_states

    try:
        last_state = json.loads(LAST_DEBATE_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return True, "corrupt_prior_state_treat_as_t2", current_states

    last_versions = last_state.get("soul_doc_states", {})
    for master, cur in current_states.items():
        last = last_versions.get(master, {})
        if cur["hash"] != last.get("hash"):
            # Check if minor+ version bump (vs just content edit)
            cur_v = cur["version"]
            last_v = last.get("version", "")
            is_minor_bump = _is_minor_plus_bump(last_v, cur_v)
            return True, f"{master}_hash_change (minor_bump={is_minor_bump})", current_states
    return False, "no_soul_doc_change", current_states


def _is_minor_plus_bump(last_v: str, cur_v: str) -> bool:
    """True if cur_v is >= +0.1 of last_v (minor+ bump)."""
    def parse(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except Exception:
            return (0, 0)
    if not last_v or not cur_v:
        return False
    lt, ct = parse(last_v), parse(cur_v)
    # Check major bump or minor bump
    if ct[:1] > lt[:1]:  # major bump
        return True
    if ct[:1] == lt[:1] and len(ct) >= 2 and len(lt) >= 2 and ct[1] > lt[1]:
        return True
    return False


def check_t1_quarterly() -> tuple[bool, str]:
    """T1: >= 90 days since last T1 quarterly review."""
    past_debates = list_past_debate_ids()
    # Find last T1 trigger debate
    last_t1_date = None
    for debate_id in reversed(past_debates):
        # debate_id format: 'YYYY-MM-DD_trigger_type_...'
        parts = debate_id.split("_", 1)
        if len(parts) < 2:
            continue
        trigger_type = parts[1]
        if trigger_type.startswith("T1_") or trigger_type == "T1":
            try:
                last_t1_date = datetime.fromisoformat(parts[0])
                break
            except ValueError:
                continue

    if last_t1_date is None:
        return True, "no_prior_t1"
    now = datetime.now()
    days_since = (now - last_t1_date).days
    if days_since >= 90:
        return True, f"{days_since}_days_since_last_t1"
    return False, f"only_{days_since}_days_since_last_t1"


def check_t3_field_signal() -> tuple[bool, str, dict]:
    """T3: per-cluster request_override accumulation. Phase-gated."""
    # Load T3 phase config
    phase = T3_PHASE_EARLY
    if T3_CONFIG_PATH.exists():
        try:
            cfg = json.loads(T3_CONFIG_PATH.read_text(encoding="utf-8"))
            phase = cfg.get("phase", T3_PHASE_EARLY)
        except Exception:
            pass

    if phase == T3_PHASE_EARLY:
        return False, "t3_disabled_mvp_early", {}
    if phase == T3_PHASE_MID:
        # Only log to monitoring.md, never trigger debate
        _write_monitoring_entry("t3_mid_phase_check", "Monitoring-only, no debate triggered")
        return False, "t3_monitoring_only_mvp_mid", {}
    # MATURE phase — need a decisions.jsonl to analyze
    decisions_path = Path.home() / ".valueinvestor" / "decisions.jsonl"
    if not decisions_path.exists():
        return False, "no_decisions_log_yet", {}

    # Count request_override per cluster_id in last 30 days
    contested = {}
    cutoff = datetime.now() - timedelta(days=30)
    with decisions_path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = rec.get("timestamp", "")
            try:
                ts_dt = datetime.fromisoformat(ts)
            except Exception:
                continue
            if ts_dt < cutoff:
                continue
            if rec.get("action") != "request_override":
                continue
            cid = rec.get("cluster_id")
            ticker = rec.get("ticker", "?")
            contested.setdefault(cid, set()).add(ticker)

    # Trigger if any cluster has >= 3 distinct tickers requesting override
    contested_rules = [cid for cid, tickers in contested.items() if len(tickers) >= 3]
    if contested_rules:
        return True, f"contested_rules={contested_rules}", {"contested_rules": contested_rules}
    return False, "no_contested_rules_above_threshold", {"contested": {k: list(v) for k, v in contested.items()}}


def check_t4_agenda_overflow() -> tuple[bool, str]:
    """T4: agenda active items >= 10 AND >= 30 days since last T1/T4."""
    agenda = AgendaTracker()
    active_count = agenda.active_count()
    if active_count < AGENDA_OVERFLOW_THRESHOLD:
        return False, f"active_agenda_items={active_count}_below_threshold"

    past = list_past_debate_ids()
    last_t1_or_t4 = None
    for debate_id in reversed(past):
        parts = debate_id.split("_", 1)
        if len(parts) < 2:
            continue
        t = parts[1]
        if t.startswith("T1") or t.startswith("T4"):
            try:
                last_t1_or_t4 = datetime.fromisoformat(parts[0])
                break
            except ValueError:
                continue

    if last_t1_or_t4 is not None:
        days = (datetime.now() - last_t1_or_t4).days
        if days < MIN_DAYS_BETWEEN_SAME_TRIGGER:
            return False, f"t1_or_t4_too_recent ({days} days)"

    return True, f"active_agenda={active_count}_overflow_triggered"


def _write_monitoring_entry(event_type: str, message: str) -> None:
    """Append to Principles/monitoring.md (T3 告警)."""
    PRINCIPLES_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    line = f"- **{now}** [{event_type}] {message}\n"
    if MONITORING_PATH.exists():
        existing = MONITORING_PATH.read_text(encoding="utf-8")
        if "# Monitoring Log" not in existing:
            existing = "# Monitoring Log\n\n" + existing
    else:
        existing = "# Monitoring Log\n\n"
    MONITORING_PATH.write_text(existing + line, encoding="utf-8")


# ─────────── Decision ───────────

def decide_trigger() -> Optional[dict]:
    """Check all triggers in priority order. Return the one to fire, or None."""
    # T2 (highest)
    t2_fire, t2_reason, soul_states = check_t2_soul_doc_update()
    if t2_fire:
        return build_event("T2_soul_doc_update", "full", None, t2_reason, soul_states)

    # T3
    t3_fire, t3_reason, t3_meta = check_t3_field_signal()
    if t3_fire:
        contested = t3_meta.get("contested_rules", [])
        return build_event("T3_field_signal", "mini", contested, t3_reason, soul_states)

    # T4
    t4_fire, t4_reason = check_t4_agenda_overflow()
    if t4_fire:
        return build_event("T4_agenda_overflow", "mini", None, t4_reason, soul_states)

    # T1
    t1_fire, t1_reason = check_t1_quarterly()
    if t1_fire:
        return build_event("T1_quarterly", "mini", None, t1_reason, soul_states)

    return None


def build_event(trigger_type: str, debate_mode: str,
                 scope: Optional[list], reason: str,
                 soul_states: dict) -> dict:
    now_iso = datetime.now().isoformat(timespec="seconds")
    date_only = now_iso[:10]
    # Strip underscores from trigger_type to avoid confusing debate_id separator
    safe_trigger = trigger_type.replace(".", "_")
    debate_id = f"{date_only}_{safe_trigger}"
    event = {
        "timestamp": now_iso,
        "trigger_type": trigger_type,
        "debate_mode": debate_mode,
        "debate_id": debate_id,
        "scope": scope,
        "reason": reason,
        "skipped": False,
        "soul_doc_versions_at_trigger": soul_states,
    }
    return event


def log_trigger_event(event: dict) -> None:
    """Append to prep/trigger_log.jsonl."""
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    with TRIGGER_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def update_last_debate_state(event: dict, soul_states: dict) -> None:
    """Record the current state as "last debate" for future T2 checks."""
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "last_debate_id": event["debate_id"],
        "last_debate_timestamp": event["timestamp"],
        "trigger_type": event["trigger_type"],
        "soul_doc_states": soul_states,
    }
    LAST_DEBATE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                                        encoding="utf-8")


# ─────────── CLI ───────────

def main():
    ap = argparse.ArgumentParser(description="Phase -1 trigger detector")
    ap.add_argument("--check", action="store_true",
                     help="Check triggers without executing; print decision")
    ap.add_argument("--force", choices=["T1", "T2", "T3", "T4", "manual"],
                     help="Force a specific trigger type (for testing/manual runs)")
    ap.add_argument("--mode", choices=["full", "mini"], default=None,
                     help="Override debate mode (only used with --force)")
    ap.add_argument("--json-output", action="store_true")
    args = ap.parse_args()

    if args.force:
        soul_states = current_soul_doc_states()
        trigger_map = {
            "T1": "T1_quarterly",
            "T2": "T2_soul_doc_update",
            "T3": "T3_field_signal",
            "T4": "T4_agenda_overflow",
            "manual": "manual",
        }
        mode_default = "full" if args.force in ("T2", "manual") else "mini"
        event = build_event(
            trigger_map[args.force],
            args.mode or mode_default,
            None,
            f"forced_by_cli",
            soul_states,
        )
        if args.json_output:
            print(json.dumps(event, ensure_ascii=False, indent=2))
        else:
            print(f"Forced trigger: {event['trigger_type']}")
            print(f"  debate_id: {event['debate_id']}")
            print(f"  mode: {event['debate_mode']}")
        sys.exit(0)

    event = decide_trigger()
    if event is None:
        msg = {"triggered": False, "reason": "no_conditions_met"}
        if args.json_output:
            print(json.dumps(msg))
        else:
            print("No trigger fired.")
        sys.exit(0)

    if args.check:
        if args.json_output:
            print(json.dumps(event, ensure_ascii=False, indent=2))
        else:
            print(f"Would trigger: {event['trigger_type']}")
            print(f"  debate_id: {event['debate_id']}")
            print(f"  mode: {event['debate_mode']}")
            print(f"  reason: {event['reason']}")
    else:
        log_trigger_event(event)
        if args.json_output:
            print(json.dumps(event, ensure_ascii=False, indent=2))
        else:
            print(f"Fired: {event['trigger_type']} (debate_id={event['debate_id']})")


if __name__ == "__main__":
    main()
