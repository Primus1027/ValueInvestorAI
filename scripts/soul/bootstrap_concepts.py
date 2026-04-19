#!/usr/bin/env python3
"""
Bootstrap concept taxonomy.

Strategy:
  1. Seed from profile.json factors (primary concepts, canonical for decision-making)
  2. Add site's 63 concept IDs (secondary, may or may not map to factors)
  3. Build alias table (EN/ZH mappings)

Output:
  Resources/Sources/registry/concepts.jsonl         (canonical concepts)
  Resources/Sources/registry/concept_aliases.jsonl  (EN/ZH/variant → concept_id)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"
NOW = datetime.now(timezone.utc).isoformat()


def main():
    # Load profiles
    with (PROJECT_ROOT / "src/souls/profiles/buffett.json").open() as f:
        b = json.load(f)
    with (PROJECT_ROOT / "src/souls/profiles/munger.json").open() as f:
        m = json.load(f)
    with (PROJECT_ROOT / "src/souls/profiles/duan.json").open() as f:
        d = json.load(f)

    concepts = []  # list of concept records
    aliases = []   # list of alias records
    concept_id_set = set()

    # Primary concepts from W/C/Y profile factors
    # Each factor's `name` becomes a concept, canonically-defined by the profile
    def add_concept(cid, en_label, zh_label, definition, parent, source_lineage, decision_factor_for=None):
        if cid in concept_id_set:
            return
        concept_id_set.add(cid)
        rec = {
            "concept_id": cid,
            "canonical_label_en": en_label,
            "canonical_label_zh": zh_label,
            "definition": definition,
            "parent_concept": parent,
            "source_lineage": source_lineage,
            "decision_factor_for": decision_factor_for or [],  # list of master_ids
            "introduced_at": NOW,
            "status": "active",
        }
        concepts.append(rec)

    def add_alias(cid, variant, lang):
        aliases.append({"concept_id": cid, "variant": variant, "lang": lang})

    # Profile factors (canonical decision concepts)
    for factor in b["decision_framework"]["factors"]:
        fname = factor["name"]
        cid = f"concept_{fname}"
        add_concept(
            cid, fname.replace("_", " ").title(),
            "",  # will be filled later by ZH mapping
            factor["description"],
            parent=f"concept_category_{factor['category']}",
            source_lineage="buffett.json profile factor",
            decision_factor_for=["buffett"]
        )
    for factor in m["decision_framework"]["factors"]:
        fname = factor["name"]
        cid = f"concept_{fname}"
        if cid in concept_id_set:
            # Already exists — add munger as another decision factor user
            for c in concepts:
                if c["concept_id"] == cid:
                    c["decision_factor_for"].append("munger")
                    break
        else:
            add_concept(
                cid, fname.replace("_", " ").title(), "",
                factor["description"],
                parent=f"concept_category_{factor['category']}",
                source_lineage="munger.json profile factor",
                decision_factor_for=["munger"]
            )
    for factor in d["decision_framework"]["factors"]:
        fname = factor["name"]
        cid = f"concept_{fname}"
        if cid in concept_id_set:
            for c in concepts:
                if c["concept_id"] == cid:
                    if "duan" not in c["decision_factor_for"]:
                        c["decision_factor_for"].append("duan")
                    break
        else:
            add_concept(
                cid, fname.replace("_", " ").title(), "",
                factor["description"],
                parent=f"concept_category_{factor['category']}",
                source_lineage="duan.json profile factor",
                decision_factor_for=["duan"]
            )

    # Site's 63 concept IDs (add as supplementary)
    # These may overlap with profile factor concepts — we keep them as separate
    # concept_id (concept_site_<id>) and will link via alias if semantically equivalent.
    site_concepts_zh = {}
    sources_file = PROJECT_ROOT / "Resources/Sources/registry/sources.jsonl"
    with sources_file.open() as f:
        for line in f:
            s = json.loads(line)
            if s["metadata"]["article_type"] == "concept" and s["metadata"]["language"] == "zh":
                aid = s["metadata"]["article_id"]
                title = s["metadata"]["title"]
                site_concepts_zh[aid] = title

    # Map from site concept ID to profile factor concept (where obvious)
    alignment = {
        "circle_of_competence": "concept_business_understandability",
        "competitive_moat": "concept_durable_competitive_advantage",
        "pricing_power": "concept_pricing_power",
        "management_integrity": "concept_management_integrity_and_candor",
        "accounting_quality": "concept_management_integrity_and_candor",  # related
        "capital_allocation": "concept_capital_allocation_track_record",
        "cash_flow": "concept_owner_earnings_and_cash_generation",
        "valuation": "concept_margin_of_safety",
        "financial_strength": "concept_financial_strength_and_conservatism",
        "compounding": "concept_compounding",  # new, not in profiles directly
        "cognitive_biases": "concept_psychological_bias_audit",
        "behavioral": "concept_psychological_bias_audit",
        "mental_models": "concept_multidisciplinary_model_check",
        "inversion": "concept_inversion_stress_test",
        "concentrated_investing": "concept_opportunity_cost_discipline",
        "business_quality": "concept_return_on_equity_without_leverage",
        "value_investing_philosophy": "concept_margin_of_safety",
        "long_term_thinking": "concept_temperament_and_discipline",
        "simplicity": "concept_simplicity_and_understandability",
        "temperament_and_discipline": "concept_temperament_and_discipline",
    }

    for site_id, zh_title in site_concepts_zh.items():
        if site_id in alignment:
            target_cid = alignment[site_id]
            # It's an alias
            add_alias(target_cid, site_id, "en")
            if zh_title:
                add_alias(target_cid, zh_title, "zh")
            # Also set ZH canonical label on target if unset
            for c in concepts:
                if c["concept_id"] == target_cid and not c["canonical_label_zh"]:
                    c["canonical_label_zh"] = zh_title
                    break
        else:
            # Net new concept introduced by the site, not in our profile factors
            new_cid = f"concept_site_{site_id}"
            add_concept(
                new_cid,
                site_id.replace("_", " ").title(),
                zh_title,
                f"Site-defined concept: {zh_title} (auto-seeded from vig scan)",
                parent=None,
                source_lineage="value-investing-gurus.pages.dev",
                decision_factor_for=[]
            )
            add_alias(new_cid, site_id, "en")
            if zh_title:
                add_alias(new_cid, zh_title, "zh")

    # Write registries
    REG_DIR.mkdir(parents=True, exist_ok=True)
    with (REG_DIR / "concepts.jsonl").open("w", encoding="utf-8") as f:
        for c in concepts:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (REG_DIR / "concept_aliases.jsonl").open("w", encoding="utf-8") as f:
        for a in aliases:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    # Summary
    decision_concepts = [c for c in concepts if c["decision_factor_for"]]
    site_only = [c for c in concepts if c["source_lineage"] == "value-investing-gurus.pages.dev"]

    print(f"Total concepts: {len(concepts)}")
    print(f"  Decision-relevant (from profile factors): {len(decision_concepts)}")
    print(f"  Site-introduced (supplementary): {len(site_only)}")
    print(f"Total aliases: {len(aliases)}")
    print(f"\nDecision concepts:")
    for c in decision_concepts:
        labels = "|".join(filter(None, [c["canonical_label_en"], c["canonical_label_zh"]]))
        print(f"  {c['concept_id']}: {labels} (masters: {c['decision_factor_for']})")


if __name__ == "__main__":
    main()
