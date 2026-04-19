# Calibration Report: run-20260419-162546

Timestamp: 2026-04-19T16:25:46.750226+00:00

Cases: 10  Masters: ['buffett', 'munger', 'duan']  Versions: ['v1.0', 'v1.1']


## Per-Case Comparison (v1.0 vs v1.1)


### ADV-001.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: buy

### ADV-001.munger: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: buy

### ADV-002.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: buy

### ADV-002.duan: REGRESSION
- v1.0: decision=avoid match=True overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: avoid

### ADV-002.munger: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### ADV-003.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: buy

### ADV-003.duan: REGRESSION
- v1.0: decision=avoid match=True overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: avoid

### ADV-003.munger: =
- v1.0: decision=avoid match=True overlap=0.00
- v1.1: decision=avoid match=True overlap=0.00
- Expected: avoid

### CRS-001.buffett: =
- v1.0: decision=buy match=True overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

### CRS-001.duan: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: strong_buy

### CRS-001.munger: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### CRS-002.buffett: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: hold

### CRS-002.duan: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: hold

### CRS-002.munger: =
- v1.0: decision=avoid match=False overlap=0.00
- v1.1: decision=avoid match=False overlap=0.00
- Expected: buy

### STD-001.buffett: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-001.duan: REGRESSION
- v1.0: decision=buy match=True overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: buy

### STD-001.munger: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-002.buffett: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### STD-002.duan: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: strong_buy

### STD-002.munger: REGRESSION
- v1.0: decision=buy match=True overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### STD-003.buffett: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=buy match=False overlap=0.00
- Expected: avoid

### STD-003.duan: =
- v1.0: decision=buy match=False overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: hold

### STD-003.munger: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-004.buffett: =
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=strong_buy match=False overlap=0.00
- Expected: buy

### STD-004.duan: REGRESSION
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: strong_buy

### STD-004.munger: IMPROVEMENT
- v1.0: decision=strong_buy match=False overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

### STD-005.buffett: =
- v1.0: decision=strong_buy match=True overlap=0.00
- v1.1: decision=strong_buy match=True overlap=0.00
- Expected: strong_buy

### STD-005.duan: REGRESSION
- v1.0: decision=avoid match=True overlap=0.00
- v1.1: decision=? match=False overlap=0.00
- Expected: avoid

### STD-005.munger: =
- v1.0: decision=buy match=True overlap=0.00
- v1.1: decision=buy match=True overlap=0.00
- Expected: buy

## Gate 5 Summary

- Improvements: 1
- Stable: 22
- Regressions: 6

**GATE 5: NEEDS REVIEW** (6 regression(s))