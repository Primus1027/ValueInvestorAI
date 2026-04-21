# Pre-A: Principles Board Debate — 设计 v0.3（v1.1 升级版）

> 状态：**草案，待用户 sign-off（Q9–Q12 待回复后定稿）**
> 日期：2026-04-21
> 版本：v0.3
> 取代：`Designs/principles-board-debate-v0.2.md`（v0.2 已用于 v1.0 生成，留档不删）
> 依赖：Pre-A v1.0 执行产出（`Principles/v1.0.md` + `prep/phase*` 中间产出）的经验教训

---

## 零、一页 Executive Summary

**目标**：升级 Pre-A 辩论流程以产出 `Principles/v1.1.md`，解决 v1.0 执行中暴露的 4 个结构性问题：

| v1.0 暴露的问题 | v0.3 对应解法 |
|---|---|
| 议题混用 "target"（约束标的）vs "self"（约束投资人自身）导致共识议题被错误 DROP（如不借贷/不做空） | **Seed schema 新增 `rule_subject: target \| self \| decision_process` 三分维度**，Phase 3 聚类按 `(subject, category)` 二维网格 |
| Phase 2 Opus double-run 一致率仅 20%（目标 80%），stance 判定建立在噪声上 | **Phase 2 改 3-run majority voting**；< 2/3 一致的 stance 标记 `low_confidence` 交人工复审 |
| Phase 2.5 超时 fallback 全"keep"导致 C 完全未参与修订 | **Timeout 拉到 900s + 最多 2 次 retry**；两次仍失败才 fallback 并显式告警 |
| 定性一致但定量分歧（如持有期 3/5/10 年）被当作 DROP，损失了跨方法论方向共识 | **投票分层**：定性方向投票 → 定量阈值投票 → 严重度投票；三个维度分别汇总为三层结论 |

**v0.3 最核心的哲学转变**：
> 议题的**定性内核抽取**不再由 Opus 后验做，而是**在 Phase 1 由每位方法论研究助手直接按结构化 schema 输出**。研究助手最理解自己的立场，由他们自己结构化优于由第三方推断。

---

## 一、产出物

| 文件 | 格式 | 状态 | 说明 |
|---|---|---|---|
| `Principles/v1.1.md` | Markdown | 🆕 本流程产出 | 新增 `target` / `self` / `decision_process` 三段式结构 |
| `Principles/v1.1.schema.json` | JSON | 🆕 本流程产出 | 扩展 v1.0 schema 支持 rule_subject + follow_up_agenda |
| `Principles/soul-level-preferences-v1.1.md` | Markdown | 🆕 本流程产出 | 2/3 SOFT + 1/3 DROP |
| `Principles/debate_log_2026-XX-XX.md` | Markdown | 🆕 本流程产出 | 含 3-run voting 详情、follow-up agenda |
| `Principles/follow_up_agenda.md` | Markdown | 🆕 本流程产出 | 定量分歧的 "下届董事会讨论" 清单（v0.3 新增） |
| `Principles/critique_matrix_v1.1.jsonl` | JSONL | 🆕 本流程产出 | 每 cluster 的三维投票记录 |
| `Principles/company_data_contract.schema.json` | JSON Schema | 🔄 可能需要扩展 | 按 rule_subject=target 条款补字段；rule_subject=self 条款触发 portfolio_data schema 扩展 |

---

## 二、核心设计哲学

### 2.1 Rule Subject 三分法

```
┌──────────────────────────────────────────────────────────────┐
│  Rule Subject 分类（正交于原 category）                        │
├──────────────────────────────────────────────────────────────┤
│  target           │ 约束被投标的（公司/资产）                 │
│                   │ 例：ROIC<15%、商业模式不可解释            │
│                   │ 数据源：company_data.*                    │
│                   │                                            │
│  self             │ 约束投资机构 / 投资人自身                 │
│                   │ 例：不借贷、不做空、持有期≥10年、持仓≤10只│
│                   │ 数据源：portfolio_data.* + intent.*        │
│                   │                                            │
│  decision_process │ 约束分析流程本身（不约束公司也不约束投资人）│
│                   │ 例：质量先于价格顺序、反精确 DCF、反季报驱动│
│                   │ 数据源：analysis_trace.*                   │
└──────────────────────────────────────────────────────────────┘
```

