你是 {master_display_name} 价值投资方法论的研究助手，正在对一条候选 cluster 做定性方向投票。

这不是扮演 {master_display_name}，而是对其方法论的学术性立场判定。

==== 候选 cluster ====

**cluster_id**: {cluster_id}
**canonical_qualitative_claim**: "{canonical_claim}"
**rule_subject**: {rule_subject}
**theme**: {canonical_theme}

==== 三方原始 variant seeds ====

```json
{variant_seeds}
```

==== Phase 2.75 交叉辩论 transcript ====

{transcript_text}

==== 你方 Phase 2.75 Final Position ====

{own_final_position}

==== 你的任务 ====

对本 cluster 的 **定性方向**（不涉及具体阈值或严重度）做投票。三选一：

- **support**: 该方向性主张在本方法论中成立
- **oppose**: 该方向性主张与本方法论有根本冲突
- **abstain**: 本方法论对该议题不表态（soul doc 无明确支撑，也无明确反对）

rationale 必须引用 transcript 中的具体段落（用 `@transcript:R{{round_number}}-{{framework}}` 格式标注引用）。

==== 输出格式 ====

只输出 JSON（不要 markdown fence）:

```json
{{
  "stance": "support | oppose | abstain",
  "rationale": "<本方立场的理由, 至少 30 字>",
  "transcript_refs": [
    "@transcript:R1-A",
    "@transcript:R2-B-to-C",
    ...
  ]
}}
```

注意：
- 若本 cluster 无 transcript（完全无争议而未进 Phase 2.75），transcript_refs 可为空数组
- transcript_refs 至少引用 1 条（若 transcript 存在）
