# Calibration Report: run-20260419-162546 (regenerated 2026-04-20)

Cases: 10  Masters: ['buffett', 'munger', 'duan']  Versions: ['v1.0', 'v1.1']


## Per-Case Comparison (v1.0 vs v1.1)


### ADV-001.buffett: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: buy

### ADV-001.munger: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: buy (nuance: skeptical_buy)

### ADV-002.buffett: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: buy (nuance: reluctant_buy)

### ADV-002.duan: SINGLE_VERSION
- v1.0: decision=avoid match=True
- v1.1: (not run — soul file missing)
- Expected: avoid (nuance: pass)

### ADV-002.munger: =
- v1.0: decision=strong_buy match=True
- v1.1: decision=strong_buy match=True
- Expected: strong_buy

### ADV-003.buffett: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: buy

### ADV-003.duan: SINGLE_VERSION
- v1.0: decision=avoid match=True
- v1.1: (not run — soul file missing)
- Expected: avoid (nuance: pass)

### ADV-003.munger: =
- v1.0: decision=avoid match=True
- v1.1: decision=avoid match=True
- Expected: avoid (nuance: skeptical)

### CRS-001.buffett: =
- v1.0: decision=buy match=True
- v1.1: decision=buy match=True
- Expected: buy (nuance: hold_and_selectively_buy)

### CRS-001.duan: SINGLE_VERSION
- v1.0: decision=buy match=False
- v1.1: (not run — soul file missing)
- Expected: strong_buy (nuance: hold_and_add)

### CRS-001.munger: =
- v1.0: decision=strong_buy match=False
- v1.1: decision=strong_buy match=False
- Expected: buy (nuance: buy_quality)

### CRS-002.buffett: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: hold (nuance: selective_interest)

### CRS-002.duan: SINGLE_VERSION
- v1.0: decision=avoid match=False
- v1.1: (not run — soul file missing)
- Expected: hold (nuance: cautious)

### CRS-002.munger: =
- v1.0: decision=avoid match=False
- v1.1: decision=avoid match=False
- Expected: buy (nuance: interested_in_google)

### STD-001.buffett: =
- v1.0: decision=strong_buy match=True
- v1.1: decision=strong_buy match=True
- Expected: strong_buy

### STD-001.duan: SINGLE_VERSION
- v1.0: decision=buy match=True
- v1.1: (not run — soul file missing)
- Expected: buy

### STD-001.munger: =
- v1.0: decision=strong_buy match=True
- v1.1: decision=strong_buy match=True
- Expected: strong_buy

### STD-002.buffett: =
- v1.0: decision=strong_buy match=False
- v1.1: decision=strong_buy match=False
- Expected: buy

### STD-002.duan: SINGLE_VERSION
- v1.0: decision=buy match=False
- v1.1: (not run — soul file missing)
- Expected: strong_buy

### STD-002.munger: REGRESSION
- v1.0: decision=buy match=True
- v1.1: decision=strong_buy match=False
- Expected: buy

### STD-003.buffett: =
- v1.0: decision=buy match=False
- v1.1: decision=buy match=False
- Expected: avoid (nuance: pass)

### STD-003.duan: SINGLE_VERSION
- v1.0: decision=buy match=False
- v1.1: (not run — soul file missing)
- Expected: hold (nuance: neutral)

### STD-003.munger: =
- v1.0: decision=strong_buy match=True
- v1.1: decision=strong_buy match=True
- Expected: strong_buy

### STD-004.buffett: =
- v1.0: decision=strong_buy match=False
- v1.1: decision=strong_buy match=False
- Expected: buy

### STD-004.duan: SINGLE_VERSION
- v1.0: decision=strong_buy match=True
- v1.1: (not run — soul file missing)
- Expected: strong_buy

### STD-004.munger: IMPROVEMENT
- v1.0: decision=strong_buy match=False
- v1.1: decision=buy match=True
- Expected: buy

### STD-005.buffett: =
- v1.0: decision=strong_buy match=True
- v1.1: decision=strong_buy match=True
- Expected: strong_buy (nuance: buy_more)

### STD-005.duan: SINGLE_VERSION
- v1.0: decision=avoid match=True
- v1.1: (not run — soul file missing)
- Expected: avoid (nuance: neutral_to_pass)

### STD-005.munger: =
- v1.0: decision=buy match=True
- v1.1: decision=buy match=True
- Expected: buy

## Gate 5 Summary (regenerated)

- Improvements: 1
- Stable: 18
- Regressions (REAL): 1
- Single-version coverage: 9 (duan has no v1.1 yet; not a regression)

**GATE 5: NEEDS REVIEW** (1 real regression(s))