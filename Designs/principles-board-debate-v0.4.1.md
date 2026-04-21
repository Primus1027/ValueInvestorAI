# Pre-A: Principles Board Debate — 设计 v0.4.1（adversarial review 后定稿）

> 状态：**实施中**
> 日期：2026-04-21
> 版本：v0.4.1
> 取代：`Designs/principles-board-debate-v0.4.md`（留档）
> 依赖：v0.4 adversarial review 17 个 issues + 用户逐条反馈

---

## 零、v0.4.1 相对 v0.4 的关键变化

| 变化点 | 来源 issue | 影响章节 |
|---|---|---|
| **Phase 2 改为三层架构**：pairwise Sonnet + Opus critic + consistency critic（替代原"Opus 顺序跑 3 次"） | Issue #4 盲区 3 | §三 Phase 2 |
| **新增 Phase 2.75 Cross-Rebuttal** — 4 轮结构化辩论 + transcript 归档 | Issue #7 追问 | §三 / §四 Phase 2.75 |
| **T3 分阶段启用**：MVP 初期完全关闭 → 中期告警 → 成熟期启用 | Issue #1 盲区 1 | §四 T3 |
| **note 语义升级**：保留最低共识取 note，但 Agent 必须显式引用并论证为什么不受约束 | Issue #3 | §二.2.2 |
| **Phase 1→2 之间加 seed 脱敏步骤**：去除身份关键词 + section_id 占位 + 指纹词库扫描 | Issue #5 | §三 + §八 |
| **Circuit breaker**：3 道自动质量门 + 新版本 quarantine 机制 | Issue #6 | §四 Phase 3c + §七 |
| **DROPPED re-introduction** 三条约束：cooldown 4 轮 + quota 6 条/年 + rationale 必须指向 soul doc commit hash | Issue #7 原 | §五 |
| **Phase 1 最低门槛**：每方必须 ≥ 5 条合规 seed；不达标则 fallback 或 partial_failure | Issue #11 | §三 Phase 1 |
| **Prompt 示例改 placeholder**：具体值（0.15、排除银行）改为 `<PLACEHOLDER>` | Issue #14 | §八 |
| **历史归档强制**：所有 prep 产出每次 debate 完成后移入 `Principles/history/{debate_id}/` 永久归档 | 用户反馈 | §一 |
| **成本模型作废**：Claude Max 订阅无 per-call 成本，换为"使用限额守门" | Issue #16 | §十 |
| **meta-debate on prompts**：v0.5 路线图项，Primus 保留 override 权 | Issue #10 meta | §十二 |
| **Issue #2 (Primus 后门)**：不修改，明文声明设计层权力 | 用户反馈 | §零底层原则 |

---

## 一、产出物（v0.4.1 最终）

| 文件 | 生成方 | 说明 |
|---|---|---|
| `Principles/v{N}.md` | 自动 | 按 rule_subject 分三节 HARD |
| `Principles/v{N}.schema.json` | 自动 | 机器可执行 |
| `Principles/soul-level-preferences-v{N}.md` | 自动 | SOFT + 1/3 |
| `Principles/dropped-archive.md` | 自动累积 | 连续 3 轮 DROP 后真归档 |
| `Principles/follow_up_agenda.md` | 自动累积 | 升级议题 |
| `Principles/critique_matrix_v{N}.jsonl` | 自动 | 三维投票 |
| `Principles/current.md` | 自动 symlink | 指向最新通过 circuit breaker 的 HARD |
| `Principles/history/{debate_id}/` 🆕 | 自动 | 每次 debate 的完整中间产出归档（永不覆盖） |
| `Principles/history/{debate_id}/debate_log.md` | 自动 | 该轮完整会议纪要 |
| `Principles/history/{debate_id}/debate_transcript_{cluster_id}.md` 🆕 | 自动 | 每个分歧 cluster 的 4 轮 cross-rebuttal 对话脚本 |
| `Principles/history/{debate_id}/prep/` | 自动 | 该轮所有 Phase 中间 jsonl |
| `Principles/monitoring.md` 🆕 | 自动累积 | T3 告警记录（MVP 中期启用） |
| `prep/process_critique.jsonl` | 自动累积 | 大师对流程的建议（Primus 设计 v0.5 的输入） |
| `prep/phase_state.json` | 自动 | 断点续跑 |
| `prep/trigger_log.jsonl` | 自动累积 | 所有触发记录 |

**Primus 唯一 sign-off 的点**：流程设计文档本身（v0.4.1 → v0.5）。辩论内容无人工审批。

---

## 二、核心设计哲学

### 2.1 Rule Subject 三分（同 v0.4）

`target`（约束被投标的） / `self`（约束投资机构/人）/ `decision_process`（约束分析流程）。同 cluster 硬约束同 rule_subject。

### 2.2 Qualitative / Quantitative / Severity 三维分离 + 最低共识

#### Severity 语义升级（🆕 v0.4.1）

