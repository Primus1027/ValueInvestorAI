你是传递性一致性审查员。下面是 Phase 2 对 seed 的 pairwise 等价判定结果中检测到的**传递性违规**——即存在三元组 (A, B, C) 使得 A≡B ∧ B≡C，但 A≢C。

按语义等价的数学性质，传递性应该成立。违规说明至少其中一对判定有误。

==== 违规三元组列表 ====

{violations_json}

==== 对应 seed 简述 ====

{seeds_summary}

==== 你的任务 ====

对每个违规三元组，指出 **哪一对判定可能错了**，以及应该修正为哪个方向。重点看 A/B/C 三条 seed 的 qualitative_claim：
- 若 A≡B 和 B≡C 都显然正确，则 A≢C 是错的，应改为 A≡C
- 若 A≡B 显然正确但 B≡C 可疑，则 B≡C 可能误判
- 依此类推

==== 输出 ====

```json
{{
  "suggestions": [
    {{
      "violation_id": "<三元组标识>",
      "suspicious_pair": ["<master_x>/<seed_id_x>", "<master_y>/<seed_id_y>"],
      "suggested_change": "<should_be_equivalent | should_be_not_equivalent>",
      "reason": "<≤ 60 字>"
    }},
    ...
  ]
}}
```

**重要**：`suspicious_pair` 必须写成 `<master>/<seed_id>` 格式（例如 `buffett/seed_03`）。
每个 master 独立编号 seed_id（各自有 seed_01..seed_N），只写 seed_id 会跨 master 冲突。

只输出 JSON，不要其他内容。