**执行影响**：
- `target` 条款由 PrinciplesEngine 在读取 company_data 后触发
- `self` 条款由 Portfolio 层在 pre-trade 阶段触发
- `decision_process` 条款由 Agent 自审触发（Layer 1 自省 checkpoint）

三类条款共享同一个 `severity` 字段（veto/warning/note）和 `passed` 判定逻辑，但**检查点不同**。

### 2.2 Qualitative / Quantitative 双栈

每条 seed 必须**显式分离**两个部分：

| 层 | 字段 | 示例 |
|---|---|---|
| 定性 | `qualitative_claim` | "杠杆会放大永久性资本损失概率，是结构性风险" |
| 定量 | `quantitative_rule` | `{metric: debt_to_ebitda, op: ">", threshold: 3.0}` 或 null |

**定性一致但定量分歧**不再 DROP。改为：
1. Layer 0 取**最低共识阈值**（所有方都能接受的底线）
2. 更严的阈值进入 `follow_up_agenda`（下届董事会讨论是否收紧）

示例（持有期）：
```
定性一致：长期持有是价值投资核心。
定量分歧：Y=10年, C=5年, W=3年。
Layer 0 共识：≥3 年（最低共识）
Follow-up Agenda:
  - "持有期从 3 年升至 5 年" — 由 C 论证必要性
  - "持有期从 5 年升至 10 年" — 由 Y 论证必要性
```

### 2.3 大师自主结构化（非第三方后验抽取）

Phase 1 的 seed schema 强制每方**自行拆**：
- `qualitative_claim`（纯定性方向陈述，无数值）
- `quantitative_rule`（可机器执行的阈值规则）
- `rule_subject`（target / self / decision_process）
- `theme`（从预设 10 个主题中选 1-2）
- `severity`（veto / warning / note）
- `anti_scope`（本条不约束什么 — 避免被他方误读）

这样 Phase 2 的记录员只做**语义等价识别**（"A 的 claim 和 B 的 claim 说的是同一件事吗"），不做**定性抽取**（"A 实际上是在说什么"）。

---

## 三、修订后的流程总览

```
Phase 0   Soul Doc + Profile 索引（Python, 无 LLM）
  │
  ▼
Phase 1   三方独立结构化提案（3 并发 Sonnet call）
  │       ⭐ 强制新 seed schema: qual_claim + quant_rule 分离
  │       ⭐ 每方同时输出 positive seeds + anti_claims (Q10 待定)
  ▼
Phase 2   中立对照分析（1 Opus call, 3-run majority voting）
  │       ⭐ 3-run 一致率 < 2/3 的 stance 标记 low_confidence
  ▼
Phase 2.5 Revise 回合（3 并发 Sonnet call, 900s + 2 retry）
  │       动作：keep / modify / withdraw / new / endorse (Q10 待定)
  ▼
Phase 3a  语义聚类（1 Opus call, 仅做等价识别）
  │       按 (rule_subject, theme, category) 三维分组
  ▼
Phase 3b-qual  定性方向投票（3 并发, 2 轮上限）
  │       首轮 < 2/3 → 反对方看支持方 rationale 后再投 1 次
  ▼
Phase 3b-quant 定量阈值投票（3 并发, 1 轮）
  │       三值分布判定：同数量级 / 跨数量级 / subject 混淆
  │       计算最低共识 + 生成 follow-up agenda
  ▼
Phase 3b-sev   严重度投票（Q9 待定 — 多数决 or 取最严）
  │
  ▼
Phase 3c  汇总与渲染（Python，无 LLM）
  │       三层报告：L1 完全共识 / L2 定性共识定量分歧 / L3 定性分歧
  ▼
Phase 3d  人工 DROPPED 复审（Python 生成 review doc + 用户填写）
  │       输出 v1.1_dropped_review_candidates.md（LLM 打分排序）
  ▼
Phase E   合规扫描（Python regex，与 v0.2 一致）
```

---

## 四、各 Phase 详细规格

### Phase 0：Context Preparation

