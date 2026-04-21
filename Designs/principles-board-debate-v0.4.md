# Pre-A: Principles Board Debate — 设计 v0.4（完全自治 routine 版）

> 状态：**草案，等待 adversarial review 和实施 sign-off**
> 日期：2026-04-21
> 版本：v0.4
> 取代：`Designs/principles-board-debate-v0.3.md`（留档）
> 依赖：v1.0 执行教训 + v0.3 机制设计 + 2026-04-21 深度讨论

---

## 零、一页 Executive Summary

### 产品设计底层原则（贯穿全文）

> **产品设计者（Primus）不参与具体原则决策。**
> - Primus 的角色 = 机制 / 流程 / schema / 触发条件 / routine 的设计者
> - Primus **不做**：不投票、不 veto、不审批具体条款、不 override HARD、不手动升降级 DROPPED
> - 三位方法论研究助手（W / C / Y）是**唯一的原则决策者**
> - 全流程目标：**自动化**完成"发现 → 分析 → 讨论 → 决策 → 生效 → 定期重审"闭环

v0.4 相比 v0.3 的**核心变化**全部服务于上面这条原则：

| v0.3 残留的"用户介入"或机制缺失 | v0.4 对应修法 |
|---|---|
| Phase 3d 人工 DROPPED 复审 | ❌ 删除。DROPPED 条款每次新一轮 debate 自动重入池；连续 3 轮 < 2/3 支持才真归档 |
| v1.0.md 要求"用户 sign-off Layer 0 激活" | ❌ 删除。流程跑完即生效，`Principles/current.md` 自动 symlink 到最新 HARD |
| Follow-up agenda 的 review 主体未明 | ✅ 每季度自动触发 mini-debate，三方对 agenda 条目重新投票 |
| 何时触发新一轮 debate 没有机制 | ✅ 新增 `Phase -1: Trigger Detection`，4 种自动触发条件 |
| DROPPED 条款永久归档，没有复活通道 | ✅ 每轮 Phase 1 每方可 re-introduce 历史 DROPPED 1-3 条（附 soul doc 变化 rationale） |
| Severity "取最严"对提 veto 方倾斜 | ✅ Severity 是 seed 属性，不是投票维度。同 qualitative_claim 但不同 severity 聚合为 cluster variants；Layer 0 取**最低共识**（最轻的严重度），升级诉求入 follow-up agenda |
| 流程本身如何演化没有机制 | ✅ 大师在 Phase 2.5 可额外提交 `process_critique` 到 `prep/process_critique.jsonl`，供 Primus 设计 v0.5 时参考 |

---

## 一、产出物

| 文件 | 格式 | 生成方 | 说明 |
|---|---|---|---|
| `Principles/v{N}.md` | Markdown | 自动 | 按 `rule_subject` 分三节的 HARD 条款（N 自动递增） |
| `Principles/v{N}.schema.json` | JSON Schema | 自动 | 机器可执行版 |
| `Principles/soul-level-preferences-v{N}.md` | Markdown | 自动 | SOFT + 1/3 支持条款 |
| `Principles/dropped-archive.md` | Markdown | 自动（累积） | 连续 3 轮 < 2/3 支持的真归档条款 |
| `Principles/debate_log_{date}_{trigger}.md` | Markdown | 自动（每轮 1 份） | 每次触发的完整会议纪要 |
| `Principles/follow_up_agenda.md` | Markdown | 自动（累积） | 定量 / 严重度分歧的遗留议题 |
| `Principles/critique_matrix_v{N}.jsonl` | JSONL | 自动 | 三维投票记录 |
| `Principles/current.md` | symlink | 自动 | 指向最新 HARD 版本 |
| `Principles/company_data_contract.schema.json` | JSON Schema | 自动（按需扩展） | `target` 条款的 company_data 字段 |
| `Principles/portfolio_data_contract.schema.json` | JSON Schema | 自动（按需扩展） 🆕 | `self` 条款的 portfolio_data 字段 |
| `prep/process_critique.jsonl` | JSONL | 自动（累积） 🆕 | 大师对辩论流程本身的建议 |

**⚠️ Primus 只在一个地方"sign-off"**：设计文档的迭代（v0.4 → v0.5）。其他一切自动。

