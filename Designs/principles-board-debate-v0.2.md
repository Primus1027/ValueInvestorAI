# Pre-A: Principles Board Debate — 设计 v0.2（对抗审查后修订）

> 状态：**待用户审批**
> 日期：2026-04-20
> 版本：v0.2（整合 v0.1 + 独立 AI 审查员 debate 后的修正）
> 取代：v0.1 (`Designs/draft-principles-board-debate-v0.1.md`)

---

## 零、一页 Executive Summary

**目标**：让 3 个"方法论对照研究员"Agent 从 W v1.1 / C v1.1 / Y v1.0 soul docs + profile.json 中提炼出 Principles v1.0.md，作为 Layer 0 硬约束喂给 MVP Agent。

**相比 v0.1 的关键变化**（全部由独立 AI 审查员指出）：

| 变化 | 原因 |
|---|---|
| **删除 Phase 4 validation** | PrinciplesEngine 和 company_data adapter 都不存在，Phase 4 是空转工程。延后到 MVP 接入 yfinance 后再做 |
| **Phase 2 从"每个 master 审其他"改为"中立对照研究员"** | 原设计有合规风险（同 calibrate.py 被拦截的同型错误）。新设计用单一中立视角对照三方 seeds |
| **阈值冲突改为"保留 variants"而非"取最严格"** | 原方案消灭了三位大师的视角多元性，违反 design-v2 |
| **HARD 严格收紧为 3/3（全票），2/3 移至独立文件** | 对齐 design-v2 明文"全票通过制" |
| **Phase 3 拆成 3a/3b/3c**（去重/投票/渲染） | 避免单 call 职责过载 |
| **Primary context 用 profile.json（43KB），soul doc 只做 RAG retrieval** | 解决 token 预算超支 + 选择性加载规则不明的问题 |
| **新增 Phase 2.5 revise 回合** | 让辩论名副其实（master 可以改立场） |
| **5 个 open questions 给出默认值 + rationale** | 不把决策推给下游 |
| **新增输出合规扫描**（regex + 语义） | Phase 2.5 + Phase 3 输出必过合规门 |

---

## 一、产出物（明确 contract）

| 文件 | 格式 | Pre-A 阶段状态 | MVP 之后的演化 |
|---|---|---|---|
| `Principles/v1.0.md` | Markdown，仅含 HARD（3/3）条款 | ✅ 本阶段产出 | Layer 0 主文件 |
| `Principles/v1.0.schema.json` | JSON，可被 Python import | ✅ 本阶段产出（schema 冻结，即便暂不执行） | MVP Agent import |
| `Principles/soul-level-preferences.md` | Markdown，含 2/3 和 1/3 条款 | ✅ 本阶段产出 | 归档，不进 Layer 0 |
| `Principles/debate_log_2026-04-20.md` | Markdown | ✅ 本阶段产出 | 归档 |
| `Principles/critique_matrix.jsonl` | JSONL | ✅ 本阶段产出 | 供未来 diff 用 |
| `Principles/company_data_contract.md` | Markdown（data schema 文档） | ✅ 本阶段产出（contract 冻结） | yfinance adapter 对齐 |
| ~~`Principles/validation_report.md`~~ | ❌ 延后到 Post-MVP | 等 yfinance 接入后做 |

---

## 二、修订后的四阶段（Phase 4 延后）

