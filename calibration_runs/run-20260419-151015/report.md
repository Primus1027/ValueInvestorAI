# Calibration Report: run-20260419-151015

Timestamp: 2026-04-19T15:10:15.741012+00:00

Cases: 10  Masters: ['buffett', 'munger']  Versions: ['v1.0', 'v1.1-rc']


## Per-Case Comparison (v1.0 vs v1.1-rc)


### ADV-001.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: buy

### ADV-001.munger: =
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: skeptical_buy

### ADV-002.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: reluctant_buy

### ADV-002.munger: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### ADV-003.buffett: =
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: buy

### ADV-003.munger: =
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: skeptical

### CRS-001.buffett: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: hold_and_selectively_buy

### CRS-001.munger: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: buy_quality

### CRS-002.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: selective_interest

### CRS-002.munger: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: interested_in_google

### STD-001.buffett: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-001.munger: =
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: strong_buy

### STD-002.buffett: =
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### STD-002.munger: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### STD-003.buffett: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=buy match=False overlap=0.00
- Expected: pass

### STD-003.munger: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-004.buffett: IMPROVEMENT
- v1.0: decision=? match=False overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

### STD-004.munger: IMPROVEMENT
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

### STD-005.buffett: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy_more

### STD-005.munger: IMPROVEMENT
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

## Gate 5 Summary

- Improvements: 3
- Stable: 17
- Regressions: 0

**GATE 5: PASS** (no regressions)