# Pre-A: Principles Board Debate — 设计草案 v0.1

> 状态：**草案，待对抗性审查**
> 日期：2026-04-20
> 作者：Claude (主设计)
> 下一步：提交给另一个 AI (Plan agent, adversarial reviewer) 做 debate，然后呈给用户

---

## 一、背景与定位

在 ValueInvestorAI 的五层防线架构中，**Layer 0 = Principles.md** 是代码层硬约束，Python if/else 执行，LLM 无法绕过。

这份文档的来源（按 design-v2 要求）：**"大师董事会生成，认知驱动更新（非市场驱动），全票通过制。"**

Pre-A 的任务：用现有 W v1.1 + C v1.1 + Y v1.0 soul doc + 3 份 profile.json，让三个"方法论研究助手"Agent 通过结构化辩论，**产出 Principles.md v1.0**。

### 为什么这一步关键

1. **护栏地基**：没有 Principles.md，MVP Agent 只有 Layer 1 soul prompt，所有过滤/否决全靠 LLM 自觉 —— LLM 会漂移
2. **验证 soul doc 粒度**：如果三方辩论产出不了连贯的硬约束，说明 soul doc/profile 还不够决策化 → 省下走到 A 发现问题的弯路
3. **顺便实现"多 Agent 辩论"原语**：A 阶段 BoardOrchestrator 的依赖组件
4. **合规压力测试**：辩论场景下 Agent 最易漂向"I, Buffett, believe..."；是 `prompt-framing-guidelines.md` 的真正考验

---

## 二、产出物（明确交付清单）

| 文件 | 格式 | 用途 |
|---|---|---|
| `Principles/v1.0.md` | Markdown，4 小节 | 人类可读条款 + 每条投票记录 + 来源归属 |
| `Principles/v1.0.schema.json` | JSON Schema | Python 直接 import → `PrinciplesEngine.evaluate(company_data)` 可执行 |
| `Principles/debate_log_2026-04-20.md` | Markdown | 完整辩论过程（所有提案、质询、修正） |
| `Principles/critique_matrix.jsonl` | JSONL | 每条 candidate principle × 3 master 的投票记录 |
| `Principles/validation_report.md` | Markdown | Principles 在 cases.json 上的 self-check 结果 |
| `Principles/changelog.md` | Markdown | 未来升级时追溯 |

---

## 三、四阶段流水线

```
┌─────────────────────────────────────────────────────┐
│ Phase 1: Independent Seed Drafts (并行 3 × 1 call)   │
│  W / C / Y 各自独立提出 5-15 条 principles           │
│  每条含：id, category, claim, rationale, threshold    │
│  └─→ {w,c,y}_seed_principles.jsonl                   │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│ Phase 2: Cross-Review (并行 6 calls, 3×2)            │
│  W 审 C+Y 的 seeds 逐条: agree/modify/disagree + 理由│
│  C 审 W+Y, Y 审 W+C，同样                            │
│  └─→ critique_matrix.jsonl                           │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│ Phase 3: Semantic Dedupe + Vote Synthesis (1 call)   │
│  LLM 辅助去重跨方的同义 principles（如 "ROE>15%" vs  │
│  "高资本回报率"）→ 统一 canonical principle          │
│  按投票数分档：3/3 HARD, 2/3 SOFT, 1/3 DROP          │
│  └─→ Principles/v1.0.md + v1.0.schema.json           │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│ Phase 4: Validation (Python, 无 LLM)                 │
│  对 cases.json 跑 PrinciplesEngine.evaluate:         │
│  - STD-001~005 (known good) 应全 pass                │
│  - ADV-* 应触发合理 warning                          │
│  - CRS-* 应适度触发 crisis flag                      │
│  └─→ validation_report.md                            │
└─────────────────────────────────────────────────────┘
```

**预计 LLM 成本**：3 + 6 + 1 = 10 个辩论 call × 平均 4 min = ~13 min sequential，并行后 ~5-6 min。Phase 4 全是 Python，无 LLM。

---

## 四、Seed Principle Schema

每条 seed principle 结构化为：

```json
{
  "seed_id": "w_seed_01",
  "master_id": "buffett",
  "category": "quantitative_hard | qualitative_required | position_sizing | veto_line | valuation_method",
  "claim": "公司历史 ROE 需连续 5 年 ≥ 15%",
  "rationale": "高 ROE 是资本生产力的直接指标，巴菲特在多封股东信中强调...",
  "supporting_soul_doc_anchor": "W-buffett/v1.1.md#Module3-ROE",
  "supporting_profile_factor": "buffett.json#factors.financial_fortress",
  "quantitative_rule": {
    "metric": "roe_5yr_min",
    "operator": ">=",
    "threshold": 0.15,
    "data_field": "financials.roe_5yr_min"
  },
  "qualitative_rule": null,
  "severity_if_violated": "veto | warning | note",
  "edge_cases_anticipated": ["cyclical industries may show temporary ROE dip"]
}
```