```
┌─────────────────────────────────────────────────────────┐
│ Phase 0: Context Preparation (Python, no LLM)            │
│  - 加载 3 份 profile.json 作为 primary context           │
│  - 为 soul doc 建立 section-level grep 索引             │
│    （按 H2/H3 切块，建 keyword → section 映射）         │
│  - 输出：prep/profile_context.json, soul_doc_index.json │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Independent Seed Drafts (并行 3 calls)          │
│  每位方法论研究助手独立提出 5-15 条 principle seeds      │
│  主 context = profile.json + soul doc 章节标题索引       │
│  可选 RAG = 对每条 claim 反向 retrieval soul doc 段落   │
│  └─→ prep/{w,c,y}_seed_principles.jsonl                  │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Comparative Analysis (1 call, 中立视角) ★重写   │
│  单个"方法论对照研究员"Agent，输入三方 seeds，输出每条   │
│  seed 的 stance matrix: supported_by_others / conflicts  │
│  此阶段不使用"{master} 的助手评审另一方"框架（合规）    │
│  └─→ prep/comparative_analysis.jsonl                     │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2.5: Revise Round (并行 3 calls, 可选 but 推荐)    │
│  每位 master 看到 comparative_analysis 后，决定是否      │
│  修改自己的 seeds（增/改/删），产出 revised seeds        │
│  └─→ prep/{w,c,y}_revised_principles.jsonl               │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3a: Semantic Deduplication (1 call)                │
│  聚类跨方同义 principles，输出 canonical clusters        │
│  保留每方原阈值（不取严格值）                            │
│  └─→ prep/canonical_clusters.jsonl                       │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3b: Vote Tally (Python, no LLM)                   │
│  对每个 canonical cluster 统计 support vote：            │
│    3/3 → HARD → 进 Principles/v1.0.md                    │
│    2/3 → SOFT → 进 Principles/soul-level-preferences.md  │
│    1/3 → DROP （不进 Principles 体系）                   │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3c: Document Rendering (Python + template)         │
│  把 clusters + votes 渲染成 Markdown / JSON schema       │
│  无 LLM，纯模板填充                                       │
└───────────────────┬──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase E: Compliance Scan (Python, no LLM)                │
│  对所有中间输出扫描："你是 [master]" / "I, Buffett"等    │
│  发现即 fail + 重跑对应 phase                            │
└─────────────────────────────────────────────────────────┘

[Phase 4 Validation — 延后到 MVP 接入 yfinance 后]
```

**修订后预算**：Phase 1 (3 并发) + Phase 2 (1) + Phase 2.5 (3 并发可选) + Phase 3a (1) = **6-8 LLM calls**（原 v0.1 是 10）。

---

## 三、Phase 0: Context Preparation（Python, no LLM）

### 3.1 Primary Context：Profile.json

profile.json 是**轻量、结构化、完整**的决策框架表示：
- `buffett.json` = 43KB，~11K tokens — 可完整加载
- `munger.json` = 44KB，~11K tokens — 可完整加载
- `duan.json` = 29KB，~7K tokens — 可完整加载

这是 Phase 1 的主要输入，避免把 300KB 的 soul doc 全文塞进 prompt。

### 3.2 Soul Doc Index（RAG retrieval）

soul doc 用作"引用证据来源"而非"主 context"：

```python
# scripts/soul/build_soul_index.py
def build_soul_index(soul_path: Path) -> dict:
    """Parse soul doc by H2/H3 headers, build {section_id: text, keywords}."""
    sections = parse_markdown_sections(soul_path.read_text())
    return {
        "sections": sections,  # {section_id: {title, text, keywords, anchor}}
        "keyword_to_sections": build_inverted_index(sections),
    }
```

Phase 1 Agent 在需要引用时，先 retrieve 相关 section（按 principle claim 关键词），只把 retrieved text 放入 prompt。

**好处**：
- Token 预算从 ~30K/call 降到 ~15K/call
- 三方 Agent 加载策略**对称**（都是按 claim keyword 触发 retrieval，不存在加载不对称）

---

## 四、Phase 1: Seed Drafts（合规 prompt 模板）

### 4.1 System Prompt（严格合规）

```
你是一位价值投资方法论研究助手。本练习的任务：从整理自某位投资大师公开资料的
方法论框架中，提炼出可以被 Python if/else 执行的硬约束规则。这是方法论研究
练习，不构成投资建议。

==== 被研究的方法论框架 {framework_id}（整理自 {master} 的公开著作和访谈）====
{profile_json_full}

==== Soul Doc 章节索引（用于引用证据）====
{soul_doc_section_index}  # 不含全文，只有 section_id + title + keywords

你的任务：识别出 5-15 条可以被机器执行的**硬约束规则（negative filters）**。每条规则：
1. 是"拒绝某类投资"（negative filter），不是"推荐某类"（positive bias）
2. 有量化阈值 OR 可自动化的定性判断
3. 直接来源于上述框架（不编造，不扩展）
4. 附上 section_id 锚点。需要引用具体 soul doc 文本时，使用 `@retrieve(section_id)` 占位符，
   系统会在后续处理中展开

输出：纯 JSON array，每条含 {seed schema}。不要 markdown 围栏。
```