v1.0 对 severity 的定义：
- `veto`：拦截投资决策，returned `passed: false`
- `warning`：仍 `passed: true`，但附 warnings 列表
- `note`：仅记录，不影响 passed 状态

v0.4.1 **升级 note 语义**：
> **note**：Agent 的最终决策输出**必须显式引用本条款**并**论证"为什么本次决策不受该约束"**。未引用或论证不充分 → 该决策输出视为无效（PrinciplesEngine 会强制 Agent 重新生成决策）。

**为什么这样改**：v0.4 的 "最低共识取 note" 哲学是诚实的，但 v1.0 的 note 语义等于"形同虚设"。升级后：
- 三方最低共识仍取 note（尊重共识哲学）
- 但 note 不再是"软到透明" — 它强制 Agent 每次主动 reasoning 一次，形成真实软约束
- Y=veto / W=warning / C=note 的组合 → Layer 0 取 note，Agent 每次决策都对该条款 explicit acknowledge；升级诉求进 follow_up_agenda

#### 最低共识取值规则（v0.4 基础上细化）

| 维度 | 最低共识取值 |
|---|---|
| Threshold（数值） | 三方阈值中**最宽松的共识下界**（例：持有期 Y=10/W=3/C=5 → ≥ 3） |
| Severity | 三方 severity 中**最轻的**（veto > warning > note） |
| Category | 若三方 category 不同，按 qualitative_claim 语义主导 category 取值，其他作 `secondary_categories` 记录 |

更严格的阈值 / 更高的严重度 → `follow_up_agenda`。

### 2.3 大师自主结构化（同 v0.4）

### 2.4 Seed 原子性约束（同 v0.4）

### 2.5 anti_scope 保留（同 v0.4）

### 2.6 Primus 设计层权力（🆕 v0.4.1 明文声明）

Primus 通过 prompt / schema / trigger 设计**间接影响决策**是设计层固有权力，不视为漏洞。自动化的目标是让这种影响通过**少量可审的设计文档**发生（每次改 v0.x.x 都有 diff 可查），而不是通过 runtime 实时干预。

这意味着：
- Primus 可以修改 Phase 1 prompt 模板 → 下一轮大师判断会被塑造
- Primus 可以新增 rule_subject 枚举值 → 改变大师的分类选择空间
- Primus 可以调整 trigger 条件 → 决定 debate 何时跑

这些都是**设计层权力**，透明可审（Git log 可查）。相对的，Primus **不做**的是：
- 不对某条具体 seed / cluster 投票
- 不 override 某次 debate 的投票结果
- 不手动激活或拒绝某个 v{N}.md

---

## 三、v0.4.1 完整流程（新增 Phase 2.75 + 三层 Phase 2）

