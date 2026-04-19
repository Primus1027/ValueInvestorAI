# C-munger Soul Document: v1.0 → v1.1-rc

**Generated**: 2026-04-19T14:59:34.526307+00:00
**Scan**: scan_2026-04-19_vig
**Generator**: scripts/soul/integrate.py

## Summary of Changes

v1.1 is an **additive** update. No v1.0 prose is modified semantically. All changes are:

1. **Inline annotation** of `[NEEDS VERIFICATION]` lines with cross-check evidence
   - Changes: 0 annotations added
   - Format: `<!-- [v1.1 cross-check] vrf_id=... status=... quote="..." -->`
   - Status values: `supported` / `contradicted` / `partial`
   - Source: `Resources/Sources/registry/verifications_resolved.jsonl`

2. **Appendix Z: Cross-Master Comparisons** (new)
   - Count: 10 comparison entries
   - Purpose: feed multi-Agent debate scenarios with structured consensus/difference data
   - Source: value-investing-gurus.pages.dev synthesis + concept pages
   - Tier: P4 (secondary synthesis)

3. **Appendix: Investment Cases & Outcomes** (new)
   - Count: 29 case entries
   - Purpose: ground abstract concepts in real investments + outcomes for factor-weight calibration
   - Format: grouped by concept; each entry has company + year + outcome + supporting quote

4. **Appendix: Decision-Grade Insights** (new)
   - Count: 44 insight entries
   - Purpose: candidate flow into profile.json factor `red_flags` / `green_flags` / `how_to_evaluate`
   - Format: grouped by factor/concept tag

## Word Count

- v1.0: 17,651 words
- v1.1-rc: 19,011 words
- Delta: 1,360 words (+7%)

Target was ≤15% growth; this is within budget.

## Traceability

Every claim in the appendices has a `<!-- source: ARTICLE_ID -->` inline comment.
ARTICLE_ID maps to `Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04/<type>/<ARTICLE_ID>.zh.md`.
From there, follow the frontmatter `source_url` back to the original vig URL.

## Review Status

- **Gate 4 (Patch approval)**: pending — review the appendix content before promote
- **Gate 5 (Calibration)**: pending — run `scripts/soul/calibrate.py` to check no regression

## Promotion

Once Gate 5 passes, promote with:
```bash
mv src/souls/documents/versions/C-munger/v1.1-rc.md src/souls/documents/versions/C-munger/v1.1.md
ln -sf ../versions/C-munger/v1.1.md src/souls/documents/current/M.md
```