---

## 二、核心设计哲学

### 2.1 Rule Subject 三分（同 v0.3）

```
target           约束被投标的（公司 / 资产）
                 数据源：company_data.*
                 
self             约束投资机构 / 投资人自身
                 数据源：portfolio_data.* + intent.*
                 
decision_process 约束分析流程本身
                 数据源：analysis_trace.*
```

同 cluster 必须同 rule_subject（硬约束，防 target/self 条款被错合并）。C9 机制缓解错标：Phase 2 后 Opus 提示 rule_subject 可能错标的 seeds，对应 master 可在 Phase 2.5 调整。

### 2.2 Qualitative / Quantitative / Severity 三维分离（v0.4 确定稿）

每条 seed 显式携带三个正交属性：
- `qualitative_claim` — 纯定性方向陈述（无数值，无严重度副词）
- `quantitative_rule` — 数值阈值规则（可为 null，即纯定性条款）
- `severity` — veto / warning / note

**聚类规则**：
1. 同 `(rule_subject, qualitative_claim 语义等价)` → 合并为 cluster
2. 同 cluster 内不同 quantitative_rule / severity / category 作为**三维 variants** 并列记录
3. Phase 3b 投票时定性先投；通过后定量和严重度分别求最低共识

**最低共识定义**：
- **定量**（数值）：三方阈值中**最宽松的共识下界**。例：持有期 Y=10 / W=3 / C=5 → 共识 ≥ 3
- **严重度**（veto > warning > note）：三方 severity 中**最轻的**。例：Y=veto, W=warning, C=note → Layer 0 取 note
- 更严格的阈值 / 更高的严重度 → 入 `follow_up_agenda`，下届由提议方论证

**为什么是"取最轻"而不是"取最严"**：
- 这是价值投资**真共识的底线**，不是某一方的偏好强加给其他方
- Y 要 veto 但 W/C 只到 note → Y 没说服其他两方 → Y 的 veto 不是共识，但三方都同意至少要"记录"这件事 → note 是共识底线
- 更严格的版本进 agenda，Y 下次可以补证据再辩论收紧

### 2.3 大师自主结构化（非第三方后验抽取）

Phase 1 的 seed schema 强制每方自行拆：
- `qualitative_claim` / `quantitative_rule` / `severity` / `rule_subject` / `theme` / `anti_scope`
- Opus 在 Phase 2/3a 只做**语义等价识别**，不做**定性抽取**

### 2.4 Seed 原子性约束 🆕 C10

一条 seed = 一个观点。**禁止复合 claim**（如"不反对研究公司但反对研究宏观"应拆两条）。执行：
- Phase 1 prompt 附正反例 + 明文禁令
- Phase E 扫描 regex：`既.*又 | 不.*但 | 同意.*但反对 | 在.*同时还要求`
- Phase 1 输出后的 JSON validator 检查 qualitative_claim 是否含复合句式连接词

### 2.5 anti_scope 保留（非 anti_claim）🆕 C11

每条 seed 自带 `anti_scope`（本条不约束什么）作为作用域澄清，不是"第二个观点"。例：
- cl_02 claim: "ROIC < 15% → warning"
- anti_scope: "本条不适用于银行、保险等结构性高杠杆行业"

不引入独立的 anti_claims 列表（v0.3 Q10 已否决）。

---

## 三、完整流程总览（v0.4 新增 Phase -1 和 routine 机制）

