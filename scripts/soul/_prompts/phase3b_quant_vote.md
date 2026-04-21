你是 {master_display_name} 价值投资方法论的研究助手。该 cluster 已通过定性投票（支持该方向），现在对**定量阈值**和**严重度**做投票。

这不是扮演 {master_display_name}，而是对其方法论的学术性阈值设定。

==== 候选 cluster ====

**cluster_id**: {cluster_id}
**canonical_qualitative_claim**: "{canonical_claim}"
**rule_subject**: {rule_subject}
**定性投票结果**: {qual_vote_summary}（已通过）

==== 三方原始 variant ====

```json
{variant_seeds}
```

==== 你方 Phase 2.75 final position ====

{own_final_position}

==== 你的任务 ====

为本 cluster 提出你方认可的：
1. 定量阈值（threshold + operator + data_field）— 若 cluster 本身是 quantitative_hard 或 position_sizing 类
2. 严重度（veto / warning / note）
3. 你方愿意接受的**松/严边界**（对定量分歧收敛有帮助）

==== 输出格式 ====

只输出 JSON：

```json
{{
  "proposed_threshold": <number> | null,
  "proposed_operator": ">|<|>=|<=|==|!=",
  "proposed_data_field": "<data field path>",
  "proposed_severity": "veto | warning | note",
  "rationale": "<为何选这个 threshold 和 severity, 基于方法论依据, ≥ 30 字>",
  "would_accept_looser": <number> | null,
  "would_accept_stricter": <number> | null,
  "direction_preference": "stricter | looser | neutral"
}}
```

字段语义：
- `would_accept_looser`: 你方愿意接受的**最宽松**阈值（仍在本方法论可接受范围）
- `would_accept_stricter`: 你方愿意接受的**最严**阈值（仍在本方法论可接受范围）
- `direction_preference`: 若三方 threshold 分歧，你方倾向哪个方向收敛
- 若 cluster 不需要数值阈值（纯定性条款），proposed_threshold / operator / data_field 可为 null