无 LLM。与 v0.2 一致。输出：
- `prep/soul_prompt_toc_{master}.json` — 章节标题 + keywords
- `prep/soul_index.json` — 全文索引供 RAG 检索
- `prep/soul_priority_sections.json` — 🆕 每个 master 标注 3-5 个**不可省略的核心 section**（如 Y 的"本分"、W 的"能力圈 Tier-1 铁律"、C 的"too hard pile"），Phase 1 提示词强制包含这些 section 的全文

### Phase 1：独立结构化提案

**模型**：`claude-sonnet-4-6`  
**并发**：3（W / C / Y 独立）  
**输入**：
- profile.json（该 master）
- soul_prompt_toc（该 master 章节索引）
- **soul_priority_sections 的全文**（🆕 Phase 0 预标注）
- prompt 模板（强合规 + 强结构化）

**输出 schema（v0.3 新版）**：

```jsonc
{
  "seed_id": "seed_01",
  "rule_subject": "target | self | decision_process",      // 🆕 必填
  "theme": "moat | capital_return | financial_strength | management_integrity | 
            valuation_method | behavioral_discipline | circle_of_competence | 
            portfolio_construction | accounting_quality | opportunity_cost",   // 🆕 必填，从预设 10 个选 1-2
  "category": "quantitative_hard | qualitative_required | veto_line | 
               valuation_method | position_sizing",        // 保留 v0.2

  "qualitative_claim": "...",                               // 🆕 必填，纯定性方向陈述，无数值
  "quantitative_rule": null | {                             // 可选，若为 null 即纯定性条款
    "metric": "...",
    "operator": "> | < | >= | <= | == | !=",
    "threshold": <number>,
    "data_field": "..."
  },
  "qualitative_rule": null | "...",                         // 可选，若 quantitative_rule 为 null 且需执行规则时填

  "severity": "veto | warning | note",

  "rationale": "...",                                       // 为什么这是方法论必需的
  "evidence_strength": "direct_quote | consistent_pattern | reasonable_inference",  // 🆕 Q11 待定
  "supporting_section_id": "soul/...",
  "supporting_profile_factor": "...",

  "anti_scope": "本条不约束 XXX",                          // 🆕 必填，避免他方误读
  "_master": "buffett | munger | duan"
}
```

**每个 master 还需额外输出 3-5 条 anti_claims**（🆕 Q10 待定）：
```jsonc
{
  "anti_claim": "本方法论明确反对：XXX",
  "conflicts_with_methodologies": ["technical_analysis", "macro_timing", ...],
  "rationale": "..."
}
```

**验收**：每方产出 8-20 条 seeds + 3-5 条 anti_claims；rule_subject 分布覆盖 ≥ 2 类。

### Phase 2：中立对照分析（3-run majority voting）⭐

**模型**：`claude-opus-4-7`  
**并发**：不并发（顺序跑 3 次，每次种子相同）  
**匿名映射**：W → random token, C → random token, Y → random token（每次 run 独立随机重排）

**输入**：所有 masters 的 seeds + anti_claims（匿名化）

**输出 per run**：对每条 seed 给出 stance：
```jsonc
{
  "seed_id": "X_seed_01",
  "framework": "X",  // 匿名标签
  "claim_normalized": "记录员对该 claim 的中立重述（不做定性抽取，只做去冗余）",
  "supported_by_frameworks": ["Y", "Z"],          // 哪些框架有直接同义 seed
  "supported_by_seed_ids": ["Y_seed_05", "Z_seed_11"],
  "conflicts_with_frameworks": [],                 // 哪些框架的 anti_claim 明确反对这条
  "conflicts_with_anti_claims": [],
  "compatible_but_unrelated_frameworks": ["..."],  // 🆕 v0.3 新增：方向不冲突也未显式覆盖
  "framework_specific_aspects": ["..."],
  "synthesis_note": "..."
}
```

**3-run 汇总**：
- 若 3 runs 对 `supported_by_frameworks` 给出一致集合 → `stance_confidence = high`
- 若 2/3 runs 一致 → 取多数，`stance_confidence = medium`  
- 若 3 runs 完全不同 → `stance_confidence = low`，标记人工复审