```
┌──────────────────────────────────────────────────────────────┐
│ Phase -1: Trigger Detection (Python, 无 LLM, cron 驱动)      │ 🆕
│   检查 4 种触发条件，决定是否跑 debate 以及跑什么类型         │
└──────────────────┬───────────────────────────────────────────┘
                   │ 若无触发，exit；若有，按类型分发
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 0: Context Preparation (Python)                         │
│  - Soul doc 索引（按 H2/H3 切块 + keywords）                  │
│  - soul_priority_sections 自动识别（Sonnet 扫打分）🆕 B6      │
│  - 读取 current Principles + follow_up_agenda + dropped-archive │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 1: 三方独立结构化提案 (3 并发 Sonnet)                   │
│  ⭐ 强制 seed schema: qual_claim + quant_rule + severity 分离  │
│  ⭐ 允许每方 re-introduce 历史 DROPPED 1-3 条 🆕 B5            │
│  ⭐ 每条 seed 必须通过原子性校验 🆕 C10                        │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 2: 3-run Majority Voting (3 Opus calls, 顺序)          │
│  ⭐ 匿名化 A/B/C 每次 run 独立随机重排                         │
│  ⭐ 每个 framework 对每 seed 的支持判定独立取 2/3 多数 🆕 C7    │
│  输出: stance + stance_confidence (high/medium/low)           │
│  + 🆕 C9 rule_subject 一致性提示 (不强制)                      │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 2.5: Revise Round (3 并发 Sonnet, 900s + 2 retry)      │
│  每方动作: keep / modify / withdraw / new                     │
│  + 🆕 E12 可额外提交 process_critique                          │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3a: 语义聚类 (1 Opus call)                              │
│  按 (rule_subject, qualitative_claim 等价) 聚类               │
│  同 cluster 保留 quant/severity/category 三维 variants       │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3b-qual: 定性方向投票 (≤ 2 轮, 3 并发 Sonnet)          │
│  首轮 < 2/3 support + 1 oppose → 第 2 轮 oppose 方复审        │
│  < 2/3 → 进 DROPPED (但不立即归档, 进入 3 轮滑动窗口)         │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3b-quant: 定量阈值投票 (3 并发 Sonnet)                  │
│  三值模式判定 → Layer 0 取最低共识 + follow_up_agenda         │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3b-sev: 严重度汇总 (Python, 无 LLM)                     │
│  severity 作为 cluster variants → Layer 0 取最轻共识          │
│  升级诉求自动生成 follow_up_agenda 条目                       │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3c: 汇总渲染 (Python, 无 LLM)                           │
│  - 更新 Principles/v{N}.md, schema.json                       │
│  - 更新 soul-level-preferences                                │
│  - 更新 follow_up_agenda.md (追加)                            │
│  - 更新 dropped-archive.md (归档连续 3 轮 DROP 条款)          │
│  - 自动 symlink Principles/current.md → v{N}.md 🆕 A2         │
└──────────────────┬───────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase E: 合规扫描 (Python regex)                              │
│  扫描 身份扮演 / qualitative_claim 含数字 / seed 复合性       │
│  违规 → 自动重跑对应 Phase，不交人工                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、Phase -1: Trigger Detection 详细规格 🆕 B4

**实现**：`scripts/soul/trigger_detector.py` + crontab 或 systemd timer

**4 种触发条件**：

### T1. 定时触发（每季度）
- crontab 每季度第 1 日凌晨跑
- 类型 = `quarterly_follow_up_review`
- 范围：仅对 `follow_up_agenda.md` 条目跑 mini-debate（Phase 1 输入集限定为 agenda 条目）
- 如果 agenda 为空 → 自动 skip，不触发

### T2. Soul Doc 版本触发
- 监听 `src/souls/documents/current/{W,C}.md` 和 `src/souls/documents/Y-duan-soul-v*.md` 的 semver 变化
- Minor+ bump（1.1 → 1.2 或 1.x → 2.0）→ 触发
- 类型 = `soul_doc_update_full_rerun`
- 范围：完整 debate（Phase 1 重跑全量，不限定输入集）

### T3. 实战信号触发
- 监听 MVP 执行日志 `~/.valueinvestor/decisions.jsonl`
- 某条 HARD 被 Layer 1 Agent 标记 `request_override` ≥ 3 次（在 30 天滑动窗口内）→ 触发
- 类型 = `field_signal_rule_contention`
- 范围：仅对被标 override 的条款及其语义相邻条款跑 mini-debate

### T4. Agenda 积累触发
- follow_up_agenda.md 条目累计 ≥ 10 条且距上次 quarterly_follow_up_review ≥ 30 天 → 触发
- 类型 = `agenda_overflow_mini_debate`
- 范围：agenda 全量 + 可能的语义关联条款

**触发互斥**：同一日多个条件同时满足时按优先级 T2 > T3 > T4 > T1 选一个（避免重复 debate 浪费算力）。

**触发记录**：每次触发写 `prep/trigger_log.jsonl`，包含 trigger type / timestamp / scope / downstream debate_log 引用。

---

## 五、DROPPED 条款的滑动窗口机制 🆕 A1 + B5

### 5.1 每轮 Phase 1 的 re-introduction 权限

每位 master 在 Phase 1 草拟 positive seeds 的同时，**最多可从 `dropped-archive.md` 或 `soul-level-preferences-v{N-1}.md` 中 re-introduce 1-3 条**。

每条 re-introduced seed 需额外填：
```jsonc
{
  "_reintroduced_from": "cl_26 (v1.0 DROPPED)",
  "_reintroduction_rationale": "W soul doc v1.2 新增 '资本保全优先级' 章节，与本条原意对齐，值得重新辩论"
}
```

Phase 3a 聚类时，re-introduced seed 与新 seed 同等处理（不享受"上次已经辩论过就不用再辩"的豁免）。

### 5.2 DROPPED 条款的 3 轮滑动窗口

一条 cluster 在某轮 Phase 3b-qual 投票 < 2/3 support → **进 DROPPED**，但不立即归档。

追加一条 metadata：
```jsonc
{
  "cluster_id": "cl_27",
  "_drop_history": [
    {"debate_id": "2026-04-20_initial", "support_count": 1},
    {"debate_id": "2026-07-01_quarterly_review", "support_count": 1}
  ]
}
```

- 若未来某轮重新 ≥ 2/3 support → 升入 SOFT 或 HARD（按新结果），清空 _drop_history
- 若连续 3 轮（跨 debates）均 < 2/3 support → 真归档到 `dropped-archive.md`，不再自动进下一轮
- 归档后仍可被 re-introduce（§5.1），但每方每轮最多 3 条的限额内

---

## 六、三层汇总与 Follow-up Agenda 🆕 A3

### 6.1 三层汇总（输出位置）

| 层 | 条件 | 输出位置 |
|---|---|---|
| **L1** 完全共识 | qual 3/3 ∧ quant 单一共识 ∧ severity 单一 | `Principles/v{N}.md` HARD 区 |
| **L2** 方向共识 | qual ≥ 2.5/3 ∧（quant 有最低共识 ∨ severity 有最低共识） | `Principles/v{N}.md` HARD with variants 区 |
| **L3** 定性分歧 | qual < 2/3 | `soul-level-preferences-v{N}.md` (带 _drop_history) |

### 6.2 Follow-up Agenda 生成规则

每个 L2 条款自动生成 0-2 条 agenda item：

**定量升级 item**（若 quant variants 存在）：
```markdown
### Agenda: cl_10 持有期
- Current Layer 0: ≥ 3 年（最低共识）
- Proposed upgrades:
  - "3 → 5 年" by C (rationale: ...)
  - "5 → 10 年" by Y (rationale: ...)