```
┌──────────────────────────────────────────────────────────────────┐
│ Phase -1: Trigger Detection (Python, cron/launchd)                │
│   4 种触发条件 + 互斥优先级                                        │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 0: Context Preparation (Python + 1 Sonnet call)             │
│   - Soul doc 索引（复用 build_soul_index.py）                      │
│   - priority_sections 自动识别（Sonnet 扫打分）                    │
│   - 读取 current Principles + agenda + dropped-archive             │
│   - 准备 re-introduction candidates (考虑 cooldown/quota)          │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1: 三方独立结构化提案 (3 并发 Sonnet)                        │
│   ⭐ 强制 seed schema v1.1                                         │
│   ⭐ 允许每方 re-introduce 历史 DROPPED 1-3 条 (受 quota 约束)      │
│   ⭐ 最低门槛: 每方 ≥ 5 条合规 seed                                │
│   ⭐ 失败降级: retry 2 次 → v{N-1} HARD fallback (标记 _fallback)  │
│   ⭐ 2 方以上 partial_failure → 整个 debate abort (不产新版)       │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1.5: Seed 脱敏 (1 Sonnet call)   🆕                          │
│   - 替换身份关键词 (本分/too hard pile/lollapalooza 等)            │
│   - section_id → [ref_X] 占位 (真实映射存到 _metadata)             │
│   - 合规扫描指纹词库 (未清除则重跑)                                │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2: 三层架构 stance 识别   🆕                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Pairwise Sonnet (并发)                             │  │
│  │   对每对 (seed_i, seed_j) 问 "语义等价? yes/no + confidence"│  │
│  │   decision space 从集合 → 布尔，稳定性大幅提升              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Layer 2: Opus Critic (仲裁 low-confidence pair)             │  │
│  │   Layer 1 confidence < 0.7 或 yes/no ambiguous 的 pair      │  │
│  │   → Opus 最终判定 (仅小比例 hard case)                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Layer 3: Consistency Critic (1 Sonnet call)                 │  │
│  │   扫所有 pairwise 结果的传递性: A≡B ∧ B≡C ⟹ A≡C           │  │
│  │   不满足传递性 → flag 重跑该三元组                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│   输出: pairwise equivalence matrix + confidence scores            │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2.5: Revise Round (3 并发 Sonnet, 900s + 2 retry)           │
│   keep / modify / withdraw / new                                   │
│   可选提交 process_critique                                        │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 2.75: Cross-Rebuttal (结构化辩论)   🆕🌟                    │
│   对每个潜在分歧 cluster 跑 4 轮:                                  │
│     Round 1 Position (3 方并发, ≤ 150 字)                         │
│     Round 2 Rebuttal (3 方并发, ≤ 100 字)                         │
│     Round 3 Response (被反驳方并发, ≤ 100 字)                     │
│     Round 4 Closing (可选, ≤ 80 字)                               │
│   全程匿名化 A/B/C label                                           │
│   输出: debate_transcript_{cluster_id}.md (Primus 可读的脚本)     │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3a: 语义聚类 (1 Opus call)                                   │
│   基于 Phase 2 equivalence matrix + Phase 2.75 辩论后立场          │
│   按 (rule_subject, qualitative_claim 等价) 聚类                   │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3b-qual: 定性方向投票 (≤ 2 轮, 3 并发 Sonnet)               │
│   投票 rationale 必须引用 debate_transcript 中某段话               │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3b-quant: 定量阈值投票 (3 并发 Sonnet)                       │
│   三值模式 + 最低共识计算                                          │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3b-sev: 严重度汇总 (Python, 无 LLM)                         │
│   取最轻共识 (note 保留, 语义升级后不再形同虚设)                   │
│   升级诉求 → follow_up_agenda                                      │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase 3c: 渲染 + Circuit Breaker (Python)  🆕                     │
│   生成 v{N}.md, schema, soul-level, agenda                         │
│   ⭐ 3 道质量门:                                                    │
│     - Regression guard: HARD ≥ v{N-1} × 70%                        │
│     - Drift guard: veto 占比降幅 ≤ 30%                             │
│     - Health check: ≥ 2 方 Phase 2.5 fallback → debate unhealthy   │
│   过门 → symlink current.md → v{N}.md                              │
│   不过门 → 移至 v{N}_quarantine.md, current.md 不变                │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase E: 合规扫描 (Python regex + LLM 辅助)                       │
│   扫: 身份扮演 / qual_claim 含数字 / seed 复合性 /                 │
│       指纹词库 / prompt de-anonymization                           │
│   违规 → 自动重跑对应 Phase                                        │
└──────────────────┬───────────────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Phase F: 归档 (Python)  🆕                                         │
│   所有 prep/phase*.jsonl → Principles/history/{debate_id}/prep/    │
│   生成 debate_log.md 总结                                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 四、各 Phase 详细规格（v0.4.1 更新部分）

### Phase -1: Trigger Detection（同 v0.4，仅 T3 阶段化）

4 种触发：
- **T1 定时**（每季度）
- **T2 soul doc 版本**（semver minor+）
- **T3 实战信号** 🆕 分阶段：
  - MVP 初期（案例 < 10）：**完全关闭**
  - MVP 中期（案例 10-50）：**只写 `Principles/monitoring.md`**，不触发 debate
  - MVP 成熟期（有 ground truth 回报信号）：启用 meta-debate（辩论"该条款是否应 Layer 0"，不是"阈值改多少"）
- **T4 agenda 积累** ≥ 10 条

互斥优先级：T2 > T3 > T4 > T1。

### Phase 0（v0.4 基础上细化）

新增逻辑：
- 扫 `Principles/dropped-archive.md`，按 cooldown 规则（真归档后至少 4 轮）过滤可 re-introduce 候选
- 扫每 master 当年 re-introduction 累计次数，按 quota（6 次/年）过滤可用数
- 输出 `prep/reintro_candidates_{master}.jsonl` 供 Phase 1 引用

### Phase 1: 三方独立提案（v0.4.1 关键改动）

#### 最低门槛

每方必须产出 ≥ 5 条合规 seed（通过 JSON Schema validator + 原子性 regex）。

#### 失败降级流程

```
Phase 1 跑 → 结果合规检查
  ├─ ≥ 5 条合规 → 正常流程
  ├─ < 5 条合规 → retry 1 (同 prompt)
  │             ├─ ≥ 5 条 → 正常
  │             └─ < 5 条 → retry 2 (调整 prompt 明确合规要求)
  │                       ├─ ≥ 5 条 → 正常
  │                       └─ < 5 条 → FALLBACK:
  │                                    用 v{N-1} 中该 master 的 HARD 条款作为 seed
  │                                    标记 _fallback_from_v{N-1} = true
  │                                    该 master 的 seed 在 Phase 2 stance 判定中 confidence 降权 × 0.7
  └─ 若 ≥ 2 方 fallback → debate 标记 phase1_partial_failure
                        → 不生成新版本，只写日志告警
                        → trigger_log.jsonl 记录
