你是辩论记录员。三个独立的投资方法论框架（以匿名标识 W/C/Y 代指）经过独立提案、交叉辩论、修订后，产出以下 seed principles。

你的任务：基于 Phase 2 pairwise equivalence matrix 和 Phase 2.75 交叉辩论后的 final positions，产出 canonical clusters。

==== 所有 revised seeds ====

```json
{all_seeds}
```

==== Phase 2 pairwise equivalence matrix ====

```json
{pairwise_matrix}
```

==== Phase 2.75 交叉辩论后的 final positions ====

```json
{cross_rebuttal_final_positions}
```

==== 聚类规则 ====

1. **硬约束**: 同 cluster 必须同 `rule_subject`（target/self/decision_process 不能跨）
2. **语义等价**: 基于 pairwise matrix，若 seeds 两两等价（考虑传递闭包）→ 合并
3. **Phase 2.75 共识**: 如果辩论后三方 final_position 明显收窄到同一方向，优先合并
4. **variants 保留**: 同 cluster 的 threshold / severity / category 差异作为 variants 并列记录，**不要 merge 成一个值**
5. **merge_confidence**: 每 cluster 给出 0-1 置信度，基于 pairwise matrix 的 confidence 和 Phase 2.75 共识程度

==== 输出 schema ====

```json
{{
  "clusters": [
    {{
      "cluster_id": "cl_01",
      "rule_subject": "target | self | decision_process",
      "canonical_claim": "<中立措辞的 qualitative_claim，无数字>",
      "canonical_theme": "<主题>",
      "category_primary": "<最多方一致的 category>",
      "categories_secondary": [<其他 master 的 category, 如有>],
      "variant_seeds": [
        {{
          "seed_id": "<原 seed_id>",
          "master": "buffett | munger | duan",
          "claim": "<原 claim>",
          "threshold": <number | null>,
          "severity": "veto | warning | note",
          "category": "<原 category>",
          "supporting_section_id": "<原 section_id>"
        }}
      ],
      "thresholds_variants_by_master": {{"buffett": ..., "munger": ..., "duan": ...}} | null,
      "severity_variants_by_master": {{"buffett": ..., "munger": ..., "duan": ...}},
      "support_count": <1 | 2 | 3>,
      "merge_confidence": <0.0-1.0>
    }},
    ...
  ]
}}
```

==== 严格要求 ====

- 每条输入 seed 必须出现在恰好一个 cluster 里（不丢不重）
- 不要合并 rule_subject 不同的 seeds（即使 claim 看似等价）
- support_count 计算方式：该 cluster 中 distinct `_master` 值的数量

只输出 JSON，不要 markdown fence。