**验收**：
- 所有 seeds 有 stance
- `stance_confidence = high` 比例 ≥ 50%（v1.0 的 double-run 一致率才 20%，新目标降低到现实水平）
- `low` 置信 stances 进入 Phase 3d 人工复审清单

### Phase 2.5：Revise 回合

**模型**：`claude-sonnet-4-6`  
**并发**：3（W / C / Y 独立）  
**timeout**：900s  
**retry**：最多 2 次（总计 ≤ 3 次调用）；全部失败才 fallback 并在日志显著告警

**输入**：该 master 的原 seeds + Phase 2 comparative analysis（含 anti_claim 冲突识别）

**可做动作**：
- `keep` — 保留原 seed（默认）
- `modify` — 修订 claim / threshold / severity / rationale（必须填 rationale）
- `withdraw` — 撤回（本 master 不再持有该立场）
- `new` — 新增 seed（受其他方启发或补漏）
- `endorse` — 🆕 Q10 待定：明确支持其他 master 的某条 seed（不等于合并，但计票时该条 seed 的 supported_by 加上本 master）

### Phase 3a：语义聚类

**模型**：`claude-opus-4-7`（v1.0 用 Sonnet 跑不通才换的 Opus，这次继续 Opus）  
**timeout**：900s

**聚类规则**（v0.3 新版）：
1. **按 qualitative_claim 的语义等价聚类**（不是按原始 free-form claim）
2. 同 cluster 必须同 `rule_subject`（🆕 v0.3 新增硬性约束 — 防止 target 和 self 条款被错误合并）
3. 同 cluster 应同 `theme`；若 theme 不同但 qualitative_claim 等价，标 `theme_divergence=true` 交 Phase 3d 复审
4. `category` 差异允许（被 v1.0 cl_05/cl_06 拆分的教训纠正）
5. 每 cluster 保留所有 variant_seeds 的原 threshold / severity / category / _master

**输出**：`prep/phase3a_clusters_v1.1.jsonl`

### Phase 3b-qual：定性方向投票（2 轮上限）

**模型**：`claude-sonnet-4-6`  
**并发**：3（每 cluster，三方并发投票）

**第 1 轮输入**：每个 cluster 的 `canonical_qualitative_claim`（从 variant_seeds 中**选择最清晰的原话**，而非 Opus 抽取）

**每方输出**：
```jsonc
{
  "cluster_id": "cl_01",
  "stance": "support | oppose | abstain",
  "rationale": "...",
  "preferred_phrasing": "我方建议的 claim 措辞" | null
}
```

**判定**：
- 3/3 support → 进 Phase 3b-quant
- 2/3 support + 0 oppose → 进 Phase 3b-quant
- 2/3 support + 1 oppose → 进**第 2 轮**：oppose 方看另两方的 rationale 后再投一次
- < 2/3 support → DROP 到 soul-level-preferences.md

**第 2 轮**（仅当首轮 2/3 support + 1 oppose 时触发）：
- 将首轮 support 方的 rationale 发给 oppose 方
- oppose 方可改投 support / abstain，或继续 oppose
- 结果：3/3 或 2+1 abstain → 过；仍 1 oppose → DROP（该 master 实质否决）

### Phase 3b-quant：定量阈值投票

**触发条件**：定性投票通过（Phase 3b-qual 过的 cluster 才进入本 phase）

**模型**：`claude-sonnet-4-6`  
**并发**：3

**每方输入**：该 cluster 的 canonical_qualitative_claim + 三方原 variant thresholds（已 merged 的 seeds 里的原值）

**每方输出**：
```jsonc
{
  "cluster_id": "cl_01",
  "proposed_threshold": <number> | null,
  "proposed_operator": ">|<|>=|<=|==",
  "proposed_severity": "veto | warning | note",
  "rationale": "...",
  "would_accept_looser": <number> | null,        // 🆕 最低可接受（spectrum 下界）
  "would_accept_stricter": <number> | null,      // 🆕 最严可接受（spectrum 上界）
  "direction_preference": "stricter | looser | neutral"  // 🆕 倾向
}
```

