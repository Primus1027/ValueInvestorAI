你是仲裁员。Sonnet 对下列两条投资方法论原则是否语义等价做了初判，但置信度不足以直接采信。请结合两条的**完整 rationale** 做最终判定。

==== Sonnet 初判 ====

```
equivalent: {sonnet_equivalent}
confidence: {sonnet_confidence}
brief_reason: "{sonnet_brief_reason}"
```

==== Seed A（完整）====

```
qualitative_claim: "{claim_a}"
rule_subject: {rule_subject_a}
theme: {theme_a}
quantitative_rule: {quantitative_rule_a}
severity: {severity_a}
rationale: "{rationale_a}"
anti_scope: "{anti_scope_a}"
```

==== Seed B（完整）====

```
qualitative_claim: "{claim_b}"
rule_subject: {rule_subject_b}
theme: {theme_b}
quantitative_rule: {quantitative_rule_b}
severity: {severity_b}
rationale: "{rationale_b}"
anti_scope: "{anti_scope_b}"
```

==== 判定要点 ====

对照以下 3 维判定（三者都需满足才算等价）：
1. 定性方向一致（两条是否在主张同一种判断）
2. 约束主体一致（target / self / decision_process 是否相同）
3. 触发情境本质相同

阈值差异不算不等价，range 差异不算不等价，rationale 措辞差异不算不等价。

==== 输出 ====

只输出 JSON:

```json
{{
  "equivalent_final": true|false,
  "rationale": "<100 字以内的判定依据，要具体指向 A/B 的某个字段差异或共同点>"
}}
```