每个 category 的预期条目数：
- `quantitative_hard`: 5-10 条（ROE, 盈利持续性, 杠杆, FCF, 分红, 等）
- `qualitative_required`: 3-5 条（能力圈, 商业模式可解释, 管理层诚信）
- `position_sizing`: 3-5 条（单只上限, 总持仓数, 集中度阈值）
- `veto_line`: 3-5 条（直接拒绝的硬条件）
- `valuation_method`: 2-3 条（用什么 / 不用什么）

**总量预期**：每 master 16-28 条 → 三方合计 48-84 条 → 去重后 **final ~20-40 条 principles**。

---

## 五、Prompt 合规设计（关键！）

所有 Agent 必须用 **"方法论研究助手"** 口吻，严禁扮演。

### Phase 1 System Prompt 模板

```
你是一位价值投资方法论研究助手。本练习的任务是从 {master} 公开资料整理出的
投资方法论框架中，提炼出可以被 Python if/else 执行的硬约束规则。

==== 方法论文档（整理自 {master} 的公开著作和访谈）====
{soul_doc}

==== 决策框架（结构化的评估维度）====
{profile}

请从这份方法论中识别出 5-15 条可以被机器执行的硬约束规则。每条规则必须：
1. 是"拒绝某类投资"的规则（negative filter），不是"推荐某类"（positive bias）
2. 有清晰的量化阈值 OR 可以被自动化的定性判断
3. 直接来源于上述方法论文档（不编造）
4. 如可能，附上 soul doc 的锚点或 profile 的 factor ID

输出纯 JSON 数组，每条含 {schema 如 §四}。不要其他文字。
本练习为方法论研究性质，不构成投资建议。
```

### Phase 2 Review System Prompt 模板

```
你是一位价值投资方法论研究助手（运用 {master} 的方法论框架）。

本任务：评审另外两位方法论框架（分别整理自 {other_master_1} 和 {other_master_2}）
提出的 principles，判断它们是否与 {master} 的方法论相容。

对每条 principle，输出一个判断：
{
  "seed_id": "...",
  "stance": "agree | agree_with_modification | disagree",
  "rationale": "...",
  "modified_version": <只在 agree_with_modification 时>,
  "conflict_evidence": <只在 disagree 时，引用 soul doc 锚点证明矛盾>
}
```

### Phase 3 Synthesis Prompt 模板

```
你是辩论记录员。下面是三位方法论研究助手（W/C/Y）独立提出的 principle seeds，
以及他们互相评审的 stance。

你的任务：
1. 识别语义等价的 principles（跨方的相同主张，不同措辞），合并成 canonical form
2. 统计每条 canonical principle 的投票：agree + agree_with_modification 计为支持
3. 按投票档分类：
   - 3/3 → 进 Principles.md 的 "硬约束 / 全票通过" section
   - 2/3 → 进 "多数共识 / 软约束" section
   - 1/3 → 不进，作为 soul doc 层面个人偏好保留
4. 输出 Principles.md 草稿 + schema.json

严禁：
- 编造任何不在 seed 池中的 principle
- 把"1 票支持"的 principle 强行升级为硬约束
```

---

## 六、语义去重挑战

**问题**：三方会提出不同措辞的相同 principle。例：
- W: `"公司历史 ROE 需连续 5 年 ≥ 15%"`
- C: `"高资本回报率（ROE > 12% 为宜）"`
- Y: `"ROE 是关键指标，低于 10% 一般不考虑"`

这是同一 principle（ROE 阈值），但阈值不同、措辞不同。

**解决方案**：Phase 3 使用 LLM 辅助语义合并：
1. **第一轮**：LLM 识别同义组（基于 `category` + `claim` 的语义相似）
2. **第二轮**：对每个同义组，决定 canonical claim 和 canonical threshold
   - 规则：**取最严格的阈值**（保守偏好 = 高 ROE 要求 = 15%）
   - 但记录各 master 原始阈值作为 metadata
3. **验证**：如果阈值差异 > 50%（如 W 要 15%, Y 要 7%），flag 为"需人工审查"不自动合并

---

## 七、Validation Phase 设计

Phase 4 纯 Python，不用 LLM：

```python
from principles_engine import PrinciplesEngine
pe = PrinciplesEngine.load("Principles/v1.0.schema.json")

# 对每个校准 case
for case in load_cases():
    synthetic_company = build_company_data_from_case(case)  # 从 case 提取 ROE, PE 等
    result = pe.evaluate(synthetic_company)
    # result = {passed: bool, violations: [...], warnings: [...]}

# 验证判据：
#  - STD-* (known good investments) → 大部分应 pass，少数 warnings 可接受
#  - ADV-* (philosophical evolution cases) → 可能多 warnings（这是设计意图）
#  - CRS-* (crisis) → 主要 warnings，不是硬否决
```