**后处理（Python，不调 LLM）**：

令三方阈值为 `[T_a, T_b, T_c]`（按方向排序）。

**模式 1：数值同数量级**（max/min < 3）  
→ `Layer 0 threshold = 最低共识值`（例：10/5/3 年，取 ≥ 3 年）  
→ `variant_thresholds_by_master = {...}`  
→ `follow_up_agenda`: 生成 "X → Y" 升级讨论（例：3→5 由谁论证；5→10 由谁论证）

**模式 2：数值跨数量级**（max/min ≥ 3）  
→ 检查 `would_accept_looser` 是否收敛到同数量级  
→ 若 yes：按模式 1 处理，用 `would_accept_looser` 值  
→ 若 no：**标记 `needs_subject_split`** — 通常是 subject 混淆（例：投资人杠杆 0% / 公司杠杆 3x / 金融机构杠杆 25x）。进入 Phase 3d 人工复审，建议拆子议题

**模式 3：方向不一致**（部分方要 `>`, 部分要 `<`）  
→ 实质定性分歧（一方要拦截高值，一方要拦截低值）  
→ 降级到 SOFT 或 DROP（Phase 3d 复审决定）

### Phase 3b-sev：严重度投票 [Q9 待定]

**[OPEN - awaiting Q9 sign-off]** — 两种方案可选：

**方案 A（v1.0 默认）**：取最严（veto > warning > note），无投票。

**方案 B（v0.3 推荐）**：每方给 severity proposal → 多数决：
- 3/3 一致 → 采纳
- 2/3 一致 → 采纳多数值
- 三方全异（如 veto/warning/note 各一）→ **取中位 warning** 且列入 follow_up_agenda

### Phase 3c：汇总与渲染（Python）

**无 LLM**。按三维投票结果生成三层报告：

| 层 | 条件 | 输出位置 |
|---|---|---|
| **L1 完全共识** | 定性 3/3 + 定量同数量级 + 严重度一致 | `Principles/v1.1.md` HARD 区 |
| **L2 方向共识** | 定性 3/3 或 2/3 + 定量分歧但有最低共识 | `Principles/v1.1.md` HARD with variants 区，+ `follow_up_agenda.md` |
| **L3 定性分歧** | 定性 < 2/3 | `Principles/soul-level-preferences-v1.1.md` |

每层按 `rule_subject` 分三节（target / self / decision_process）。

### Phase 3d：人工 DROPPED 复审

**模型**：`claude-sonnet-4-6`（打分用）  
**输入**：所有 DROPPED 和 low_confidence 的 seeds/clusters

**输出**：`Principles/v1.1_dropped_review_candidates.md`

每条 candidate 附：
- 原 claim + 原 master
- `cross_method_value_score` 0-10（LLM 评估"其他两方方法论里是否潜在认同"）
- `suggested_action`: 升 HARD / 升 SOFT / 保持 DROP
- 用户 Y/N + rationale 填写位

用户手工 review 后，填写的 markdown 被 parsing 后生效。

### Phase E：合规扫描

与 v0.2 一致。扫描所有 Phase 1-3 中间产出 + 最终 Principles。regex 禁止模式：
- `你是 (Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格)`
- `(保持|keep).*(风格|口吻|personality|voice)` + master 名
- 其他见 `Designs/prompt-framing-guidelines.md`

🆕 v0.3 **额外扫描**：`principles_synthesizer.py` 的 prompt 文本（防止 v1.0 那次 "W/C/Y — 分别对应 buffett/munger/duan" 的 de-anonymization 再次发生）。

---

## 五、新 Seed Schema 完整定义

