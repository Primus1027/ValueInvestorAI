#!/usr/bin/env python3
"""Orchestrator v2 — main pipeline for Principles Board Debate v0.4.1.

Pipeline:
  Phase -1 (trigger_detector) — determines if/what to run
  Phase 0   (context_prep)
  Phase 1   (seed_draft)
  Phase 1.5 (sanitize)
  Phase 2   (comparative, 3-layer)
  Phase 2.5 (revise)
  Phase 2.75 (cross_rebuttal)
  Phase 3a  (cluster)
  Phase 3b-qual (vote_qualitative)
  Phase 3b-quant (vote_quantitative)
  Phase 3b-sev (vote_severity, pure Python)
  Phase 3c  (render + circuit breaker)
  Phase E   (compliance scan)
  Phase F   (archive)

Checkpoint after each phase → can --resume-from.

CLI:
  python3 -m scripts.soul.orchestrator_v2 --auto            # uses trigger_detector
  python3 -m scripts.soul.orchestrator_v2 --manual --mode full
  python3 -m scripts.soul.orchestrator_v2 --resume-from phase2_5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

_DEBATE_ID_VALID_RE = re.compile(r"^[A-Za-z0-9_\-\.]+$")


def _validate_debate_id(debate_id: Optional[str]) -> Optional[str]:
    """Validate debate_id format to prevent path traversal. Returns error msg or None."""
    if debate_id is None:
        return None
    if not debate_id or not _DEBATE_ID_VALID_RE.match(debate_id):
        return (f"Invalid debate_id {debate_id!r}: only alphanumerics, "
                f"underscore, hyphen, dot allowed")
    if ".." in debate_id or debate_id.startswith("."):
        return f"Invalid debate_id {debate_id!r}: cannot contain '..' or start with '.'"
    return None

from scripts.soul.board import PROJECT_ROOT, PREP_DIR, HISTORY_DIR
from scripts.soul.board import trigger_detector
from scripts.soul.board import context_prep
from scripts.soul.board import seed_draft
from scripts.soul.board import sanitize
from scripts.soul.board import comparative
from scripts.soul.board import revise
from scripts.soul.board import cross_rebuttal
from scripts.soul.board import cluster as cluster_mod
from scripts.soul.board import vote_qualitative
from scripts.soul.board import vote_quantitative
from scripts.soul.board import vote_severity
from scripts.soul.board import render
from scripts.soul.board import compliance
from scripts.soul.board import archive

PHASE_STATE_PATH = PREP_DIR / "phase_state.json"

ALL_PHASES = [
    "phase-1",
    "phase0",
    "phase1",
    "phase1_5",
    "phase2",
    "phase2_5",
    "phase2_75",
    "phase3a",
    "phase3b_qual",
    "phase3b_quant",
    "phase3b_sev",
    "phase3c",
    "phaseE",
    "phaseF",
]


class Orchestrator:
    def __init__(self, debate_id: str, trigger_type: str, debate_mode: str,
                 scope: Optional[list] = None, skip_compliance: bool = False):
        self.debate_id = debate_id
        self.trigger_type = trigger_type
        self.debate_mode = debate_mode
        self.scope = scope or []
        self.skip_compliance = skip_compliance
        self.state: dict = {
            "debate_id": debate_id,
            "trigger_type": trigger_type,
            "debate_mode": debate_mode,
            "scope": scope,
            "phase_outputs": {},
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "status": "running",
        }

    def _save_checkpoint(self, phase_name: str, phase_output: dict) -> None:
        self.state["phase_outputs"][phase_name] = phase_output
        self.state["last_completed_phase"] = phase_name
        self.state["last_updated"] = datetime.now().isoformat(timespec="seconds")
        PREP_DIR.mkdir(parents=True, exist_ok=True)
        PHASE_STATE_PATH.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8",
        )

    def _load_checkpoint_if_exists(self) -> bool:
        if not PHASE_STATE_PATH.exists():
            return False
        try:
            prior = json.loads(PHASE_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return False
        if prior.get("debate_id") != self.debate_id:
            # Different debate; archive old state
            return False
        self.state = prior
        return True

    # ─── Phase runners ───

    def run_phase0(self) -> dict:
        return context_prep.prepare_context(
            self.debate_id, debate_mode=self.debate_mode, scope=self.scope,
        )

    def run_phase1(self, context: dict) -> dict:
        return seed_draft.draft_seeds_parallel(context)

    def run_phase1_5(self, phase1_summary: dict) -> dict:
        return sanitize.sanitize_all_seeds(phase1_summary)

    def run_phase2(self) -> dict:
        return comparative.phase2_comparative()

    def run_phase2_5(self) -> dict:
        return revise.revise_parallel()

    def run_phase2_75(self) -> dict:
        return cross_rebuttal.phase2_75_cross_rebuttal(self.debate_id)

    def run_phase3a(self) -> dict:
        return cluster_mod.phase3a_cluster()

    def run_phase3b_qual(self) -> dict:
        return vote_qualitative.phase3b_qual_vote(self.debate_id)

    def run_phase3b_quant(self, qual_summary: dict) -> dict:
        return vote_quantitative.phase3b_quant_vote(self.debate_id, qual_summary)

    def run_phase3b_sev(self) -> dict:
        return vote_severity.phase3b_severity_vote(self.debate_id)

    def run_phase3c(self) -> dict:
        return render.phase3c_render_and_gate(self.debate_id)

    def run_phaseE(self) -> dict:
        if self.skip_compliance:
            return {"skipped": True}
        # Scan all prep/ artifacts for this debate
        scan = compliance.scan_directory(PREP_DIR)
        return scan

    def run_phaseF(self) -> dict:
        # Build stats from prior phases
        stats = {
            "trigger_type": self.trigger_type,
            "debate_mode": self.debate_mode,
            "outcome": "success" if self.state.get("phase_outputs", {}).get("phase3c", {}).get("published") else "quarantine_or_partial",
        }
        # Aggregate selected stats
        p1 = self.state["phase_outputs"].get("phase1", {})
        p25 = self.state["phase_outputs"].get("phase2_5", {})
        p275 = self.state["phase_outputs"].get("phase2_75", {})
        p3a = self.state["phase_outputs"].get("phase3a", {})
        p3b_qual = self.state["phase_outputs"].get("phase3b_qual", {})
        p3c = self.state["phase_outputs"].get("phase3c", {})
        stats.update({
            "phase1_seed_counts": {m: r.get("seed_count") for m, r in p1.get("results_by_master", {}).items()},
            "phase1_partial_failure": p1.get("partial_failure", False),
            "phase1_fallback_count": p1.get("fallback_count", 0),
            "phase2_layer1_stats": self.state["phase_outputs"].get("phase2", {}).get("layer1_stats"),
            "phase2_layer2_stats": self.state["phase_outputs"].get("phase2", {}).get("layer2_stats"),
            "phase2_layer3_stats": self.state["phase_outputs"].get("phase2", {}).get("layer3_stats"),
            "phase2_5_fallback_count": p25.get("fallback_count", 0),
            "phase2_75_disputes_count": p275.get("total_disputes", 0),
            "phase2_75_convergence_stats": p275.get("convergence_stats"),
            "phase3a_cluster_counts": {
                "hard_candidate": p3a.get("hard_candidate"),
                "soft_candidate": p3a.get("soft_candidate"),
                "singleton": p3a.get("singleton"),
            },
            "phase3b_vote_results": p3b_qual.get("decision_counts"),
            "circuit_breaker": p3c.get("circuit_breaker"),
            "version_published": p3c.get("version"),
            "published": p3c.get("published"),
            "quarantine_path": p3c.get("quarantine_path"),
            "quarantine_reasons": p3c.get("quarantine_reasons"),
            "transcripts": p275.get("transcript_paths", []),
            "process_critique_entries": _load_process_critique(),
        })

        # Update last_debate_state (used by T2 detection next time)
        soul_states = trigger_detector.current_soul_doc_states()
        event_for_state = {
            "debate_id": self.debate_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "trigger_type": self.trigger_type,
        }
        trigger_detector.update_last_debate_state(event_for_state, soul_states)

        archive_dir = archive.archive_debate(
            self.debate_id, prep_dir=PREP_DIR, history_root=HISTORY_DIR, stats=stats,
        )
        return {"archive_dir": str(archive_dir), "stats": stats}

    # ─── Main ───

    def run(self, resume_from: Optional[str] = None) -> dict:
        """Run the pipeline end to end. Supports --resume-from phase name."""
        self._load_checkpoint_if_exists()
        completed = self.state.get("phase_outputs", {})

        def should_skip(phase_name: str) -> bool:
            if resume_from is None:
                return phase_name in completed
            try:
                resume_idx = ALL_PHASES.index(resume_from)
                current_idx = ALL_PHASES.index(phase_name)
                return current_idx < resume_idx
            except ValueError:
                return phase_name in completed

        # Reconstruct context from phase0 checkpoint on resume. If phase0
        # was already completed, its output must be available; otherwise
        # Phase 1 would crash on context["debate_id"].
        phase0_ckpt = self.state.get("phase_outputs", {}).get("phase0", {})
        context: dict = dict(phase0_ckpt) if phase0_ckpt else {}
        phase_sequence = [
            ("phase0", lambda: self.run_phase0()),
            ("phase1", lambda: self.run_phase1(context)),
            ("phase1_5", lambda: self.run_phase1_5(self.state["phase_outputs"].get("phase1", {}))),
            ("phase2", lambda: self.run_phase2()),
            ("phase2_5", lambda: self.run_phase2_5()),
            ("phase2_75", lambda: self.run_phase2_75()),
            ("phase3a", lambda: self.run_phase3a()),
            ("phase3b_qual", lambda: self.run_phase3b_qual()),
            ("phase3b_quant", lambda: self.run_phase3b_quant(self.state["phase_outputs"].get("phase3b_qual", {}))),
            ("phase3b_sev", lambda: self.run_phase3b_sev()),
            ("phase3c", lambda: self.run_phase3c()),
            ("phaseE", lambda: self.run_phaseE()),
            ("phaseF", lambda: self.run_phaseF()),
        ]

        for phase_name, runner in phase_sequence:
            if should_skip(phase_name):
                print(f"[orchestrator] skipping {phase_name} (already done or before resume point)")
                continue
            print(f"\n===== {phase_name} =====")
            try:
                result = runner()
                if phase_name == "phase0":
                    context.update(result)
                self._save_checkpoint(phase_name, result)
            except Exception as e:
                print(f"[orchestrator] ERROR in {phase_name}: {e}")
                traceback.print_exc()
                self.state["status"] = "error"
                self.state["error_phase"] = phase_name
                self.state["error_message"] = str(e)
                self._save_checkpoint(phase_name, {"error": str(e)})
                return self.state

            # Early exit if Phase 1 partial_failure
            if phase_name == "phase1":
                if result.get("partial_failure"):
                    print(f"[orchestrator] phase1 partial_failure — 2+ masters fell back; "
                          f"skipping later phases, going to archive")
                    self.state["status"] = "partial_failure"
                    # Skip to phaseF to archive whatever we have
                    try:
                        self._save_checkpoint("phaseF", self.run_phaseF())
                    except Exception as e:
                        print(f"[orchestrator] phaseF error: {e}")
                    return self.state

        self.state["status"] = "complete"
        self.state["completed_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_checkpoint("complete", {})
        return self.state


def _load_process_critique() -> list:
    """Aggregate per-master critique files produced in Phase 2.5.

    Also appends to the cumulative prep/process_critique.jsonl (which Archive
    preserves across debates). Safe to call multiple times — aggregation is
    idempotent by (master, content) de-dup is not done, so callers should
    invoke once per debate.
    """
    out = []
    for p in sorted(PREP_DIR.glob("process_critique_*.jsonl")):
        if p.name == "process_critique.jsonl":
            continue  # skip the global cumulative file
        try:
            with p.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            continue

    # Also append all to the global cumulative file (single writer, no race)
    if out:
        global_path = PREP_DIR / "process_critique.jsonl"
        try:
            with global_path.open("a", encoding="utf-8") as gf:
                for c in out:
                    gf.write(json.dumps(c, ensure_ascii=False) + "\n")
        except Exception:
            pass

    return out[-20:]  # last 20 entries


def main():
    ap = argparse.ArgumentParser(description="Principles Board Debate v0.4.1 orchestrator")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--auto", action="store_true",
                     help="Run trigger_detector first; exit if no trigger")
    g.add_argument("--manual", action="store_true",
                     help="Force manual run; requires --mode")
    g.add_argument("--resume-from", help="Resume from a specific phase (e.g. phase2_5)")
    ap.add_argument("--mode", choices=["full", "mini"], default="full")
    ap.add_argument("--scope", nargs="*", help="For mini mode: cluster_ids or seed_ids")
    ap.add_argument("--debate-id",
                     help="Override debate_id (usually auto-generated)")
    ap.add_argument("--skip-compliance", action="store_true",
                     help="Skip Phase E compliance scan (testing only)")
    args = ap.parse_args()

    # Validate any user-supplied debate_id
    if args.debate_id:
        err = _validate_debate_id(args.debate_id)
        if err:
            print(err, file=sys.stderr)
            sys.exit(2)

    if args.auto:
        event = trigger_detector.decide_trigger()
        if event is None:
            print("No trigger fired. Exiting.")
            sys.exit(0)
        trigger_detector.log_trigger_event(event)
        debate_id = args.debate_id or event["debate_id"]
        orch = Orchestrator(
            debate_id=debate_id,
            trigger_type=event["trigger_type"],
            debate_mode=event["debate_mode"],
            scope=event.get("scope"),
            skip_compliance=args.skip_compliance,
        )
        result = orch.run()
    elif args.manual:
        now = datetime.now().isoformat(timespec="seconds")[:10]
        debate_id = args.debate_id or f"{now}_manual"
        orch = Orchestrator(
            debate_id=debate_id,
            trigger_type="manual",
            debate_mode=args.mode,
            scope=args.scope,
            skip_compliance=args.skip_compliance,
        )
        result = orch.run()
    elif args.resume_from:
        # Need an existing state file
        if not PHASE_STATE_PATH.exists():
            print("No phase_state.json found — cannot resume.")
            sys.exit(2)
        prior_state = json.loads(PHASE_STATE_PATH.read_text(encoding="utf-8"))
        orch = Orchestrator(
            debate_id=prior_state["debate_id"],
            trigger_type=prior_state["trigger_type"],
            debate_mode=prior_state["debate_mode"],
            scope=prior_state.get("scope"),
            skip_compliance=args.skip_compliance,
        )
        result = orch.run(resume_from=args.resume_from)
    else:
        ap.print_help()
        sys.exit(2)

    print(f"\n===== DONE =====")
    print(f"Status: {result.get('status')}")
    print(f"Debate ID: {result.get('debate_id')}")
    phase3c = result.get("phase_outputs", {}).get("phase3c", {})
    if phase3c:
        print(f"Version: {phase3c.get('version')}")
        print(f"Published: {phase3c.get('published')}")
        print(f"HARD count: {phase3c.get('hard_count')}")


if __name__ == "__main__":
    main()