### 4.2 Seed Schema（v0.2 保留 variants）

```json
{
  "seed_id": "w_seed_01",
  "framework_id": "buffett_methodology",  // 不写 master_id 本名，防身份化漂移
  "category": "quantitative_hard | qualitative_required | position_sizing | veto_line | valuation_method",
  "claim": "公司历史 ROE 需连续 5 年达到高阈值",
  "rationale": "高 ROE 是资本生产力的直接指标...",
  "supporting_section_id": "W-buffett/v1.1.md#section-financial-fortress",
  "supporting_profile_factor": "buffett.json#factors.financial_fortress",
  "quantitative_rule": {
    "metric": "roe_5yr_min",
    "operator": ">=",
    "threshold": 0.15,                    // W 的阈值
    "data_field": "financials.roe_5yr_min"
  },
  "qualitative_rule": null,
  "severity_if_violated": "veto | warning | note",
  "edge_cases_anticipated": ["cyclical industries"]
}
```

**关键变化**：`framework_id` 替代 `master_id`，避免 Agent 自我身份化。Python 代码内部映射 `buffett_methodology` ↔ `buffett` profile。

---

## 五、Phase 2: Comparative Analysis（单中立 Agent）★重写

### 5.1 为什么用单中立 Agent

v0.1 的设计"W 助手评审 C+Y"在合规上是炸弹——因为 LLM 会理解为"Buffett 评价 Munger 的方法论"，第一人称漂移几乎必然。

v0.2 改用**一个不绑定任何 master 的中立对照研究员**：

```
你是方法论对照研究员。下面是三个独立的价值投资方法论框架（frameworks A, B, C）
各自提出的 principle seeds。请以中立视角标注每条 seed：

- supported_by: [A, B, C] 中哪些框架有同义 principle
- conflicts_with: 哪些框架有反对的 principle（引用对方 seed_id + 冲突类型）
- framework_specific: 是否只有单一框架支持（不代表 "wrong"，只代表个人偏好）

你的任务不是评价哪个框架"对"，而是做对照映射。
输出 JSONL，一行一个 stance judgment。
```

**注意**：framework A/B/C 是匿名标签，不给 Agent 透露对应哪位 master。减少身份化漂移。

### 5.2 Stance Output Schema

```json
{
  "seed_id": "w_seed_01",
  "framework_id": "A",  // 匿名
  "claim_normalized": "High sustained ROE required",
  "supported_by": ["B"],
  "conflicts_with": [],
  "framework_specific_aspects": ["threshold differs: A=0.15, B=0.12"],
  "synthesis_note": "三个框架都认同高 ROE 原则，阈值差异反映各自风险偏好"
}
```

---

## 六、Phase 2.5: Revise Round（可选但推荐）

### 6.1 Motivation

真实董事会辩论的价值不在投票，在**看到别人的观点后改变立场**。v0.1 缺这一步，把辩论降级为投票。

### 6.2 Revise Prompt

```
你是价值投资方法论研究助手（研究 framework {X}）。你之前提出了以下 seeds：
{original_seeds}

下面是中立对照研究员对三个框架的映射分析：
{comparative_analysis}

根据对照分析，你可以选择：
(a) 保留原 seed 不变
(b) 修改 seed（调整 threshold / 扩展 edge case / 改 claim）
(c) 撤回 seed（如果觉得对照分析指出的问题让这条不再适合作为硬约束）
(d) 新增 seed（如果对照过程启发了新想法）

对每个变更写明 rationale。输出 JSONL，每行是一个 revision 决策。
```

### 6.3 如果某 framework 大改 seeds 会怎样？

- 小改（<30% seeds 变动）：正常进 Phase 3
- 大改（>30%）：flag 为 "framework instability"，可能需要用户看一眼 —— 但不阻塞 pipeline

---

## 七、Phase 3: Synthesis（拆成 3a/3b/3c）

### 7.1 Phase 3a：Semantic Deduplication（1 LLM call）

