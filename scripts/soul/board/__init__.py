"""Principles Board Debate v0.4.1 core package.

This package implements the automated debate pipeline described in
`Designs/principles-board-debate-v0.4.1.md`.

Module layout (by dependency level):
  Level 0:  (not in this package) _schemas/, _prompts/, _fingerprint_dict.json
  Level 1:  compliance.py
  Level 2:  dropped_tracker.py, agenda_tracker.py, archive.py
  Level 3:  context_prep.py, seed_draft.py, sanitize.py
  Level 4:  comparative.py, revise.py
  Level 5:  cross_rebuttal.py, cluster.py
  Level 6:  vote_qualitative.py, vote_quantitative.py, vote_severity.py
  Level 7:  render.py
  Level 8:  trigger_detector.py + ../orchestrator_v2.py

All LLM calls go through CliClaudeProvider pattern (subprocess to `claude -p`)
to use the Claude Max subscription, not API.
"""

from pathlib import Path

# Package-level paths (used by all modules)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_SOUL = PROJECT_ROOT / "scripts" / "soul"
SCHEMAS_DIR = SCRIPTS_SOUL / "_schemas"
PROMPTS_DIR = SCRIPTS_SOUL / "_prompts"
FINGERPRINT_DICT_PATH = SCRIPTS_SOUL / "_fingerprint_dict.json"

PREP_DIR = PROJECT_ROOT / "prep"
PRINCIPLES_DIR = PROJECT_ROOT / "Principles"
HISTORY_DIR = PRINCIPLES_DIR / "history"

# ─── Shared type aliases (documented; enforced by JSON Schema, not static checker) ───

RULE_SUBJECTS = ("target", "self", "decision_process")
SEVERITIES = ("veto", "warning", "note")
SEVERITY_ORDER = {"note": 0, "warning": 1, "veto": 2}  # lightest first
CATEGORIES = (
    "quantitative_hard", "qualitative_required", "veto_line",
    "valuation_method", "position_sizing",
)
THEMES = (
    "moat", "capital_return", "financial_strength", "management_integrity",
    "valuation_method", "behavioral_discipline", "circle_of_competence",
    "portfolio_construction", "accounting_quality", "opportunity_cost",
)
MASTERS = ("buffett", "munger", "duan")
MASTER_DISPLAY_NAMES = {
    "buffett": "Buffett 价值投资",
    "munger": "Munger 价值投资",
    "duan": "段永平价值投资",
}
EVIDENCE_STRENGTHS = ("direct_quote", "consistent_pattern", "reasonable_inference")
TRIGGER_TYPES = ("T1_quarterly", "T2_soul_doc_update", "T3_field_signal",
                 "T4_agenda_overflow", "manual")
DEBATE_MODES = ("full", "mini")


def master_display_name(master: str) -> str:
    """Return the display name used in prompts (framework-focused, not impersonation)."""
    return MASTER_DISPLAY_NAMES.get(master, master)