- Next review: 2026-07-01 quarterly_follow_up_review
```

**严重度升级 item**（若 severity variants 存在）：
```markdown
### Agenda: cl_02 ROIC<15%
- Current Layer 0 severity: warning
- Proposed upgrades:
  - "warning → veto" by Y (rationale: ROIC<15% 公司无法支撑好生意定义)
- Next review: ...
```

### 6.3 Agenda 条目的生命周期

- 被 T1 / T4 触发的 mini-debate 处理后：
  - 三方达成新共识 → 条目 resolve（从 agenda 移除）
  - 仍分歧 → 条目 stale，保留但标记连续 N 季度未收敛
  - 连续 4 季度（一年）未收敛 → 自动降级为"各方永久偏好差异"，从 agenda 移至 `soul-level-preferences.md` 底部"永久分歧"区

---

## 七、Seed Schema（v0.4 最终版）

```jsonc
{
  // ─── 标识 ───
  "seed_id": "seed_01",
  "_master": "buffett | munger | duan",

  // ─── 分类维度（v0.4 强制） ───
  "rule_subject": "target | self | decision_process",
  "theme": "moat | capital_return | financial_strength | management_integrity | 
            valuation_method | behavioral_discipline | circle_of_competence | 
            portfolio_construction | accounting_quality | opportunity_cost",
  "category": "quantitative_hard | qualitative_required | veto_line | 
               valuation_method | position_sizing",

  // ─── 核心内容（三维分离） ───
  "qualitative_claim": "<纯定性方向陈述，无数值，无严重度副词，一个观点>",
  "quantitative_rule": null | {
    "metric": "...",
    "operator": "> | < | >= | <= | == | !=",
    "threshold": <number>,
    "data_field": "company_data.* | portfolio_data.* | analysis_trace.*"
  },
  "qualitative_rule": null | "<可机器执行的定性规则, 当 quantitative_rule 为 null 时填>",
  "severity": "veto | warning | note",

  // ─── 作用域 + 元信息 ───
  "anti_scope": "<本条不约束什么, v0.4 必填>",
  "rationale": "<为什么是方法论必需>",
  "evidence_strength": "direct_quote | consistent_pattern | reasonable_inference",
  "supporting_section_id": "soul/...",
  "supporting_profile_factor": "...",

  // ─── 可选: 历史 re-introduction ───
  "_reintroduced_from": null | "<cluster_id> (vX DROPPED)",
  "_reintroduction_rationale": null | "<soul doc 新变化说明>"
}
```

**JSON Schema validator**（`scripts/soul/seed_schema_v1.1.json`）在 Phase 1 输出后强制校验。失败的 seed 交还该 master 重写（retry 最多 2 次）。

---

## 八、关键 Prompt 合规要求（全流程）

### Phase 1 prompt 模板关键要求

```
你是价值投资方法论研究助手，基于下列 soul doc + profile 为 {framework_id} 框架
提炼 principle seeds。你不是大师本人，不要扮演大师口吻。