```
你是辩论记录员。下面是三个框架的（revised）seeds：
{all_revised_seeds}

任务：识别跨框架的语义等价 principle，聚成 canonical clusters。

对每个 cluster 输出：
{
  "cluster_id": "cl_01",
  "canonical_claim": "高 ROE 持续性 required",
  "category": "quantitative_hard",
  "variant_seeds": [
    {"seed_id": "w_seed_01", "threshold": 0.15},
    {"seed_id": "c_seed_03", "threshold": 0.12},
    {"seed_id": "y_seed_05", "threshold": 0.07}
  ],
  "thresholds_diverge": true  // 如有，false 如一致
}

严格要求：不合并语义不等价的 seeds。阈值差异超过 50% flag 为"suspicious"，
由人工确认是否真同义。
```

### 7.2 Phase 3b：Vote Tally（Python，no LLM）

```python
# scripts/soul/principles_synthesizer.py
def tally(clusters: list) -> dict:
    final = {"hard": [], "soft": [], "dropped": []}
    for cluster in clusters:
        support_count = len(cluster["variant_seeds"])
        if support_count == 3:
            final["hard"].append(cluster)
        elif support_count == 2:
            final["soft"].append(cluster)
        else:
            final["dropped"].append(cluster)
    return final
```

### 7.3 Phase 3c：Document Rendering（Python + Jinja2）

从 `tally` 结果 + 模板渲染 4 个产出文件：
- `Principles/v1.0.md` — 只含 HARD
- `Principles/soul-level-preferences.md` — 含 SOFT
- `Principles/v1.0.schema.json` — HARD 的 machine-executable form
- `Principles/debate_log_2026-04-20.md` — 全过程汇总

---

## 八、Phase E: Compliance Scan（Python, no LLM）

### 8.1 扫描规则

```python
# scripts/soul/compliance_scan.py
FORBIDDEN_PATTERNS = [
    r"你是\s*(Buffett|Munger|段永平|Warren|Charlie|巴菲特|芒格)",
    r"You are (Warren|Charlie|Duan)",
    r"I, (Buffett|Munger|Duan)",
    r"我作为\s*(巴菲特|芒格|段永平)",
    r"(保持|keep).*(Buffett|Munger|段永平).*(风格|口吻|personality|voice)",
    r"(像|think like|as if you were|impersonate)\s*(Buffett|Munger|段永平|Warren|Charlie)",
]

# 白名单（不触发的合法用法）
WHITELIST_PHRASES = [
    "think like owners",  # 投资概念，指被投公司管理层
    "does NOT impersonate",  # 合规声明本身
]

def scan(text: str) -> list:
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ctx = text[max(0, match.start()-50):match.end()+50]
            if not any(wl in ctx for wl in WHITELIST_PHRASES):
                violations.append({"pattern": pattern, "match": match.group(), "context": ctx})
    return violations
```

### 8.2 什么时候扫描

- Phase 1 每个 seed draft 的 rationale 字段
- Phase 2 comparative_analysis 的 synthesis_note 字段
- Phase 2.5 每个 revise 的 rationale
- Phase 3a canonical_claim 字段
- 最终 `Principles/v1.0.md` 的全文

**违规处理**：自动 retry 一次，附加 explicit negative constraint in prompt。连续失败 → 冻结 pipeline + 报错给用户。

---

## 九、Open Questions 的默认回答

| # | Question | 默认回答 | Rationale |
|---|---|---|---|
| 1 | 阈值冲突取严格还是中位数？ | **保留 variants，不取单值** | 违反多元主义；variants 交给 Layer 1 Agent 按分析视角选 |
| 2 | 1/3 principle 去向？ | 归 `soul-level-preferences.md`，不进 Principles 体系 | 对齐 design-v2 "全票通过制" |
| 3 | Phase 1 seed 能否参考其他 master？ | **否** | 独立提案才有投票意义 |
| 4 | v1.0 需要人工审批才能成为 Layer 0？ | **是** | Layer 0 是关键护栏，AI 自动化不行 |
| 5 | Principles 引用具体行业/公司名？ | **否** | 保持抽象，Layer 0 应通用 |
| 6 | v1.0 → v2.0 升级触发条件？ | 重大 soul doc 版本 bump（v2.x）或 6 个月到期，以先到为准 | 防止无休止微调 |
| 7 | 三 Agent 用不同模型（Doubao for Y）？ | **v1.0 全用 Claude Sonnet 4.6** | 控制单变量；未来可改 |