**红旗信号**（Principles 质量问题）：
- 若 Principles 把 STD-001 (KO 1988, 经典好 buy) 否决了 → 过严，需要放宽
- 若 Principles 对所有 case 都 pass → 过松，没有实际过滤力
- 若 Principles 的 warnings 都集中在 1-2 条 rule → 规则设计偏频

---

## 八、时间预算与风险

### 预估时间（不计调试）
- Phase 1 (3 seed drafts, 并行): 5-8 min
- Phase 2 (6 cross-reviews, 并行): 10-15 min
- Phase 3 (synthesis): 5-10 min
- Phase 4 (Python validation): <1 min
- 合计：~25-35 min 的 LLM 时间，加上调试 1-2 天

### 风险清单
| 风险 | 概率 | 缓解 |
|---|---|---|
| Soul doc 太大超出 prompt 预算 | 高 | 按 module 选择性加载（如只加载 Module 3 决策框架 + Module 7 checklist），不全文 |
| LLM 输出 JSON schema 不规范 | 中 | 用 `_json_utils.parse_llm_json` |
| 语义去重误判（合并不该合并的） | 中 | Phase 3 输出带"可疑合并"标签给人工复核 |
| 合规：Agent 偏向扮演 | 中 | Prompt 模板强制"研究助手"口吻 + 输出扫描 `你是 [master]` 模式 |
| 三方共识太少（<6 条硬约束） | 低 | 说明 soul doc 粒度问题，这本身是有价值的诊断信号 |
| 阈值差异大无法自动合并 | 中 | 默认取严格值，flag 为 review |

---

## 九、为什么不用其他方案？

| 备选方案 | 为什么不选 |
|---|---|
| 直接写固定的 Principles.md（跳过辩论） | 违反 design-v2 "大师董事会生成"要求；也失去了验证 soul doc 粒度的机会 |
| 5 AI 辩论（用现成的 /ai-debate skill） | 过度。用 5 个独立 AI 辩论适合战略性问题；这里是从 3 个**确定**的方法论框架中提炼规则，不需要外部视角 |
| 单轮一次性合并（跳过 cross-review） | 跳过 cross-review 就失去"投票"机制，3/3 vs 2/3 没法区分 |
| 完全人工手写 | 人工工作量大且容易有偏见；AI 辅助合理 |
| 让 Agent 自由产出 principles 再合并 | 没有 schema 约束的 seed 难去重；结构化 seed 是必要的 |

---

## 十、验收判据（Done Criteria）

Pre-A 完成，当且仅当：

- [ ] `Principles/v1.0.md` 存在，含 4 个 category，至少 **10 条 principles**
- [ ] 至少 **6 条是 HARD（全票通过）**，不然说明一致性不足需诊断
- [ ] 每条 principle 有 `supporting_soul_doc_anchor` 或 `supporting_profile_factor`
- [ ] `Principles/v1.0.schema.json` 能被 Python 解析运行
- [ ] `PrinciplesEngine.evaluate()` 在 STD-001~005 上 pass ≥ 4
- [ ] `PrinciplesEngine.evaluate()` 在 ADV-* 上至少 1 个触发 warning
- [ ] `debate_log.md` 体现了真实的分歧（不是伪一致）
- [ ] `validation_report.md` 列出 ≥ 3 个 edge case 分析
- [ ] 合规扫描（grep 黑名单）无 HIGH 违规

---

## 十一、待决策点（需用户 / 审查 AI 确认）

1. **阈值冲突时取严格还是取中位数？** 本设计默认"取最严格"。
2. **三票 1/3 的 principle 去向**：丢弃 or 作为 master-specific 保留？
3. **Phase 1 seed 是否允许参考其他 master 的 profile？**（本设计：否，独立提案）
4. **Principles v1.0 是否需要人工审批才能成为 Layer 0**？（推荐：是）
5. **是否允许 principles 引用具体行业/公司名**？（推荐：否，保持抽象，通用）

---

## 十二、文件 / 代码影响面

**新建**：
- `scripts/soul/board_debate.py` — 辩论流程主脚本
- `scripts/soul/principles_engine.py` — Phase 4 验证引擎
- `scripts/soul/principles_engine_test.py` — pytest
- `Principles/` 目录（包含 v1.0.md, v1.0.schema.json, debate_log, 等）

**复用**：
- `scripts/soul/calibrate.py` 的 `run_agent()` 模式（合规模板）
- `scripts/soul/_json_utils.py` 的 `parse_llm_json`
- `src/souls/documents/current/*.md` (soul doc symlinks)
- `src/souls/profiles/*.json`
- `src/souls/calibration/cases.json` (Phase 4 输入)

**修改**：无（完全 additive）
