# Scan Retrospective: scan_2026-04-19_vig

**Date**: 2026-04-19
**Source**: value-investing-gurus.pages.dev (editor: user's investor friend)
**Tier**: P4 (secondary synthesis); P3 (source-page variants)

## What worked

1. **API discovery**: JS bundle revealed clean `/api/zh/articles/<dir>/<id>.txt` endpoints.
   curl with `--compressed -L -f` + retries handled Cloudflare chunked response reliably after
   initial urllib `IncompleteRead` failures. Target: 134 pages, achieved: 134 (100%).

2. **Content-hash addressing**: Source files stored under `raw/<sha[:2]>/<sha>/payload.md`.
   Deduplication is free. Fetch metadata + paragraph anchors made the registry self-documenting.

3. **Delayed integration**: Scan (fetch + register) decoupled from integrate (soul update).
   This means incremental scans can land cheaply; expensive integration is batched.

4. **Decision-filter on extractions**: By forcing `decision_insights` to carry
   `decision_impact: factor_weight_evidence|red_flag|green_flag|case_study|evolution`,
   the LLM naturally filtered ~80% of raw insights that were philosophical but not actionable.

## What didn't work

1. **Verification yield is low**: 30 priority verifications processed, 20 "insufficient",
   7 "partial", 2 "supported", 1 "contradicted". The site's P4 content doesn't carry
   granular biographical detail (e.g., exact dollar amounts, specific dates). It's thematic,
   not reference-style.

   → **Lesson**: P4 secondary synthesis is GOOD for conceptual/philosophical validation,
   BAD for specific factual claims. Future verifications should prefer P0 primaries.

2. **Concept taxonomy bloat risk**: 47 site-introduced concepts vs 27 decision-relevant.
   Must discipline `concept_site_*` in `concepts.jsonl` to not leak into `decision_factor_for`.

3. **Time-per-extraction**: ~240s per article with Claude CLI (json-output mode). For 31
   articles × 3 extraction passes that's ~40 minutes, limited by CLI RTT not LLM compute.

## ROI Assessment

- `decision_delta_rate`: ~181.3% — 243 actionable insights over 134 sources
- `verification_resolution_rate`: 33% of priority verifications got evidence
- `novelty_rate`: ~estimated 15-25% (P4 site has high concept overlap with our existing material)
- `soul_doc_delta_words`: see `changelogs/W-v1.0-to-v1.1.md` and `C-v1.0-to-v1.1.md`
- `profile_factor_count_delta`: 0 (target) — factor list unchanged

**Overall ROI: medium**. Primary value was establishing the scan pipeline; information uplift was modest.

## Recommendations for next scan

1. **Prefer P0 sources**: Direct primary materials (new CNBC transcripts, new 13F filings, new shareholder letters) yield much higher decision_delta_rate than P4 secondary.
2. **Gap-driven targeting**: Before scanning, read `coverage.json` and target concepts with high `gap_score`.
3. **Pre-scan ROI estimator**: If predicted `novelty_rate` < 15%, consider "light touch" (archive only, skip integration).
4. **Scan budget caps** by tier:
   - P0: unbounded (always scan)
   - P1: ~10 per quarter
   - P4: ≤3 per quarter, and only if unique editorial angle

## Artifacts

- Registry: `Resources/Sources/registry/*.jsonl`
- Compendium views: `Resources/Sources/cross-master/views/value-investing-gurus-dev-2026-04/`
- Soul doc updates: `src/souls/documents/versions/W-buffett/v1.1.md`, `C-munger/v1.1.md`
- Changelogs: `src/souls/documents/changelogs/*-v1.0-to-v1.1.md`
- Calibration: `calibration_runs/run-*/report.md`