见 `Principles/seed_schema_v1.1.json`（本流程实施时创建）。以下为核心字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| seed_id | string | ✅ | 本 master 内唯一 |
| rule_subject | enum{target, self, decision_process} | ✅ 🆕 | 约束对象 |
| theme | enum[10 themes] | ✅ 🆕 | 主题分组 |
| category | enum{5 categories} | ✅ | 保留 v0.2 |
| qualitative_claim | string | ✅ 🆕 | 纯定性方向陈述，无数值 |
| quantitative_rule | object \| null | ⚠️ | 与 qualitative_rule 至少一个非 null |
| qualitative_rule | string \| null | ⚠️ | 机器可执行的定性规则 |
| severity | enum{veto, warning, note} | ✅ | |
| rationale | string | ✅ | 为什么是方法论必需 |
| evidence_strength | enum{direct_quote, consistent_pattern, reasonable_inference} | ✅ 🆕 [Q11 待定] | |
| anti_scope | string | ✅ 🆕 | 本条不约束什么 |
| supporting_section_id | string | ✅ | soul doc anchor |
| supporting_profile_factor | string | ✅ | profile.json factor |
| _master | enum{buffett, munger, duan} | ✅ | 内部字段 |

**额外 anti_claims schema**（Q10 待定）：
| 字段 | 类型 | 必填 |
|---|---|---|
| anti_claim | string | ✅ |
| rule_subject | enum{3} | ✅ |
| conflicts_with_methodologies | string[] | ✅ |
| rationale | string | ✅ |

---

## 六、三层汇总报告模板

### L1 完全共识（HARD）

按 rule_subject 分三节：

```markdown
## HARD - Target 约束（约束被投标的）

### T-1. <canonical qualitative_claim>
- Cluster ID: cl_01
- Theme: moat
- Category: qualitative_required
- Severity: veto (3/3 一致)
- Threshold: <单一共识值>
- Supported by: W, C, Y (3/3 support)
- Stance Confidence: high (3-run majority)
- Evidence Sources: ...
```

### L2 方向共识（HARD with variants）

```markdown
## HARD with Variants - Self 约束

### S-3. <canonical qualitative_claim>
- Cluster ID: cl_11
- Theme: behavioral_discipline  
- Category: position_sizing
- Severity: warning (3/3 一致)
- **Layer 0 Threshold**: ≥ 3 年（最低共识）
- Variant Thresholds by Master: {Y: 10, C: 5, W: 3}
- Supported by: W, C, Y (3/3 support 定性; 定量分歧)
- **Follow-up Agenda**:
  - 由 C 下届论证：持有期 3 → 5 年的必要性
  - 由 Y 下届论证：持有期 5 → 10 年的必要性
```

### L3 定性分歧（soul-level）

```markdown
## Soul-Level Preferences

### SL-7. <claim>
- Original Master: Y
- Voting Result: 1/3 support (W: oppose, C: abstain)
- Reason Dropped: W 方法论明确支持 [X] 与本条冲突（见 W 的 anti_claim #3）
- Retention Reason: Y 方法论保留此偏好用于 Layer 1 Agent 参考
```

---

## 七、Open Questions（待 sign-off）

| Q | 议题 | 当前默认 | 待确认 |
|---|---|---|---|
| Q9 | 严重度投票机制 | 取最严（v1.0 默认） | 多数决 or 取最严？ |
| Q10 | Phase 1 是否加 anti_claims | 推荐加 | 加 / 不加 |
| Q11 | Seed 加 evidence_strength 字段 | 推荐加 | 加 / 不加 |
| Q12 | 用户对 HARD 有 sign-off veto 权 | 推荐有 | 有 / 无 |

Q4（v1.1 全量重跑 vs 增量补丁）、Q5（v1.1 升级时序）、Q6（Phase 3d 落地形式）已由用户推迟到设计讨论清楚后再定。

---

## 八、时间 / 成本预算（预估）

| Phase | LLM calls | 并发 | 预计时间 |
|---|---|---|---|
| Phase 0 (Python) | 0 | - | < 1 min |
| Phase 1 (3 seeds + anti) | 3 | yes | 10-15 min |
| Phase 2 (3-run Opus) | 3 | no (顺序) | 15-25 min |
| Phase 2.5 (revise + retry) | 3-9 | yes | 10-20 min |
| Phase 3a (clustering) | 1 | - | 5-10 min |
| Phase 3b-qual (2 轮上限) | 3-6 | yes | 5-10 min |
| Phase 3b-quant | 3 | yes | 3-5 min |
| Phase 3b-sev (Q9) | 0-3 | yes | 0-3 min |
| Phase 3c (Python) | 0 | - | < 1 min |
| Phase 3d (scoring) | 1 | - | 3-5 min |
| Phase E (scan) | 0 | - | < 1 min |
| **合计 LLM** | **17-28 calls** | | **50-85 min** |