```

#### Re-introduction 规则（v0.4.1 严格化）

每 master 在 Phase 1 seed 列表中可包含 1-3 条 re-introduced seed，每条必须：

```jsonc
{
  "_reintroduced_from": "cl_26 (v1.0 dropped-archive)",
  "_reintroduction_rationale": "W soul doc commit a1b2c3d 新增 #capital-conservatism-under-macro-stress 章节，提出 Debt/EBITDA 3x 为结构性红线，与本条目标一致",
  "_reintroduced_seed_commit_hash": "a1b2c3d",   // 必填: git commit hash
  "_reintroduced_seed_section_id": "#capital-conservatism-under-macro-stress"  // 必填: 新章节 anchor
}
```

**约束检查**（在 Phase 0 预处理时完成）：
- cooldown: 该 cluster 真归档后至少 4 轮（由 `dropped-archive.md` 的 `_archived_at_debate_id` 追溯）
- quota: 该 master 本年度（当前 debate_id 所在年）累计 re-introduce 次数 ≤ 6

不满足约束的 re-introduction 提议自动剔除（不 count 入 Phase 1 的 5 条最低门槛）。

### Phase 1.5: Seed 脱敏（🆕 v0.4.1）

位置：Phase 1 输出 → Phase 2 输入之间。

**操作**：
1. 对每条 seed 的 `qualitative_claim` / `rationale` / `anti_scope` 字段跑 Sonnet 脱敏
2. 指纹词替换表（`scripts/soul/_prompts/fingerprint_dict.json`）：
   ```json
   {
     "本分": "品行自律",
     "too hard pile": "太难理解的领域",
     "lollapalooza": "多因素汇合效应",
     "能力圈": "熟悉领域",
     "tier-1 铁律": "核心约束",
     "circle of competence": "knowledge boundary"
     // ... 持续维护
   }
   ```
3. `supporting_section_id` 替换为 `[ref_1]`、`[ref_2]` 等占位，真实映射保存到 `prep/phase1_5_section_id_map.json`
4. 合规扫描：脱敏后再次扫指纹词库，若仍检出则 retry 脱敏

脱敏后的 seed 进 Phase 2；原始 seed 保存在 `prep/phase1_original_seeds_{master}.jsonl`（合规扫描员可 audit）。

### Phase 2: 三层架构（🆕 v0.4.1 核心重构）

#### Layer 1: Pairwise Sonnet

**输入**：所有 master 的脱敏后 seeds，组成两两 pairs。若总 seeds 数为 N，pairs 数为 N×(N-1)/2。

**每对 pair 的 prompt**（~150 tokens 输入 + ~50 tokens 输出）：
```
你是语义等价判定员。下面两条投资方法论原则是否在核心观点上语义等价？
注意：阈值差异不算等价；范围描述差异不算等价；仅当两条的"定性方向 + 约束主体"都一致时才判等价。

Seed A: <qualitative_claim A>
Seed B: <qualitative_claim B>

输出 JSON:
{
  "equivalent": true|false,
  "confidence": 0.0-1.0,
  "brief_reason": "<30 字以内>"
}
```

**并发**：所有 pairs 并发（受 Claude Max 限额约束，可分批，每批 ≤ 10）。

**输出**：`prep/phase2_pairwise_matrix.jsonl`

```jsonc
{"pair_id": "01-02", "seed_ids": ["seed_01", "seed_02"], "equivalent": true, "confidence": 0.92, "brief_reason": "..."}
```

#### Layer 2: Opus Critic

**触发条件**：Layer 1 输出中 `confidence < 0.7` 或 `equivalent` 在多次 run 中不稳定的 pair（默认 low-confidence 比例预估 20-30%）。

**每 pair 的 Opus 仲裁 prompt**：
```
下列两条投资原则是否语义等价？Sonnet 初判 equivalent=<val>, confidence=<val>, 但置信度不足以直接采信。
请结合两条的 full rationale 做最终判定。

Seed A (full): {qualitative_claim + rationale}
Seed B (full): {qualitative_claim + rationale}

输出 JSON:
{
  "equivalent_final": true|false,
  "rationale": "<100 字以内的判定依据>"
}
```

输出覆盖 Layer 1 对应 pair 的结果。

#### Layer 3: Consistency Critic

**位置**：Layer 1/2 完成后，产出最终 equivalence matrix 之前。

**操作**：
1. Python 构建所有 `equivalent=true` 的三元闭包
2. 对每个 A, B, C 三元组，若 A≡B ∧ B≡C 但 A≢C（或其他传递性违规），**flag**
3. 若 flag 数 > 0，Sonnet 扫整体矩阵给出 "哪几对可能误判" 的建议
4. 重跑这些 pair（Opus Layer 2）

**输出**：`prep/phase2_final_matrix.jsonl` + `prep/phase2_consistency_report.md`

### Phase 2.75: Cross-Rebuttal（🆕🌟 v0.4.1 最重要的新机制）

#### 触发与输入

在 Phase 2 完成后、Phase 3a 聚类前。

**候选分歧 cluster 识别**（Python 预处理）：
- 从 equivalence matrix 中找出 "多 master 有同聚类但 threshold/severity 存在 variants" 的 potential clusters
- 或 "有 master 的 seed 与他方存在 partial equivalence（confidence 0.3-0.7）" 的边界 case
- 这些候选进入 Cross-Rebuttal；完全一致或完全不等价的 clusters 跳过

**预计每轮 debate 有 5-15 个分歧 cluster 进入 Phase 2.75。**

#### 4 轮结构化对话

每个分歧 cluster 独立跑（可并发多 clusters）：

**Round 1 — Position Statement**（3 方并发 Sonnet call）

每方 prompt：
```
你是 {framework_id}（匿名标签 A/B/C）框架的方法论研究助手。本轮 Cross-Rebuttal
针对 cluster_{cid}，其涉及的 qualitative_claim 为：

