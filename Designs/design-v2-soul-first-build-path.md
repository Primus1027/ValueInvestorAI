# ValueInvestorAI — Design v3: Soul-First Build Path

> 最终版设计文档，整合 /office-hours + /plan-ceo-review + /plan-eng-review 三轮审查 + 灵魂封装架构设计（2026-04-15/16 session）的全部决策。
> 日期：2026-04-16
> 状态：APPROVED
> 取代：design-v2 (2026-04-15)

---

## 一、Problem Statement

构建一个 AI 价值投资系统，目标是在 10 年内跑赢指数。系统产出投资决策（具体买入价格和仓位比例）和内容（月度股东信 + 分析文章）。

**核心论点：** AI 在价值投资中的优势不是计算能力，而是情绪中性 + 研究耐力。AI 不会在市场崩盘时恐慌，也不会在读第 200 份年报时感到无聊。

**10x 愿景：** 一个完全由 AI 运营的 Berkshire Hathaway。

**关键洞察（来自创始人）：**
- 大多数"价值投资者"失败不是因为交易时的恐惧/贪婪，而是因为**研究阶段的畏难和无聊**，导致在没有真正看懂公司之前就做出决策
- AI 的另一个优势：它不会因为分析大量资料而感到厌倦，能真正完成人类放弃的深度研究
- 投资大师的灵魂封装 IS the process of discovering investment criteria，标准从深度学习中涌现，不是预先定义的
- "保持谦逊 — 在没有做完所有功课之前，谁也别说自己了解价值投资的全部决策标准"

---

## 二、3 位投资大师

> CEO review 决定：删除李录（公开资料不足以校准）。保留 3 位。

| 大师 | 角色 | 核心框架 | 资料来源 | 模型 |
|------|------|----------|---------|------|
| **巴菲特** | 主投资人 | 所有者收益、护城河分析（品牌/成本/网络/转换）、管理层质量、安全边际、能力圈 | 致股东信 1957-2025 (Berkshire PDF), CNBC Archive | Claude / GPT |
| **芒格** | 对抗性检查 | 多学科思维模型、逆向思维、心理学偏误、检查清单 | 千页合集 PDF, 公开演讲稿 | Claude / GPT |
| **段永平** | 中国视角 | 商业模式简洁性、"做对的事情"、消费品牌评估 | 段永平投资问答录 (雪球特别版 PDF) | Doubao（中文语料权重更高）/ Claude |

**模型选择原则：** 按语料语言分配权重。英文语料为主的大师用 Claude/GPT；中文语料为主的用 Doubao。具体权重在 Phase 1 校准中调优。

**大师的双重角色：**
1. **分析器：** 深度分析通过筛选的公司
2. **筛选器：** 每个大师先做快速判断（"在我的能力圈内吗？值得深入分析吗？"），2/3 大师同意才进入深度分析。标准从大师辩论中涌现，不是单独的规则引擎。

---

## 三、技术架构

### 技术栈
- **语言：** Python（金融数据生态原生：OpenBB, yfinance, edgartools, FinanceToolkit）
- **数据库：** SQLite + JSON 文件（Phase 0-2）；Phase 2+ 当累积分析 >50 个时加 vector store
- **LLM：** Claude API + GPT API + Doubao API
- **结构化输出：** 使用 Claude/GPT 的 tool_use / function_calling，模型层面保证 JSON schema 合规
- **数据层：** OpenBB (统一抽象), yfinance, SEC EDGAR, Finnhub

### 灵魂封装架构（五层防线）

> 核心设计原则：LLM 天然向"通用分析师"漂移（训练数据中 100 万篇华尔街报告 vs 48 封巴菲特股东信）。单靠 prompt 无法对抗这种统计拔河。必须用代码层硬约束隔离 LLM 的漂移风险。

