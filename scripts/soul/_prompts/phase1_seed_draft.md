你是一位价值投资方法论研究助手，正在对投资方法论做学术性的原则提炼演练。

本练习的任务：基于下述价值投资方法论文档（整理自 {master_display_name} 的公开著作和访谈），提炼出 5-20 条可作为投资决策硬约束的 principle seeds。这是研究性质的方法论分析，不构成真实投资建议，也不是在扮演任何真实人物。

==== 方法论文档节选 ====
{priority_sections_text}

==== 评估因子（profile） ====
{profile_json}

==== 章节索引（可通过 section_id 引用）====
{soul_toc_summary}

==== 本轮辩论上下文 ====
- Debate ID: {debate_id}
- Debate Mode: {debate_mode}
- Re-introduction 候选（历史 DROPPED 条款，你可选择 1-3 条重新提出，需填写完整 _reintroduced_* 字段）:
{reintro_candidates}

==== 硬性输出规则（违反任一条 → 校验失败 retry）====

1. **原子性**: 每条 seed 只能表达一个观点。禁止复合 claim（如"既 A 又 B"、"不 A 但 B"、"同意 X 但反对 Y"）。复合观点必须拆成多条独立 seed。
2. **qualitative_claim 纯定性**: 不得含任何数字、百分号、具体年限。阈值放在 quantitative_rule。
3. **rule_subject 分类**:
   - `target` = 约束被投标的（公司）
   - `self` = 约束投资机构/投资人自身（如不借贷、持有期、持仓数量）
   - `decision_process` = 约束分析流程本身（如反 DCF、反季报驱动、质量先于价格）
4. **anti_scope 必填**: 本条不约束什么，防止过度解读。
5. **severity 从 seed 内在逻辑决定**，不要为了"更强"而都写 veto。
6. **最低门槛**: 必须至少产出 5 条合规 seed，否则本轮视为失败。

==== Seed Schema（严格遵循）====

```json
{{
  "seed_id": "seed_XX",
  "rule_subject": "target | self | decision_process",
  "theme": "<从预设 10 个主题选 1，见下>",
  "category": "quantitative_hard | qualitative_required | veto_line | valuation_method | position_sizing",
  "qualitative_claim": "<方向性陈述，无数字，无复合>",
  "quantitative_rule": null | {{
    "metric": "<METRIC_NAME>",
    "operator": "<OP>",
    "threshold": <NUMERIC_THRESHOLD>,
    "data_field": "<DATA_FIELD_PATH>"
  }},
  "qualitative_rule": null | "<可机器执行的定性规则描述>",
  "severity": "veto | warning | note",
  "anti_scope": "<SCOPE_EXCLUSION>",
  "rationale": "<方法论依据, 至少 20 字, 可引用 soul doc 或 profile>",
  "evidence_strength": "direct_quote | consistent_pattern | reasonable_inference",
  "supporting_section_id": "<soul doc anchor>",
  "supporting_profile_factor": "<profile factor id>",
  "_master": "{master}",
  "_reintroduced_from": null | "<cl_XX (v1.X dropped-archive)>",
  "_reintroduction_rationale": null | "<soul doc 新章节说明>",
  "_reintroduced_seed_commit_hash": null | "<git commit hash>",
  "_reintroduced_seed_section_id": null | "<新章节 anchor>"
}}
```

可选 theme: `moat`, `capital_return`, `financial_strength`, `management_integrity`, `valuation_method`, `behavioral_discipline`, `circle_of_competence`, `portfolio_construction`, `accounting_quality`, `opportunity_cost`

==== 输出格式 ====

只输出一个 JSON object，结构如下（不要 markdown fence, 不要前后文字）:

```json
{{
  "seeds": [
    {{ /* seed_01 */ }},
    {{ /* seed_02 */ }},
    ...
  ]
}}
```

现在开始提炼 seeds。专注方法论本质，不要为了数量硬凑。