"<canonical_qualitative_claim>"

三方的 variant seeds (脱敏后) 如下：
{seeds_by_framework}

请用 ≤ 150 字明确你方的立场和核心论据（基于你方已产出的 seed 的 rationale）。
禁止提及其他 framework 的身份特征。禁止展开新的话题。
```

输出：`{cluster_id}/round1_position_{framework}.txt`

**Round 2 — Rebuttal**（3 方并发）

每方 prompt：
```
你已看到三方的 Round 1 立场陈述（脱敏匿名）。请选出对你方立场最构成挑战的一方，
用 ≤ 100 字反驳其论据。反驳必须具体（不能只是"不同意"），要指向对方论证的具体弱点。
```

输出：`{cluster_id}/round2_rebuttal_{framework}.txt`

**Round 3 — Response**（被反驳方并发）

Python 解析 Round 2，确定每方被哪方反驳。被反驳方 prompt：
```
{challenger_framework} 框架对你方 Round 1 立场提出如下反驳：
"{rebuttal_text}"

请用 ≤ 100 字回应。你可以:
(a) 接受对方论点并修正自己立场
(b) 反驳对方的反驳
(c) 承认分歧存在但说明为何你方立场仍有价值
```

**Round 4 — Closing**（可选，由 moderator 决策）

Python 判断：若 Round 3 所有框架都选 (a) 或 (c) → debate 收敛，不需要 Round 4。
若仍有 (b) → 给每方 ≤ 80 字 closing statement 机会。

#### 输出

每个 cluster 生成 `Principles/history/{debate_id}/debate_transcript_{cluster_id}.md`，格式（见用户确认的示例）：

```markdown
# Cluster {cluster_id} 交叉辩论 — {topic}

## Round 1 Position Statements

**Framework A**: ...
**Framework B**: ...
**Framework C**: ...

## Round 2 Rebuttals

**A 质疑 B**: ...
**B 质疑 C**: ...
**C 质疑 A**: ...

## Round 3 Responses

**A 回应 C**: ... (action: accept/rebut/acknowledge)
**B 回应 A**: ...
**C 回应 B**: ...

## Round 4 Closing (if needed)

...

## Final Positions

- A: "<修正后 claim>"
- B: "<修正后 claim>"
- C: "<修正后 claim>"

## 分歧收窄 & 仍存

**收窄**: ...
**仍存**: ...
```

transcript **同时**作为 Phase 3b 投票的必读背景，投票者的 rationale 必须引用 transcript 的某段话。

#### 合规

Cross-Rebuttal 全程匿名化，Phase E 扫描 transcript 文件中是否出现 master 名称或指纹词。

### Phase 3a/3b/3c（v0.4 基础上小改）

- Phase 3a 聚类：输入含 Phase 2 matrix + Phase 2.75 final positions
- Phase 3b-qual 投票：rationale 必须引用 transcript 段落（Python 校验包含 `@transcript:` 标记）
- Phase 3c 渲染：新增 circuit breaker 逻辑

### Phase 3c: Circuit Breaker（🆕 v0.4.1）

```python
def circuit_breaker(new_version_clusters, prev_version_md):
    prev_hard_count = count_hard(prev_version_md)
    new_hard_count = count_hard_in_clusters(new_version_clusters)

    prev_veto_ratio = count_veto(prev_version_md) / prev_hard_count
    new_veto_ratio = count_veto_in_clusters(new_version_clusters) / new_hard_count

    phase2_5_fallback_count = count_fallback_masters()

    # 3 道门
    gate1_pass = new_hard_count >= prev_hard_count * 0.7
    gate2_pass = (prev_veto_ratio - new_veto_ratio) / prev_veto_ratio <= 0.3 if prev_veto_ratio > 0 else True
    gate3_pass = phase2_5_fallback_count < 2

    return {
        "regression_guard": gate1_pass,
        "drift_guard": gate2_pass,
        "health_check": gate3_pass,
        "all_pass": gate1_pass and gate2_pass and gate3_pass
    }