```
公司数据
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 0: PRINCIPLES (代码执行, 非 LLM)                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Principles.md — 投资硬约束 checklist                    │ │
│  │  量化约束: ROE>15%, 10年中≥8年盈利, 杠杆<3x, FCF>0...   │ │
│  │  定性必查: 能力圈(2/3大师同意), 可解释商业模式, 管理层诚信 │ │
│  │  仓位约束: 单只≤15%, 总持仓≤20只                         │ │
│  │  → Python if/else 执行, LLM 无法绕过                     │ │
│  │  → 不通过 = 直接否决, 不进入 LLM 分析                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│  来源: 大师董事会生成, 认知驱动更新(非市场驱动), 全票通过制    │
└─────────────────────────────────┬───────────────────────────┘
                                  │ 通过
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: SOUL PROMPT (LLM, 动态组装)                        │
│  ┌────────────┐ ┌───────────┐ ┌──────────────┐              │
│  │ 身份+哲学   │ │ 决策框架   │ │ 防漂移规则   │              │
│  │ ~800 tok   │ │ 8因子详述  │ │ 8-11条"不做" │              │
│  └────────────┘ │ ~2000 tok │ │ ~600 tok     │              │
│  ┌────────────┐ └───────────┘ └──────────────┘              │
│  │ Few-shot   │ ┌──────────────────────────┐                 │
│  │ 按相关性选  │ │ RAG 一手资料锚点 (Ph 1b) │                 │
│  │ ~3000 tok  │ │ 大师原话作为 context       │                 │
│  └────────────┘ └──────────────────────────┘                 │
│  → 每位大师 ~7000 tokens system prompt                        │
│  → tool_use 保证结构化 JSON 输出                              │
└─────────────────────────────────┬───────────────────────────┘
                                  │ 分析结果
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: OUTPUT VALIDATION (代码执行, 非 LLM)               │
│  → 检测漂移信号: DCF语言、技术分析术语、短期目标价、          │
│    conviction scoring、季度导向                               │
│  → 检测表演性一致: 三位大师输出是否缺乏实质差异               │
│  → 违规 = 重新生成或标记人工审查                              │
└─────────────────────────────────┬───────────────────────────┘
                                  │ 通过
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: RAG ANCHORING (Phase 1b, LLM + 检索)              │
│  → 分析苹果时, 检索巴菲特实际写过的关于苹果的股东信段落      │
│  → 一手资料原文作为 context, 锚定大师真实思维                │
│  → 原文锚点比规则锚点强 10x (不是规则说"不做DCF",            │
│    而是巴菲特自己说"我从来不做 DCF")                          │
└─────────────────────────────────┬───────────────────────────┘
                                  │ 最终分析
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: CALIBRATION REGRESSION (定期, 反馈循环)            │
│  → 每 N 次分析后, 自动跑校准案例                             │
│  → 5 常规 + 3 对抗性 + 2 危机场景                            │
│  → 准确率下降 = 漂移发生 → 触发框架微调                      │
│  → 校准结果反馈回 Layer 1 (prompt 优化)                      │
│    和 Layer 0 (Principles 审议输入)                           │
└─────────────────────────────────────────────────────────────┘
```

**关键设计决策：Layer 0 和 Layer 2 是代码层，LLM 无法绕过。即使 LLM 某次"创新"地想推荐一家 ROE 5% 的公司，硬约束会直接否决，根本不给 LLM 辩解的机会。**

### Principles.md — 投资硬约束

> **核心理念（来自创始人）：** Principles 的进化应该由**认知驱动**，不是由市场驱动。如果 Principles 基于"上个月亏了"来调整，本质上就是让恐惧/贪婪通过后门进入系统。

#### Principles 的结构

```markdown
# ValueInvestorAI Investment Principles
# Version: v0.1
# Status: ACTIVE

## 量化硬约束 (代码执行, 不通过=直接否决)
1. 能力圈: 至少 2/3 大师判定"在我能力圈内"
2. 商业模式可理解: 能用 3 句话向外行解释清楚
3. 盈利历史: 过去 10 年中至少 8 年盈利
4. ROE: 近 5 年平均 ROE > 15%（无过度杠杆）
5. 护城河: 至少识别出一种可持续竞争优势
6. 管理层: 无重大诚信问题记录
7. 估值: 当前 PE < 合理估值上限（大师共识）
8. 债务: 净债务/EBITDA < 3x
9. 自由现金流: 近 3 年 FCF 为正
10. 仓位: 单只不超过总组合 15%

## 卖出触发条件
1. 原始投资论点被永久性破坏（不是暂时困难）
2. 估值远超合理范围（PE > 2x 合理上限）
3. 管理层出现诚信问题
4. 发现当初分析有重大遗漏
```

#### Principles 的更新机制

**合法的修改输入（仅限）：**
- ✅ 新发现的大师一手材料（尤其是思想变化，Type B 变化 = 大师自我纠正）
- ✅ 新的价值投资学术研究或深度分析
- ✅ 校准测试中发现的系统性偏差
- ❌ 上个月的投资表现
- ❌ 当前市场环境/情绪
- ❌ 新闻事件
- ❌ 某只股票涨了/跌了

