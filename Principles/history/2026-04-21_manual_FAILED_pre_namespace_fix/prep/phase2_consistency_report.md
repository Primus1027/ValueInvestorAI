# Phase 2 Consistency Report

Layer 1 stats: {"total_pairs": 435, "skipped_different_subject": 272, "equivalent_after_l1": 2, "low_conf_after_l1": 0}
Layer 2 stats: {"arbitrated_count": 0, "arbitration_errors": 0, "equivalent_after_l2": 2}
Layer 3 stats: {"violations_detected": 8, "suggestions_from_sonnet": 0, "pairs_revised": 0}

Violations found: 8
- Triple ['seed_03', 'seed_05', 'seed_03']: AB=True BC=True AC=False
- Triple ['seed_03', 'seed_05', 'seed_05']: AB=True BC=False AC=True
- Triple ['seed_03', 'seed_03', 'seed_05']: AB=False BC=True AC=True
- Triple ['seed_05', 'seed_03', 'seed_05']: AB=True BC=True AC=False
- Triple ['seed_09', 'seed_10', 'seed_09']: AB=True BC=True AC=False
- Triple ['seed_09', 'seed_10', 'seed_10']: AB=True BC=False AC=True
- Triple ['seed_09', 'seed_09', 'seed_10']: AB=False BC=True AC=True
- Triple ['seed_10', 'seed_09', 'seed_10']: AB=True BC=True AC=False