```

若 `all_pass=True` → symlink `current.md` → `v{N}.md`
若 `all_pass=False` → 写 `v{N}_quarantine.md`，current.md 不变，写告警到 `trigger_log.jsonl` 和 `Principles/monitoring.md`

### Phase F: 归档（🆕 v0.4.1）

Phase 3c 完成后，自动：
1. 创建 `Principles/history/{debate_id}/` 目录（debate_id = `{date}_{trigger_type}`）
2. 移动所有 `prep/phase*.jsonl`、`prep/phase*.json` 到 `history/{debate_id}/prep/`（非拷贝）
3. 生成 `debate_log.md` 总结（统计数据 + HARD/SOFT/DROP 分布 + circuit breaker 结果 + process_critique 摘要）
4. `prep/` 清空供下次 debate 使用（但 `dropped-archive.md`、`follow_up_agenda.md`、`current.md`、`process_critique.jsonl` 等累积文件保留）

---

## 五、DROPPED 滑动窗口 + Re-introduction（v0.4.1 严格化）

### 规则集

1. **进 DROPPED 滑动窗口**：某 cluster 在 Phase 3b-qual 投票 < 2/3 support
2. **真归档条件**：连续 3 次 debate（跨触发） < 2/3 support
3. **真归档后 re-introduce**：任何 master 可在自己 Phase 1 seed 中标记 `_reintroduced_from`
4. **Re-introduce 约束**（v0.4.1 新加）：
   - **Cooldown**：该 cluster 真归档后至少 **4 次 debate**（约 1 年，假设每季度 1 次）方可 re-introduce
   - **Quota**：每 master 每年（按 debate_id 年份）累计 re-introduce 次数 ≤ **6 次**
   - **Rationale 格式**：必须指向 **soul doc git commit hash + 新章节 anchor**，不能是自然语言模糊描述
5. **Re-introduce 失败后**：若本轮仍 < 2/3 support → **直接回归档**，不进滑动窗口（drop_history 不清零）
6. **Re-introduce 成功后**（≥ 2/3 support）：进入当前轮正常流程，若入 L1/L2 则从 dropped-archive 移出；`_drop_history` 清空

### 数据结构

`Principles/dropped-archive.md` 附带 YAML frontmatter：

```yaml
---
dropped_clusters:
  - cluster_id: cl_26
    canonical_claim: "任何使用借贷资金投资直接拒绝"
    rule_subject: self
    _drop_history:
      - debate_id: "2026-04-20_initial"
        support_count: 1
      - debate_id: "2026-07-01_quarterly_review"
        support_count: 1
      - debate_id: "2026-10-01_quarterly_review"
        support_count: 1
    _archived_at_debate_id: "2026-10-01_quarterly_review"
    _reintro_count_by_master:
      duan: 2
      munger: 0
      buffett: 0
  - ...
---
```

---

## 六、使用限额守门（🆕 v0.4.1）

### Claude Max 订阅特性

- 无 per-token $ 成本
- 有 "5 小时窗口" 使用限额（每 5 小时 reset）
- Opus 消耗比 Sonnet 高（粗估 3-4x token 消耗）

### 建议策略

1. **T1 定时触发安排在深夜**（crontab `0 3 1 */3 *`，每季度首日凌晨 3 点）— 避开 Primus 的 MVP 开发工作窗口
2. **使用限额预估**：
   - Full debate：~200-400 LLM calls（Phase 2 pairwise + 2.75 rebuttal 最重），可能耗 50-70% 5 小时额度
   - Mini debate：~50-100 calls，耗 20-30% 额度
3. **分批执行**：Phase 2 pairwise（可能 100+ pairs）自动分批，每批 ≤ 10 并发，批间 sleep 30 秒，防一次性耗尽限额
4. **降级预案**：若 Orchestrator 检测到 `usage_limit_near` 告警（由 CliClaudeProvider 暴露的 header 判断），自动暂停当前 Phase，保存 `phase_state.json`，等额度恢复后断点续跑

---

## 七、Circuit Breaker 三道门（🆕 v0.4.1）

详见 §四 Phase 3c 代码段。决策逻辑汇总：

| 门 | 检查 | 不过怎么处理 |
|---|---|---|
| Regression guard | 新 HARD 数 ≥ 旧版 70% | 新版本移 `v{N}_quarantine.md`；current.md 不变 |
| Drift guard | veto 占比降幅 ≤ 30% | 同上 |
| Health check | Phase 2.5 fallback 方数 < 2 | 整个 debate 标 unhealthy；不产新版 |

Quarantine 版本不自动激活，但 debate_log 记录下来。下次 debate 开始前 Primus 可手动 review（这是流程层审阅，不违反"不介入决策"—— Primus 看的是"为什么 quarantine 了"，决定要不要改流程，不是改具体条款）。

---

## 八、Prompt 模板合规要求（v0.4.1 严化）

### Phase 1 prompt

**不变**：身份框架 = "价值投资方法论研究助手"，禁止扮演。

**新加（Issue #14）**：所有示例字段值改为 placeholder。

正例：
```json
{
  "qualitative_claim": "<方向性陈述，描述某指标/行为与某判定结果的关系>",
  "quantitative_rule": {
    "metric": "<METRIC_NAME>",
    "threshold": <NUMERIC_THRESHOLD>,
    ...
  },
  "severity": "<veto | warning | note>",
  "anti_scope": "<SCOPE_EXCLUSION>"
}
```

反例（禁用）：示例中含具体 "0.15"、"银行保险"等。

**新加（Issue #5 相关）**：Phase 1 prompt 提醒 "qualitative_claim 写作时尽量避免使用方法论特有的称谓（如'本分''lollapalooza'），改用通用词"。这是第一层防御；Phase 1.5 是兜底。

### Phase 1.5 prompt（🆕）

```
你是 seed 脱敏员。下列 seed 的 qualitative_claim 与 rationale 可能含方法论身份
指纹（如"本分"、"too hard pile"、"能力圈"等），请替换为通用词保留语义：