**修改共识机制：**
1. 提案者必须引用一手材料原文（不能凭"感觉"）
2. **三位大师全票同意**（不是 2/3，是 3/3）
3. 创始人审核并确认
4. 修改记录必须包含：触发材料引用、修改前后差异、每位大师同意理由
5. 版本历史 git tracked

**材料扫描 vs Principles 审议：**
- 材料扫描：高频（每两周，发挥 AI 优势）
- Principles 审议：仅在有合法触发时发生（可能几个月不变）
- 常规议程是"有没有新材料值得学习"，不是"要不要改规则"

### Soul Profile — 大师身份数据

每位大师一个结构化 JSON 文件，存储在 `src/souls/profiles/` 目录，git tracked，人类可读可编辑。

```
src/souls/
├── profiles/           ← 每位大师的身份+哲学+框架 (JSON)
│   ├── buffett.json    (42K, 9因子, 11防漂移规则, 7案例, 15真实语录)
│   ├── munger.json     (43K, 9因子, 10防漂移规则, 6案例, 23心智模型)
│   └── duan.json       (29K, 9因子, 10防漂移规则, 7案例, 16中文语录)
├── calibration/        ← 校准案例集
│   └── cases.json      (23K, 5常规+3对抗性+2危机场景)
└── examples/           ← Few-shot 推理链条 (Phase 1b 扩展)
```

**Profile 的 JSON Schema 核心字段：**
- `identity`: 身份、哲学、投资时间线、情绪特征、能力圈
- `decision_framework`: 带权重的决策因子（权重之和 ≈ 1.0）
- `reasoning_patterns`: 分析序列、特征问题、真实语录、心智模型
- `anti_drift_rules`: "不做"清单 + 检测方法
- `few_shot_examples`: 真实投资案例的完整推理链条

**Prompt Composer 运行时组装：**
```python
system_prompt = compose(
    identity(master),                          # 你是谁
    philosophy(master),                        # 核心哲学
    decision_framework(master),                # 决策因子+权重
    anti_drift_rules(master),                  # 不做清单
    select_relevant_examples(master, company), # 按相关性选 few-shot
    retrieve_source_quotes(master, company),   # 一手资料 RAG 锚 (Phase 1b)
)
# 组装后 ~7000 tokens per master, 约一封完整股东信长度
```

### SQLite Schema

```sql
-- 大师分析结果（跨 session 累积）
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    master_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'screen' | 'deep' | 'update'
    input_snapshot TEXT NOT NULL, -- 输入数据快照 (JSON)
    output TEXT NOT NULL,         -- 结构化分析结果 (JSON)
    confidence TEXT,
    reasoning_summary TEXT
);

-- 校准测试结果
CREATE TABLE calibration_runs (
    id INTEGER PRIMARY KEY,
    master_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    expected_decision TEXT,
    actual_decision TEXT,
    score REAL,
    reasoning_match TEXT,
    notes TEXT
);

-- 论点演变时间线
CREATE TABLE argument_timeline (
    id INTEGER PRIMARY KEY,
    ticker TEXT NOT NULL,
    master_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    thesis TEXT NOT NULL,
    delta_from_previous TEXT,
    trigger TEXT
);

-- Principles 版本历史
CREATE TABLE principles_history (
    id INTEGER PRIMARY KEY,
    version TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    changes TEXT NOT NULL,       -- JSON: 修改前后差异
    trigger_material TEXT,       -- 触发修改的材料引用
    votes TEXT NOT NULL,         -- JSON: 每位大师的投票+理由
    founder_approved BOOLEAN
);
```

### 系统运行流程

```
候选公司列表
    │
    ▼
[Layer 0: Principles 硬约束] ──否决──→ REJECTED (记录原因)
    │ 通过
    ▼
[大师快速筛选] 2/3 同意 ──不通过──→ FILTERED (记录原因)
    │ 通过
    ▼
[Layer 1: 大师深度分析] × 3 位大师并行
    │
    ▼
[Layer 2: 输出验证] ──漂移──→ 重新生成或标记人工审查
    │ 通过
    ▼
[跨大师综合引擎] 组合视角 + 分歧检测
    │
    ▼
[数据验证层] 结构化 JSON → 对比源 API 数据
    │
    ├──→ [决策引擎] 买/卖推荐 + 人工审批门
    ├──→ [内容引擎] 月度股东信 + 分析文章
    ├──→ [审计追踪] 论点演变 + 反投资组合
    └──→ [自我改进] 结果追踪 → 复盘 → 回馈 Memory
```

