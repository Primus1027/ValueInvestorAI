#!/usr/bin/env python3
"""
Extract all [NEEDS VERIFICATION] markers from W/C soul docs.

Also reads the corresponding GPT review file to get more context per marker.
Outputs verifications.jsonl with structured records per marker.
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REG_DIR = PROJECT_ROOT / "Resources/Sources/registry"

SOUL_DOCS = {
    "buffett": PROJECT_ROOT / "src/souls/documents/versions/W-buffett/v1.0.md",
    "munger": PROJECT_ROOT / "src/souls/documents/versions/C-munger/v1.0.md",
}
REVIEWS = {
    "buffett": PROJECT_ROOT / "src/souls/documents/reviews/W-review-gpt5.3.md",
    "munger": PROJECT_ROOT / "src/souls/documents/reviews/C-review-gpt5.3.md",
}


def find_verifications(soul_doc_text: str, master: str) -> list[dict]:
    """Find [NEEDS VERIFICATION] markers with surrounding context."""
    lines = soul_doc_text.split("\n")
    results = []
    for i, line in enumerate(lines):
        if "[NEEDS VERIFICATION]" not in line:
            continue
        # Get 2 lines before, the marker line, and 2 lines after
        ctx_start = max(0, i - 2)
        ctx_end = min(len(lines), i + 3)
        context_block = "\n".join(lines[ctx_start:ctx_end])
        # Try to extract the concrete claim being flagged
        claim_match = re.search(r"\[NEEDS VERIFICATION\]:?\s*(.+?)$", line)
        claim = claim_match.group(1).strip() if claim_match else ""
        # Find enclosing section (look back for most recent ## or ### heading)
        section = ""
        for j in range(i, -1, -1):
            m = re.match(r"^(#{1,4})\s+(.+)", lines[j])
            if m:
                section = m.group(2).strip()
                break

        results.append({
            "master": master,
            "line_number": i + 1,
            "full_line": line,
            "claim": claim,
            "section": section,
            "context": context_block,
        })
    return results


def load_review_findings(review_text: str) -> list[dict]:
    """Parse GPT review file into structured findings."""
    findings = []
    # Pattern: ### Finding N.M\n- **Text:** "..."\n- **Issue:** ...\n- **Confidence:** ...\n- **Suggested Fix:** ...
    blocks = re.split(r"###\s+Finding\s+", review_text)
    for b in blocks[1:]:
        first_line_end = b.find("\n")
        if first_line_end == -1:
            continue
        fid = b[:first_line_end].strip()
        body = b[first_line_end:]
        # Find Check context (look back in earlier part)
        txt_m = re.search(r"\*\*Text:\*\*\s*[\"\"]?(.+?)[\"\"]?\s*\n", body, re.DOTALL)
        issue_m = re.search(r"\*\*Issue:\*\*\s*(.+?)(?=\n-|\n###|\Z)", body, re.DOTALL)
        conf_m = re.search(r"\*\*Confidence:\*\*\s*(\w+)", body)
        fix_m = re.search(r"\*\*Suggested Fix:\*\*\s*(.+?)(?=\n-|\n###|\Z)", body, re.DOTALL)
        findings.append({
            "finding_id": fid,
            "text": txt_m.group(1).strip() if txt_m else "",
            "issue": issue_m.group(1).strip() if issue_m else "",
            "confidence": conf_m.group(1) if conf_m else "",
            "suggested_fix": fix_m.group(1).strip() if fix_m else "",
        })
    return findings


def main():
    all_verifications = []

    for master in ["buffett", "munger"]:
        soul_text = SOUL_DOCS[master].read_text(encoding="utf-8")
        review_text = REVIEWS[master].read_text(encoding="utf-8")

        marker_records = find_verifications(soul_text, master)
        review_findings = load_review_findings(review_text)

        print(f"\n=== {master.upper()} ===")
        print(f"NEEDS VERIFICATION markers: {len(marker_records)}")
        print(f"GPT review findings: {len(review_findings)}")

        # Merge: for each marker, try to find a review finding with overlapping text
        for i, m in enumerate(marker_records):
            merged_finding = None
            claim_snippet = m["context"][:200].lower()
            for rf in review_findings:
                # Simple text overlap heuristic
                rf_text_lower = rf["text"][:200].lower()
                if rf_text_lower and rf_text_lower[:50] in claim_snippet:
                    merged_finding = rf
                    break
            all_verifications.append({
                "verification_id": f"vrf_{master[0].upper()}_{i+1:02d}",
                "master_id": master,
                "soul_doc_path": str(SOUL_DOCS[master].relative_to(PROJECT_ROOT)),
                "line_number": m["line_number"],
                "section": m["section"],
                "full_line": m["full_line"].strip(),
                "claim_at_marker": m["claim"],
                "context_block": m["context"],
                "gpt_review_finding": merged_finding,
                "status": "pending_verification",
                "resolution": None,
            })

        # Also add GPT findings that have HIGH/MEDIUM confidence even if no NEEDS VERIFICATION marker yet
        # (expanded review queue)
        for rf in review_findings:
            if rf["confidence"] in ("HIGH", "MEDIUM"):
                # Skip if already merged
                already_merged = any(v for v in all_verifications
                                      if v["master_id"] == master
                                      and v.get("gpt_review_finding") is not None
                                      and v["gpt_review_finding"].get("finding_id") == rf["finding_id"])
                if already_merged:
                    continue
                all_verifications.append({
                    "verification_id": f"vrf_{master[0].upper()}_gpt_{rf['finding_id'].replace('.', '_')}",
                    "master_id": master,
                    "soul_doc_path": str(SOUL_DOCS[master].relative_to(PROJECT_ROOT)),
                    "line_number": None,
                    "section": "",
                    "full_line": "",
                    "claim_at_marker": "",
                    "context_block": "",
                    "gpt_review_finding": rf,
                    "status": "pending_verification",
                    "resolution": None,
                    "source": "gpt_review_backlog",
                })

    REG_DIR.mkdir(parents=True, exist_ok=True)
    fp = REG_DIR / "verifications.jsonl"
    with fp.open("w", encoding="utf-8") as f:
        for v in all_verifications:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")

    # Summary
    print(f"\n=== TOTAL ===")
    print(f"Verifications to resolve: {len(all_verifications)}")
    for m in ["buffett", "munger"]:
        ms = [v for v in all_verifications if v["master_id"] == m]
        marker_only = [v for v in ms if not v.get("source")]
        gpt_only = [v for v in ms if v.get("source") == "gpt_review_backlog"]
        print(f"  {m}: {len(ms)} total ({len(marker_only)} from markers, {len(gpt_only)} from GPT review backlog)")
    print(f"\nWritten: {fp}")


if __name__ == "__main__":
    main()