指纹映射字典（部分）:
{fingerprint_dict}

输入: {seed_json}
输出: 相同结构的 seed，敏感词已替换。不新增/删除字段。
```

### Phase 2 Layer 1 pairwise prompt

见 §四 Phase 2 Layer 1。

### Phase 2.75 各 round prompt

见 §四 Phase 2.75。关键合规：所有 round 都以匿名 A/B/C label，禁止引用 master 名或方法论指纹词。

### Phase E 合规扫描规则（升级）

| 规则 | 扫描对象 | 处置 |
|---|---|---|
| 身份扮演（"你是 Buffett"等） | 所有中间产出 + 最终文档 + prompt 文本 | 🔴 fail, abort |
| qualitative_claim 含数字（如 "15%"、"3 倍"）| phase1_*_seeds.jsonl 的 qualitative_claim 字段 | 🟡 warning，retry 生成 |
| Seed 复合（"既..又"、"不..但"等）| phase1_*_seeds.jsonl | 🟡 retry 拆分 |
| 指纹词（"本分"、"lollapalooza"等） | phase2_input（脱敏后）| 🔴 fail Phase 1.5，重新脱敏 |
| Prompt 文本 de-anonymization（"A 对应 buffett"） | scripts/soul/board/_prompts/*.md | 🔴 fail，拒绝启动 debate |

---

## 九、Process Critique 机制（v0.4.1 微调）

大师在 Phase 2.5 可选提交 process_critique 条目。存到 `prep/process_critique.jsonl`。

**v0.4.1 新增声明**：Primus 读 process_critique 后在设计 v0.5 时的改动透明可审（Git log 可查）。不强制 "三方 diff 共识门"（按用户要求，保留 Primus 的设计层权力）。

---

## 十、时间预算（v0.4.1 更新）

| Phase | 调用 | 并发 | 预计时间 | 限额占用预估 |
|---|---|---|---|---|
| -1 (Python) | 0 | - | < 1 s | 0 |
| 0 (priority_sections) | 3 Sonnet | yes | 2-3 min | ~5% |
| 1 (seed draft + retry) | 3-9 Sonnet | yes | 10-15 min | ~15% |
| 1.5 (脱敏) | 1-3 Sonnet | yes | 2-3 min | ~3% |
| 2 Layer 1 (pairwise) | 50-150 Sonnet | 10-way batched | 10-20 min | ~25% |
| 2 Layer 2 (Opus critic) | 5-30 Opus | 3-way batched | 5-15 min | ~15% |
| 2 Layer 3 (consistency) | 1-3 Sonnet | - | 2-5 min | ~3% |
| 2.5 (revise) | 3-9 Sonnet | yes | 10-20 min | ~10% |
| **2.75 (Cross-Rebuttal)** 🆕 | 60-180 Sonnet | 3-way batched | 20-40 min | ~20% |
| 3a (cluster) | 1 Opus | - | 5-10 min | ~5% |
| 3b-qual (2 轮) | 6-12 Sonnet | yes | 5-10 min | ~5% |
| 3b-quant | 3 Sonnet | yes | 3-5 min | ~3% |
| 3b-sev (Python) | 0 | - | < 1 min | 0 |
| 3c (Python) | 0 | - | < 1 min | 0 |
| E (Python + Sonnet scan) | 1-5 Sonnet | - | 2-5 min | ~3% |
| F (Python) | 0 | - | < 1 min | 0 |
| **Full 合计** | **140-400 calls** | | **80-150 min** | **~110% → 需跨限额窗口 或分 2 次跑** |
| Mini 合计 | 40-120 calls | | 30-50 min | ~30-50% |

**关键发现**：v0.4.1 的 full debate 可能**单个 5 小时窗口跑不完**。两种应对：
1. 拆为两段跑：Phase 0-2 一次，Phase 2.5-F 一次，之间 sleep 等额度 reset
2. Orchestrator 检测到限额紧张时自动暂停 + 断点续跑

实施时选方案 2（更稳健）。

---

## 十一、风险矩阵

| 风险 | 概率 | 缓解 |
|---|---|---|
| Phase 2 pairwise 结果仍不稳定（单 pair 也不稳）| 低 | Layer 2 Opus 仲裁 + Layer 3 consistency critic |
| Phase 2.75 debate 发散（超 token 限制）| 中 | 每 round 严格字数限制 + Python 后处理截断 |
| Phase 2.75 辩论脚本质量差（敷衍）| 中 | 每 round prompt 要求"具体指向对方弱点"；Phase E 合规扫描抽检 |
| Circuit breaker 过于严格导致 v{N} 几乎永不生效 | 低 | 门槛参数（70%, 30%）可调；Phase 3c 输出时显式列出 each gate 值 |
| Re-introduction 仍被滥用 | 低 | Quota + cooldown + commit hash 三重约束 |
| Seed 脱敏改变语义 | 中 | 脱敏前后对比由 Phase E 抽检；映射字典保守（只替换明确指纹词） |
| 使用限额耗尽导致 debate 无限 retry | 中 | Orchestrator usage_limit_near 检测 + 断点续跑 + 限额窗口跨越 |
| Debate transcript 归档膨胀磁盘 | 低 | 每 debate ≤ 5MB，10 年合计 < 500MB |

---

## 十二、v0.5 Roadmap

v0.4.1 实施后，如下 idea 留待 v0.5 讨论：

1. **Meta-debate on prompts**（Issue #10）：让三方大师匿名审查 Primus 写的 prompt 模板是否含隐性倾向。产出 flag list 但不强制，Primus 保留 override 权
2. **Soul doc 质疑机制**（Issue #15）：给 soul doc 本身引入 adversarial review 层
3. **Request_override 成熟期机制**（Issue #1 阶段 3）：当 MVP 有 ground truth（人类/市场回报数据确认 override 是否对）时，启用 T3 meta-debate
4. **Agenda 自动重新激活**（Issue #12）：永久分歧区条款加 `_soul_doc_snapshot`，soul doc 变化时自动回 agenda
5. **Opus 模型版本升级后重新评估**（Issue #4 长期）：Opus 5.x / Sonnet 5.x 发布后重跑 consistency stress test，看能否简化回更少层

---

## 十三、执行前置

1. ✅ Primus 对 v0.4.1 流程设计 sign-off（等同于任务启动确认）
2. 🔨 本任务包：实施所有 v0.4.1 脚本
3. 🔨 本任务包后：首次 T2 手动触发（或 T1 到期）生成 v1.1.md

---

## 十四、Changelog vs v0.4

| 改动 | v0.4 | v0.4.1 |
|---|---|---|
| Phase 2 架构 | Opus 顺序 3-run majority | Sonnet pairwise + Opus critic + consistency critic |
| Phase 2.75 | ❌ 无 | ✅ Cross-Rebuttal 4 轮结构化辩论 |
| T3 启用 | 一开始就启用 | 分 3 阶段（MVP 初期关闭 / 中期告警 / 成熟期启用） |
| Severity note 语义 | 形同虚设 | 强制 Agent 显式引用 + 论证 |
| Phase 1.5 脱敏 | ❌ 无 | ✅ 身份关键词去除 + section_id 占位 |
| Phase 1 失败降级 | 未明 | ≥ 5 条门槛 + v{N-1} HARD fallback + partial_failure abort |
| Phase 3c Circuit breaker | ❌ 无 | ✅ 3 道门 + quarantine 机制 |
| DROPPED re-introduction 约束 | 模糊 | cooldown 4 轮 + quota 6 条/年 + commit hash rationale |
| Prompt 示例 | 具体值 | placeholder |
| 成本估算 | $130/年 | 作废（Claude Max）+ 使用限额守门 |
| Debate 历史归档 | 隐式 | 显式 `Principles/history/{debate_id}/` |

v0.4.1 相对 v0.4 增加约 30-50% LLM 调用（主要是 Phase 2.75 Cross-Rebuttal），但用 Claude Max 无 $ 成本。时间从 50-90 min 增加到 80-150 min。

---

## 附录 A：sign-off checklist

- [x] Rule subject 三分 + 硬聚类约束
- [x] Qual / quant / severity 三维分离 + 最低共识取值
- [x] note 语义升级（必须引用 + 论证）
- [x] Seed 原子性 + anti_scope 保留
- [x] Phase 2 三层架构（pairwise + critic + consistency）
- [x] Phase 2.75 Cross-Rebuttal 4 轮对话 + transcript 归档
- [x] Phase 1 最低门槛 + v{N-1} fallback
- [x] Phase 1.5 seed 脱敏
- [x] DROPPED 3 轮滑动窗口 + cooldown 4 轮 + quota 6 条/年
- [x] Circuit breaker 3 道门 + quarantine
- [x] T3 分阶段启用
- [x] 历史 debate 永久归档
- [x] 使用限额跨窗口断点续跑
- [x] Primus 设计层权力明文声明（不修）