### 成本模型

价值投资不是暴力扫描所有公司。真实过程是漏斗：

0. **Principles 硬约束过滤（零成本）：** 量化标准代码执行，过滤 ~90% 候选。
1. **大师快速筛选（近零成本）：** 3 位大师做快速判断（~$0.01/公司/大师）。2/3 同意才进入深度分析。
2. **深度分析（LLM 成本）：** 每月仅 2-5 家新公司需要完整的多大师分析。
3. **持续扫描（低成本）：** 定期轻量扫描新进入投资范围的公司。

**月预算：** ~$50-100/月 LLM APIs。

---

## 四、分阶段实施计划

### Phase 0: 基础搭建（Week 1）— ✅ 大部分已完成

| 任务 | 内容 | 状态 |
|------|------|------|
| 项目初始化 | git repo | ✅ 已完成 |
| 资料收集 | 下载大师一手资料 | ✅ 81文件/41MB |
| 灵魂封装 Phase 1a | 三位大师 Soul Profile + 校准案例 | ✅ 137K 结构化数据 |
| Memory 层 | SQLite schema + 读写接口 | ⬜ 待开发 |
| Data 层 | OpenBB/yfinance 接入 | ⬜ 待开发 |
| Python 项目结构 | 包管理、依赖、目录规范 | ⬜ 待开发 |

**Exit Criteria:**
- [x] Git repo 初始化
- [x] 3 位大师 Soul Profile JSON 生成（Phase 1a）
- [x] 校准案例集设计（5 常规 + 3 对抗性 + 2 危机场景）
- [x] P0 源资料下载（48年股东信、Wesco信、投资问答录等）
- [ ] Memory 接口可读写（SQLite schema 实现）
- [ ] Data 层可获取基本财务数据
- [ ] Python 项目结构搭建

### Phase 1: 灵魂封装 + 校准 + Principles（Week 2-4）

**Phase 1a（✅ 已完成）：** AI 从训练数据生成初版框架
- 三位大师 Profile JSON (buffett/munger/duan)
- 决策因子 + 权重 + 防漂移规则 + few-shot 案例

**Phase 1b：一手资料深化**
- RAG 索引：将 48 年股东信、演讲稿、投资问答录构建为检索库
- AI 对比 Phase 1a 框架与一手资料，标注"框架里缺了什么"
- 用一手资料中的具体案例扩充 few-shot examples
- 重跑校准案例，量化 Phase 1a vs 1b 的提升

**Phase 1c：生成 Principles v0.1**
- 从三个 Profile 的 decision_framework 中提取可量化标准
- 校准案例验证：确保 Principles 不会误杀经典投资（如 1988 可口可乐）
- 创始人审核确认
- 实现 Principles 硬约束检查的 Python 代码

**校准协议：**
- 5 个常规历史案例：方向性判断
- 3 个对抗性案例：哲学与行为矛盾（测试推理，不是记忆）
- 2 个危机场景：极端市场 + 新闻轰炸，验证纪律
- **评分标准：** 方向匹配(40%) + 推理质量(30%) + 大师差异化(20%) + 抗漂移(10%)

**结构化输出 Schema（tool_use）：**
```json
{
  "ticker": "AAPL",
  "master": "buffett",
  "principles_check": {"passed": true, "violations": []},
  "recommendation": "buy",
  "fair_value_range": [150, 180],
  "moat_type": "brand + ecosystem",
  "moat_durability": "high",
  "key_risks": ["regulatory pressure", "China dependency"],
  "position_size_suggestion": "5-8% of portfolio",
  "confidence": "high",
  "reasoning_summary": "...",
  "anti_drift_self_check": {"violations": [], "clean": true}
}
```

**Exit Criteria:**
- [ ] 校准基线建立（Phase 1a 纯 prompt 得分）
- [ ] Phase 1b RAG 锚点实现 + 重测得分提升
- [ ] Principles v0.1 生成并通过校准验证
- [ ] Principles 硬约束 Python 代码实现
- [ ] 三位大师分析同一家公司产出可测量的不同视角
- [ ] 对抗性案例：能解释哲学演化而非死板套用历史
- [ ] 危机场景：恐慌环境下保持纪律