【硬性要求】
1. 每条 seed 是一个原子观点，禁止复合 claim
2. qualitative_claim 必须为纯定性陈述，禁止出现数字、百分号、年限
3. 若观点涉及阈值，阈值放在 quantitative_rule.threshold；qualitative_claim 只描述方向
4. 每条 seed 必须自行决定 rule_subject / theme / severity / anti_scope
5. 若观点是"反对 X"，qualitative_claim 直接写"反对 X"，不要写"不反对 Y"

【示例 — 正确】
{
  "qualitative_claim": "长期资本回报率低于基准线时反映业务质量不足",
  "quantitative_rule": {"metric": "roic_10yr_avg", "operator": "<", "threshold": 0.15, ...},
  "severity": "warning",
  "anti_scope": "本条不适用于银行、保险等结构性高杠杆行业",
  ...
}

【示例 — 错误（复合 claim）】
{
  "qualitative_claim": "资本回报率低于 15% 的公司不值得投资，除非管理层优秀",
  //           ^^ 含数字 ^^                            ^^ 第二个观点 ^^
}
```

### Phase 2 prompt 模板关键要求
- 匿名化 A/B/C（每次 run 独立重排）
- 不 de-anonymize（不出现 buffett / munger / duan 名称）
- 输出结构化 stance，不做定性抽取，只做语义等价识别

### Phase 3a prompt 关键要求
- 聚类按 (rule_subject, qualitative_claim 等价) 进行
- 同 cluster 的 variants（quant / severity / category）**全部保留**，不做"取最严"的合并
- 不 de-anonymize

**v0.4 合规扫描新增规则**：
- `principles_synthesizer.py` 等 Phase 3 脚本的 prompt 文本也纳入 Phase E 扫描（v1.0 曾出现 "W/C/Y 分别对应 buffett/munger/duan" 的 de-anon）

---

## 九、Process Critique 机制 🆕 E12

Phase 2.5 修订回合，每方可选地提交 `process_critique` 条目：

```jsonc
{
  "critiquing_master": "buffett",
  "critique_type": "rule_clarification_needed | phase_design_issue | 
                    schema_limitation | conflict_resolution_gap | other",
  "critique_content": "<对当前辩论流程/规则的具体建议>",
  "proposed_fix": "<该 master 建议的修法 (optional)>"
}
```

汇总到 `prep/process_critique.jsonl`。**Primus 是该文件的唯一消费者** — 定期（每 2-3 轮 debate）review 一次，据此决定是否需要升级到 v0.5 设计。

大师的 process_critique **不影响本轮原则投票结果**（严格分离流程层和内容层）。

---

## 十、时间 / 成本预算

| Phase | LLM calls | 并发 | 预计时间 |
|---|---|---|---|
| Phase -1 (trigger) | 0 | - | < 1 s |
| Phase 0 (含 priority_sections 自动识别) | 3 | yes | 2-3 min |
| Phase 1 (含 re-introduction) | 3 | yes | 10-15 min |
| Phase 2 (3-run majority) | 3 | no | 15-25 min |
| Phase 2.5 (含 process_critique) | 3-9 (含 retry) | yes | 10-20 min |
| Phase 3a | 1 | - | 5-10 min |
| Phase 3b-qual (≤ 2 轮) | 3-6 | yes | 5-10 min |
| Phase 3b-quant | 3 | yes | 3-5 min |
| Phase 3b-sev | 0 | - | < 1 min |
| Phase 3c (渲染) | 0 | - | < 1 min |
| Phase E | 0 | - | < 1 min |
| **Full debate 合计** | **19-28 calls** | | **50-90 min** |

**Mini-debate 预算**（T1/T3/T4 触发）：
- Phase 1 输入集小 → Phase 1 / 2 / 3 各缩小 30-50%
- 合计 ~10-15 calls / 25-40 min

**全年成本估算**（$5 / opus call + $1 / sonnet call 近似）：
- 2 次 full debate（soul doc update） × $25 = $50
- 4 次 quarterly mini-debate × $12 = $48
- 偶发实战信号 / agenda overflow × 2 × $15 = $30
- **全年 ≤ $130**

---

## 十一、风险矩阵

| 风险 | 概率 | 缓解 |
|---|---|---|
| Phase 1 LLM 无法稳定输出合规 JSON | 中 | JSON Schema validator + 2 次 retry + 完整示例注入 prompt |
| qualitative_claim 暗含数字 | 中 | Phase E regex + Phase 1 prompt 正反例 |
| 3-run Opus 仍 < 50% high_confidence | 低 | 降级到 medium 接受；low 条款自动进下轮 re-debate |
| 严重度全部投 "note" 导致 Layer 0 无硬约束 | 中 | 接受（符合"最低共识"哲学）；升级诉求积累到 agenda，下届再辩 |
| T3 实战信号误触（Agent 频繁 request_override 非因 rule 错，而因 Agent 本身漂移） | 中 | request_override 阈值设 3 次且 30 天窗口；触发后的 mini-debate 若三方仍 2/3+ 支持原规则，则锁定 180 天不再因同 trigger 重跑 |
| DROPPED 条款的 _drop_history 无限增长 | 低 | 真归档到 `dropped-archive.md` 后不再计入 history，清空 |
| Follow-up agenda 条目永远不收敛 | 中 | 连续 4 季度无进展自动降级"永久分歧"区 |
| Soul doc 外部更新未通过 Git commit（无法触发 T2） | 低 | Phase -1 改用文件 mtime + content hash 双重检测 |
| Routine 自动跑时 LLM 调用失败（API down） | 中 | 全流程支持断点续跑（`prep/phase_state.json`）；trigger_detector 失败后每 6 小时自动重试 |

---

## 十二、执行前置条件

本设计进入实施前需要：

1. ✅ Primus 对 v0.4 **流程设计**做 sign-off（不是对原则内容）
2. ⏳ Adversarial review（独立 AI 审查员 review v0.4，类似 v0.1 → v0.2 那次）
3. ⏳ 实施新脚本：
   - `scripts/soul/trigger_detector.py`（Phase -1）
   - `scripts/soul/board_debate_v2.py`（主调度，支持 full / mini 两种模式）
   - `scripts/soul/principles_synthesizer_v2.py`（Phase 3a-c 含 severity 最低共识 + agenda 生成 + dropped 滑动窗口）
   - `scripts/soul/compliance_scan.py` 升级（+qualitative_claim 数字 + seed 复合性规则）
   - `scripts/soul/seed_schema_v1.1.json`（validator）
4. ⏳ crontab / systemd 配置 trigger_detector 定时运行

**不需要**：
- ❌ Primus 对具体原则的 sign-off（取消）
- ❌ 人工复审环节（取消）
- ❌ 手工激活 Layer 0（取消）

---

## 十三、与 v1.0 的兼容性

- `Principles/v1.0.md` 保留不变
- v1.0 schema 字段是 v1.1 schema 的子集（v1.1 新增字段、不破坏原有字段）
- MVP PrinciplesEngine 通过 `principles_version` 参数化加载
- v0.4 首次跑完产出的新版本命名为 **v1.1.md**（继承 v1.0 编号序列）
- `Principles/current.md` 首次由 v0.4 pipeline 自动 symlink 时指向 v1.1.md

---

## 十四、Changelog vs v0.3

| 改动 | v0.3 | v0.4 |
|---|---|---|
| Phase 3d 人工 DROPPED 复审 | ✅ 有 | ❌ 删除（A1） |
| v1.0.md 要求用户 sign-off Layer 0 激活 | ⚠️ v1.0 有 | ❌ 取消（A2） |
| Follow-up agenda review 主体 | 未明 | ✅ 自动 quarterly mini-debate（A3） |
| 触发机制 | 无 | ✅ Phase -1，4 种触发（B4） |
| DROPPED 重入池机制 | 无 | ✅ 每方每轮 re-introduce 1-3 条 + 3 轮滑动窗口（B5） |
| soul_priority_sections 标注 | 未明 | ✅ Sonnet 自动识别（B6） |
| 3-run majority 判定 | 集合 ambiguous | ✅ 按 framework 独立判定（C7） |
| Severity 取值规则 | 投票（Q9） | ✅ 作为 seed 属性 + 最低共识（C8） |
| rule_subject 错标纠偏 | 无 | ✅ Phase 2 Opus 提示 + Phase 2.5 调整（C9） |
| Seed 原子性强制 | 无 | ✅ Phase 1 prompt + Phase E regex + validator（C10） |
| anti_scope 字段 | 待定 | ✅ 保留（C11） |
| anti_claims 独立列表 | 待定 | ❌ 不加（Q10） |
| evidence_strength 字段 | 待定 | ✅ 加（作参考不影响投票，Q11） |
| Primus HARD veto 权 | 待定 | ❌ 无（Q12） |
| Process critique 机制 | 无 | ✅ 大师提交流程建议供 Primus 设计 v0.5（E12） |
| 预算 | 17-28 calls / 50-85 min | 19-28 calls / 50-90 min（Phase 0 auto-detect 多 3 call） |

---

## 附录 A：名词表

| 术语 | 定义 |
|---|---|
| Full debate | Phase 1 重跑全量，由 T2 触发 |
| Mini-debate | Phase 1 输入集限定，由 T1 / T3 / T4 触发 |
| L1 / L2 / L3 | 共识层级（完全共识 / 方向共识 / 定性分歧） |
| Follow-up agenda | L2 条款自动生成的升级讨论遗留议题 |
| Dropped archive | 连续 3 轮 < 2/3 支持后的真归档 |
| Process critique | 大师对辩论流程本身的建议（不影响原则内容） |
| Primus | 产品设计者（即项目 owner），仅在流程设计层 sign-off |

---

## 附录 B：v0.4 sign-off checklist（给 Primus）

签字即表示同意 **流程设计**，不表示对任何具体原则内容做决定。

- [ ] 三分 rule_subject + 硬聚类约束
- [ ] qual / quant / severity 三维分离 + 最低共识取值规则
- [ ] Seed 原子性 + anti_scope 保留 + 无 anti_claims
- [ ] 3-run Opus majority（按 framework 独立）
- [ ] Phase 2.5 timeout 900s + 2 retry
- [ ] Phase 3b-qual 最多 2 轮
- [ ] DROPPED 3 轮滑动窗口 + re-introduction 机制
- [ ] Phase -1 的 4 种触发条件
- [ ] 无人工复审环节
- [ ] 无用户对具体 HARD 的 sign-off / veto 权
- [ ] 自动 symlink `current.md`
- [ ] Process critique 机制
- [ ] 预算接受度（$130/年）