相比 v0.2 的 9 calls / 25-40 min，v0.3 约 **2-3 倍**成本，换来：
- 3-run 代替 double-run 降低 stance 噪声
- 定性/定量/严重度三维投票提升共识粒度
- Retry 机制避免 v1.0 那次 C 超时丢失修订的悲剧

---

## 九、风险矩阵（v0.3 新增）

| 风险 | 概率 | 缓解 |
|---|---|---|
| 新 schema 过于复杂，Phase 1 LLM 无法稳定输出合规 JSON | 中 | Phase 1 prompt 附完整示例 × 3（每个 rule_subject 类型一个） + JSON Schema 自动校验 + 失败 retry |
| `qualitative_claim` 由大师自写但仍暗含数值（污染定性层） | 中 | Phase 1 prompt 明文禁止 qualitative_claim 中出现数字；Phase E 扫描补这条正则 |
| Phase 3a 聚类按 qualitative_claim 等价识别失准（漏合并或错合并） | 中 | 保留 Phase 3d 人工复审；聚类 prompt 要求 Opus 输出 `merge_confidence` |
| 3-run Opus 仍高度不一致 (< 50% high confidence) | 低 | 降级判定到 medium confidence 接受 + 扩大 Phase 3d 复审范围 |
| Follow-up agenda 积累过多而不 review | 中 | v1.1 生效后每季度强制 review agenda，升级或 drop |
| Subject 三分仍有边界模糊（如"管理层 X"既 target 也 decision_process） | 中 | Phase 3a 的 subject 一致性约束放宽到 "主导 subject"，次要 subject 以 `secondary_subjects` 字段记录 |

---

## 十、执行前置条件

本流程**不立即执行**。前置：
1. ✅ 用户 sign-off Q9-Q12
2. ⏳ 用户决定 Q4/Q5/Q6（v1.1 升级时序与产出形式）
3. ⏳ 实施代码：
   - `scripts/soul/board_debate_v2.py`（主调度）
   - `scripts/soul/principles_synthesizer_v2.py`（Phase 3a-3d）
   - `scripts/soul/compliance_scan.py` 升级（加 Phase 1 "qualitative_claim 含数字" 规则）
4. ⏳ 准备新 prompt 模板（Phase 1 / 2 / 2.5 / 3a / 3b-qual / 3b-quant / 3b-sev）
5. ⏳ Seed schema 校验器（JSON Schema draft-07）

实施前再做一次 adversarial review（像 v0.1 → v0.2 那次）。

---

## 十一、与 v1.0 的兼容性

- `Principles/v1.0.md` 保留不动
- v1.1 生效后，`Principles/current.md` symlink 指向 v1.1.md
- v1.0.schema.json 的字段子集依然兼容 v1.1.schema.json（v1.1 只新增字段、不破坏原有）
- MVP PrinciplesEngine 同时支持 v1.0 和 v1.1 schema 加载（版本参数化）

---

## 十二、Changelog vs v0.2

| 变化点 | v0.2 | v0.3 |
|---|---|---|
| rule_subject 维度 | 无 | ✅ 三分（target/self/decision_process） |
| Phase 1 seed schema | free-form claim | 结构化 qualitative_claim + quantitative_rule 分离 |
| anti_claims | 无 | ✅ (Q10 待定) |
| evidence_strength | 无 | ✅ (Q11 待定) |
| Phase 2 run 次数 | 2 (double) | 3 (triple majority) |
| Phase 2.5 timeout | 540s 单次 | 900s + 2 retry |
| 定性/定量投票 | 合一 | 拆为三阶段 (qual + quant + sev) |
| 最低共识 + Follow-up | 无（variants 并列） | ✅ Layer 0 取最低共识 + 升级议题入 agenda |
| 严重度投票 | 取最严 | 多数决 (Q9 待定) |
| 人工复审 | 无 | ✅ Phase 3d |
| 预算 | 9 calls / 25-40 min | 17-28 calls / 50-85 min |