### Phase 2: 分析引擎（Week 5-8）

Phase 1 校准通过 + Principles v0.1 就位后启动。

- **Principles 过滤：** 候选公司先过硬约束 checklist（代码执行）
- **大师筛选：** 通过硬约束的公司过 3 位大师快速判断，2/3 同意进入深度
- **深度分析：** 每月 2-5 家公司，三位大师并行 + 数据验证
- **输出验证：** 每次分析自动检测漂移信号
- **跨大师综合：** 组合视角 + 分歧检测
- **内容生成：** 论点+证据+大师视角+分歧
- **月度股东信 + 反投资组合 + 论点演变时间线 + 审计追踪**
- **首次材料扫描：** 搜索大师新公开材料，评估是否触发 Principles 审议

**Exit Criteria:**
- [ ] 分析流水线连续运行 3 周
- [ ] ≥10 家公司分析完成
- [ ] 内容通过创始人审核（≤2 轮修改）
- [ ] Principles 经过实战验证（没有误杀好公司）
- [ ] 产出第一封月度股东信

### Phase 3: 投资决策（Week 8+）

**前置条件：** 创始人个人法律舒适度。

- 具体买入价格 + 组合配置比例（必须通过 Principles 全部硬约束）
- 人工审批门（创始人审核每笔买卖）
- 持仓追踪 + 论点监控
- **自我改进反馈循环：** 结果追踪 → 复盘 → 模式识别 → 回馈 Memory
- **Principles 持续治理：** 认知驱动审议（新材料触发，非市场触发）

---

## 五、前提假设

1. AI 可以学习并持续应用价值投资原则
2. 人类在价值投资中失败是因为情绪 + 研究疲劳 — AI 消除两者
3. 内容生产和投资决策有协同效应 — 写文章就是阐述投资逻辑
4. 创始人跳过虚拟组合，直接用真实资金（$100K），每笔交易需人工审核
5. Memory 架构是关键技术挑战 — AI 必须学会什么该记、什么该忘
6. 多大师的价值不在共识，在于**分歧检测** — 分歧强制更深入分析
7. 投资过程从第一天就是产品 — 可见的自我进化过程本身就有价值
8. **AI 默认会"污染"为股票研究模式** — 五层防线（尤其是 Principles 硬约束）的核心目的就是防止模式污染
9. **Principles 的进化由认知驱动，不是市场驱动** — 让恐惧/贪婪通过后门进入系统等同于系统失败

---

## 六、不做列表

- SEC 投资顾问注册（推迟到获得法律意见）
- LLM 微调（仅在 RAG/prompt 不够时探索）
- 券商 API 集成（所有交易手动执行）
- 多平台发布基础设施（Phase 1-2 仅个人使用）
- 回测引擎（不需要 — 前瞻性决策）
- 移动应用 / Web 仪表盘（先 CLI）
- 做空 / 期权策略（仅做多）
- 社区输入决策（社区仅围观）
- 李录独立大师（资料不足以校准，已删除）
- Conviction scoring 系统（股票研究模式，不是价值投资模式）
- 向量数据库（Phase 2+ 当 >50 个分析时再加）
- 基于投资表现修改 Principles（认知驱动，不是市场驱动）
- 月度定期 Principles 修改会议（仅在有新一手材料触发时审议）

---

## 七、成功标准

- [ ] 3 位大师通过校准测试（常规 ≥4/5 + 对抗性案例 + 危机场景）
- [ ] Principles v0.1 就位，经过校准验证不误杀经典投资
- [ ] ≥10 家公司分析，有具体买/持/卖 + 价格目标 + 配置比例
- [ ] 分析引擎自主运行 4+ 周
- [ ] 创始人审核推理后愿意用真实资金投资
- [ ] Memory 系统展示学习能力
- [ ] 至少一个案例中大师分歧导致了比任何单个大师更好的决策
- [ ] 反投资组合中至少追踪 5 家被拒绝的公司
- [ ] 产出第一封月度股东信
- [ ] Principles 经历至少一次材料扫描未触发修改（稳定性验证）

---

## 八、失败模式