---

## 十、验收判据（Done Criteria）v0.2

Pre-A 完成，当且仅当：

- [ ] `Principles/v1.0.md` 存在，含 HARD（3/3）条款至少 **6 条**（不足说明一致性问题）
- [ ] `Principles/soul-level-preferences.md` 存在，含 SOFT（2/3）条款
- [ ] 每条 HARD 都有 `supporting_section_id` 或 `supporting_profile_factor` 锚点
- [ ] `Principles/v1.0.schema.json` 通过 JSON Schema validator
- [ ] `Principles/company_data_contract.md` 明确列出未来 yfinance adapter 需提供的字段
- [ ] `Principles/debate_log.md` 体现真实分歧（不是伪一致）
- [ ] `Phase E` 合规扫描：0 violations
- [ ] 人工 sign-off：用户确认 Principles/v1.0.md 可作为 Layer 0
- ~~[ ] PrinciplesEngine.evaluate() 在 STD-001~005 pass ≥ 4~~ **← 延后到 MVP 接入 yfinance 后补做**

---

## 十一、风险清单 v0.2

| 风险 | 概率 | 缓解 |
|---|---|---|
| 即便用 profile.json 主 context，Phase 1 仍超预算 | 中 | Phase 0 提前测量 token count，超过 50K 再做章节选择性加载 |
| Phase 2 中立 Agent 仍能反推出 A/B/C 是谁，触发身份化 | 中 | 匿名标签 + 合规扫描兜底 |
| 三方 revise 后产生新的 1/3 孤儿 principles | 低 | 正常现象，归 soul-level-preferences |
| Phase 3a 语义去重误判（合并不该合并的） | 中 | thresholds_diverge > 50% flag + 人工 review |
| HARD 条款不足 6 条 | 中 | v0.2 验收判据明确"不足说明一致性问题" → 诊断 signal，正常 exit 流程 |
| 用户 sign-off 阶段对某条 HARD 有异议 | 中 | 写 v0.1.1 patch 机制，只针对单条 revise |

---

## 十二、时间预算 v0.2

- Phase 0 (Python, 索引构建): <5 min
- Phase 1 (3 calls 并行): 8-12 min
- Phase 2 (1 call): 3-5 min
- Phase 2.5 (3 calls 并行，可选): 8-12 min
- Phase 3a (1 call): 3-5 min
- Phase 3b (Python): <1 min
- Phase 3c (Python rendering): <1 min
- Phase E (Python scan): <1 min
- **合计 LLM 时间：23-36 min**，调试 1-2 天

Phase 4 Validation **延后**，不计入 Pre-A 预算。

---

## 十三、文件影响面 v0.2

**新建**：
- `scripts/soul/board_debate.py` — 主调度脚本
- `scripts/soul/build_soul_index.py` — Phase 0 索引构建
- `scripts/soul/principles_synthesizer.py` — Phase 3b/3c（Python）
- `scripts/soul/compliance_scan.py` — Phase E
- `Principles/` 目录

**复用**：
- `scripts/soul/_json_utils.py`（E 阶段刚建好）
- `scripts/soul/calibrate.py` 的 subprocess CLI 模式 + 合规 prompt 基础
- `Designs/prompt-framing-guidelines.md` 的合规规则

**不修改**：现有 soul doc / profile / cases.json

---

## 十四、审查记录

本 v0.2 是 v0.1 经过独立 AI Plan agent 对抗性审查后的修订。完整审查报告在 `debate_log_2026-04-20.md`（将在 Pre-A 执行时写入 `Principles/` 目录）。v0.2 所做的 9 处变更全部来自该审查的 Part 1-6 建议，已逐项对应。

**审查员整体评级**：v0.1 "需要修改后执行"。v0.2 的变更已消除所有 3 个 fatal flaws 和 5 个 serious issues 中的 4 个（S3 validation 循环性通过延后 Phase 4 规避；S5 Phase 3 拆分解决；S1 soul doc 加载通过 Phase 0 索引解决；S2 阈值取严解决；S4 revise 回合解决）。