| 失败 | 影响 | 缓解措施 |
|------|------|---------|
| 数据 API 不可用 | 分析停滞 | 回退到缓存数据（24h 陈旧对价值投资可接受） |
| LLM 幻觉财务数据 | 错误投资 | 结构化输出 + 自动对比源 API 数据 |
| LLM 向通用分析师漂移 | 失去大师特色 | **五层防线：Principles硬约束 + Soul Prompt + 输出验证 + RAG锚 + 校准回归** |
| LLM 拒绝回答 | 分析不完整 | 检测拒绝 → 重试或标记人工处理 |
| 表演性一致 | 无独立视角 | 强制独立信息子集 + Layer 2 差异化检测 |
| Principles 被市场情绪修改 | 系统失去纪律 | **修改门槛：需一手材料引用 + 3/3全票 + 创始人确认** |
| Memory 丢失 | 累积学习丢失 | SQLite 每日备份 + 完整性检查 |
| 成本超支 | 月预算超支 | 硬消费上限；Principles 过滤 ~90% 候选减少 LLM 调用 |

---

## 九、并行开发策略

```
已完成:
  ✅ Lane B: 大师源资料收集 (81文件/41MB)
  ✅ Phase 1a: Soul Profile + 校准案例设计

当前:
  Lane A (并行): Memory 层 (SQLite) + Data 层 (yfinance/OpenBB) + Python 项目结构
  Lane C (串行): 校准测试执行 → Phase 1b RAG → Principles v0.1 生成

下一步:
  Lane D: Principles 硬约束代码 + 输出验证代码
  Lane E: 分析引擎流水线 (依赖 Lane A + Lane C)
```

---

## 十、Open Questions

1. **模型权重调优：** Doubao 在段永平上的权重具体怎么调？Phase 1 校准中对比同一案例的输出质量
2. **外部叙事定位：** AI Debate 建议 "投资决策风格仿真" 替代 "灵魂封装"。内部使用 "decision-style modeling"
3. **段永平 PDF 来源验证：** 雪球特别版是社区编辑，需验证完整性
4. **Principles v0.1 冷启动：** 从 Profile 提取量化标准 → 校准验证 → 创始人确认。需要区分量化硬约束（代码执行）和定性必查项（LLM 评估但必须回答）
5. **材料扫描频率：** 设计为每两周，但执行方式（scheduled task vs 手动触发）待定

---

## 十一、关键设计决策日志

| # | 决策 | 日期 | 来源 | 结论 |
|---|------|------|------|------|
| 1 | Tech Stack | 04-05 | PROJECT_VISION | Python |
| 2 | LLM 配置 | 04-05 | PROJECT_VISION | Claude + GPT + Doubao 双模型 |
| 3 | 市场数据 | 04-05 | PROJECT_VISION | 免费 API + 开源库优先 |
| 4 | 大师数量 | 04-14 | CEO Review | 3 位（删除李录） |
| 5 | Memory | 04-15 | Eng Review | SQLite + JSON → Phase 2+ vector |
| 6 | 结构化输出 | 04-15 | Eng Review | tool_use / function_calling |
| 7 | 筛选机制 | 04-15 | Eng Review | 大师即筛选器，无独立规则引擎 |
| 8 | 内容格式 | 04-14 | CEO Review | 月度股东信为旗舰 |
| 9 | 灵魂封装架构 | 04-15 | 架构讨论 | 五层防线（Principles + Prompt + Validation + RAG + Calibration） |
| 10 | Principles 更新机制 | 04-16 | 创始人提议 | 认知驱动（非市场驱动），3/3全票+创始人确认 |
| 11 | Principles 合法输入 | 04-16 | 创始人提议 | 仅限：新一手材料、新研究、校准偏差。排除：投资表现、市场环境 |

---

## 审查记录

| 审查 | 日期 | 状态 | 要点 |
|------|------|------|------|
| /office-hours | 2026-04-14 | APPROVED | 基础设计文档，4 方案选 B (Soul-First) |
| /plan-ceo-review | 2026-04-14 | CLEARED | SCOPE EXPANSION: 6 提案中 4 个接受，1 跳过，3 outside voice 修正 |
| /plan-eng-review | 2026-04-15 | CLEARED | 4 个架构决策（Python/SQLite/tool_use/大师即筛选器），3 个关键缺口标记 |
| 灵魂封装架构 | 2026-04-15 | DESIGNED | 五层防线设计、Soul Profile JSON schema、校准案例集 |
| Principles 机制 | 2026-04-16 | DESIGNED | 认知驱动更新、全票通过制、硬约束 checklist 架构 |
