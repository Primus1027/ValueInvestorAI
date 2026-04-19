# ValueInvestorAI — 项目进展总结

> 最后更新：2026-04-15
> 状态：设计完成 (v2)，准备进入开发阶段

---

## 一、项目概述

**ValueInvestorAI** 是一家由 AI 虚拟董事会运营的价值投资实体。5 位投资大师（巴菲特、芒格、段永平、李录、Primus）的 AI Agent 组成虚拟董事会，自主做出投资决策，每日产出投资文章，运营 $10M 虚拟交易组合。

**核心来源项目：**
- **AIStartupOS**（`/Users/ying/Documents/Desktop/AIStartupOS`）— AI-Native 公司形态探索，"影子董事会"概念
- **PrimeLabWriting**（`/Users/ying/Documents/Desktop/PrimeLabWriting`）— AI 全链条内容生产平台，双模型协作架构

---

## 二、已完成的工作

### 2.1 项目愿景文档（v0.2）
**文件：** `PROJECT_VISION.md`

包含：背景来源、愿景、分阶段目标（短/中/长期）、5 大核心方法（灵魂封装、董事会运作、投资哲学形成、虚拟交易、内容生产）、实施路径（5 Phase / ~14 周）、技术架构图、6 个已确认的关键决策。

**已确认的关键决策：**

| # | 决策 | 结论 |
|---|------|------|
| 1 | Tech Stack | 重新选型，不复用 PrimeLabWriting 代码（HumanInterface 逻辑太多） |
| 2 | LLM | 每位大师用 **Claude + 豆包（Doubao）** 双模型，综合两者产出 |
| 3 | 市场数据 | 免费 API + 开源库优先 |
| 4 | 发布渠道 | 多渠道：Medium, LinkedIn, Twitter/X, 微信公众号, 小红书 |
| 5 | Primus 资料 | 后续提供，先做巴菲特、芒格、段永平、李录 |
| 6 | 优先级 | "每日一文" 和 "虚拟交易" 并行开发 |

### 2.2 AI Debate（5 AI / 2 轮辩论 + 预研究）
**文件：** `debates/2026-04-05-AI-Debate-项目愿景评审.md`（982 行）

**一句话结论：** ValueInvestorAI 作为"可审计的 AI 价值投研实验室"具有真实价值，但启动前必须完成：重构叙事、合规前置、废除短期业绩 KPI。

**8 个高置信度共识（5 AI 全部同意）：**
1. "灵魂封装"叙事必须放弃 → 改为"投资决策风格仿真"
2. "AI 就是投资者本身"不可持续 → 最优模式是 AI + 人类回圈
3. 多 Agent 辩论不自动优于单 Agent → 需强制独立信息子集 + 做空 Agent + 失败案例幽灵 Agent
4. $10M 虚拟盘无法证明真实管理能力 → 只能验证研究系统和决策流程
5. "每日一文"与价值投资哲学冲突 → 改为三层分级
6. 合规风险是运营终止级风险 → 使用真实人名涉及肖像权 + SEC 投顾注册
7. 短期业绩 KPI 是危险错误 → 会驱动系统向动量策略漂移
8. 商业模式应以"决策过程透明度"为核心 → 卖可观测的思维链

**4 个未解决争议：**
1. Agent 校准成功判据阈值（30 vs 40 案例，方向一致率 vs 多维度）
2. 真实投资路径可行性（需律师意见书）
3. 微型实盘启动时机（L2 满 6 个月 vs 更早）
4. 人类评审频率与权力边界（每周 vs 每月，否决权范围）

**5 个优先级行动：**
1. P1：叙事与合规重置（本周）
2. P2：Agent 校准方法论（Week 3-8，30-40 历史案例）
3. P3：多 Agent 独立性工程（Week 6-10）
4. P4：内容策略三层分级（本周启动）
5. P5：虚拟交易系统修正（Week 8 前，加入市场冲击成本模型）

### 2.3 竞争格局调研（Intel）
**文件：** `Resources/Research/competitive-landscape.md`

**最直接竞品：**
- **virattt/ai-hedge-fund**（43k Stars）— 理念最相似（18 位大师 Agent），但 prompt 级别封装，无虚拟交易和内容生产
- **TradingAgents**（Tauric Research）— 多 Agent + 辩论机制最接近，但无投资哲学聚焦
- **WarrenAI**（Investing.com）— 巴菲特式 AI 问答工具，非投资实体
- **Minotaur Capital** — 真实 AI 基金，但不透明、无内容

**ValueInvestorAI 占据的 5 个市场空白：**
1. 可观测的 AI 投资决策过程（竞品都是黑盒）
2. 投资哲学 + AI Agent 深度融合
3. 中国价值投资视角（段永平 + 李录）
4. 虚拟到真实的分阶段验证路径
5. AI 辩论作为投资教育内容

### 2.4 开源资源调研（Scout）
**文件：** `Resources/Research/` 下 5 份报告

**核心推荐：**

| 类别 | 推荐 |
|------|------|
| AI Agent 框架 | TradingAgents + FinRobot（架构参考） |
| 数据平台 | OpenBB Platform（统一数据抽象层） |
| 财务分析 | FinanceToolkit（180+ 指标, MIT） |
| 回测引擎 | VectorBT（快速）+ QuantConnect Lean（全功能） |
| 财报数据 | SEC EDGAR + EdgarTools（免费、权威） |
| 新闻情绪 | Finnhub（60 次/分钟免费） |
| 行情数据 | yfinance（开发）/ Polygon.io（生产） |
| 发布框架 | Mixpost（开源自托管）+ 各平台 API |

**大师资料（全部免费可获取）：**
- 巴菲特：致股东信 1957-2025（Berkshire 官网 + 合集 PDF）、CNBC Archive
- 芒格：千页合集 PDF、《穷查理宝典》Stripe Press 在线版
- 段永平：《段永平投资问答录》雪球特别版 PDF
- 李录：哥伦比亚大学演讲文字记录（2006/2010/2021）

**MVP 阶段月成本：** ~$20-50（仅 LLM API，数据层全免费）

### 2.5 /ai-debate Skill 优化
**修改文件：**
- `PrimeLabWriting/scripts/debate.ts` — summaryPrompt() 新增 3 个章节 + 标题截断 + 文档结构重组
- `~/.claude/skills/ai-debate/SKILL.md` — 更新文档描述

**改动要点：**
- 标题截断到 100 字，避免长话题撑爆标题
- Executive Summary 紧跟标题（原来被推到第 380 行）
- 新增 3 个章节：💡 核心洞察与有意思的发现、❓ 需要创始人回答的问题、🚀 下一步重要工作
- 附录分 A/B/C（辩论全文 / 预研究 / 完整话题）

---

### 2.6 设计审查流程（3 轮，2026-04-14 ~ 2026-04-15）

**流程：** /office-hours → /plan-ceo-review → /plan-eng-review

**关键决策（已确认）：**

| # | 决策 | 结论 |
|---|------|------|
| 7 | 大师数量 | 3 位（巴菲特、芒格、段永平）。李录因公开资料不足以校准而删除 |
| 8 | Tech Stack | Python（金融数据生态原生） |
| 9 | Memory 架构 | SQLite + JSON 先行；Phase 2+ 当 >50 个分析时加 vector store |
| 10 | 数据验证 | 结构化 JSON 输出 (tool_use) + 自动对比源 API 数据 |
| 11 | 筛选机制 | 大师即筛选器（无独立规则引擎），标准从大师辩论中涌现 |
| 12 | 内容格式 | 月度股东信为旗舰格式（替代"每日一文"） |
| 13 | 模型分配 | Claude/GPT 用于英文语料大师；Doubao 权重更高用于段永平 |
| 14 | 项目模式 | 个人项目（side project），结果好可扩展 |

**CEO Review 接受的 4 个扩展：**
1. 自我改进反馈循环（投资决策的复盘 → 模式识别 → 回馈 Memory）
2. 跨大师综合引擎（组合多大师视角产生原创论点）
3. 月度股东信（巴菲特格式，30 天 AI 董事会思考总结）
4. 反投资组合 + 结果追踪（记录被拒公司 + 持续验证）
5. 论点演变时间线（每家公司的论点如何随时间变化）

**Outside Voice 修正（已接受）：**
- 对抗性校准案例（测试推理，不是记忆）
- 危机场景测试（验证情绪中性核心论点）
- 数据验证需要具体架构（结构化输出解决）

---

## 三、项目文件结构

```
ValueInvestorAI/
├── PROJECT_VISION.md                              ← 项目愿景 v0.2（历史文档）
├── progress.md                                    ← 本文件（进展总结）
├── Designs/
│   ├── design-v2-soul-first-build-path.md         ← ★ 最终设计文档 v2
│   ├── ying-unknown-design-20260414-203151.md      ← /office-hours 原始设计（已被 v2 取代）
│   └── 2026-04-14-soul-first-build-path.md         ← /plan-ceo-review CEO 计划（已并入 v2）
├── debates/
│   └── 2026-04-05-AI-Debate-项目愿景评审.md       ← 5 AI 辩论报告
├── Resources/Research/
│   ├── 00-RESEARCH-SYNTHESIS.md                   ← Scout 综合报告
│   ├── 01-opensource-investing-tools.md            ← 开源投资工具
│   ├── 02-master-resources.md                     ← 投资大师资料
│   ├── 03-financial-data-apis.md                  ← 财务数据 API
│   ├── 04-publishing-frameworks.md                ← 多渠道发布框架
│   └── competitive-landscape.md                   ← 竞争格局报告
└── Discussions/AIStartupOS/                       ← AIStartupOS 原始讨论档案
```

---

## 四、待决策的问题（已部分回答）

| # | 问题 | 状态 | 决定 |
|---|------|------|------|
| 1 | 叙事重构 | **待定** | 内部用 "decision-style modeling"，外部定位待公开内容前决定 |
| 2 | 合规前置 | **待定** | Phase 3 前建议获取法律意见，但不阻塞个人资金投资 |
| 3 | 内容策略 | **已决定** | 月度股东信为旗舰 + 分析文章，不再是"每日一文" |
| 4 | 人类角色 | **已决定** | 每笔交易人工审核（审核推理 = 验证方法），社区仅围观 |
| 5 | 真实投资路径 | **已决定** | 保留，$100K 真实资金，人工审批门 |

---

## 五、下一步工作

**设计文档：** `Designs/design-v2-soul-first-build-path.md`（最终版，包含全部决策）

### Phase 0: 基础搭建（Week 1）— 立即启动
- [ ] Python 项目初始化 + git repo
- [ ] Memory 层：SQLite schema + JSON 格式 + 读写接口
- [ ] Data 层：OpenBB/yfinance 接入 + 基本财务数据获取
- [ ] 资料收集：巴菲特股东信、芒格合集 PDF、段永平问答录
- [ ] 校准案例：5 个常规 + 2-3 个对抗性案例确认

### Phase 1: 决策风格建模（Week 2-4）
- [ ] 3 位大师决策框架并行构建（Phase 1a 快速初版 + Phase 1b 深化）
- [ ] 校准测试（常规 + 对抗性 + 危机场景）
- [ ] 结构化 JSON 输出 (tool_use)

### Phase 2: 分析引擎（Week 5-8）
- [ ] 大师筛选 + 深度分析 + 数据验证
- [ ] 跨大师综合引擎
- [ ] 内容生成 + 月度股东信
- [ ] 反投资组合 + 论点演变时间线

### Phase 3: 投资决策（Week 8+）
- [ ] 真实资金投资 + 人工审批
- [ ] 自我改进反馈循环

---

*本文档用于跨 session 衔接。新 session 开始时，先读本文件了解全部背景。*


## 2026-04-19: Scan & Integration — value-investing-gurus compendium

**目标**：把新发现的投资资料网站（用户投资人朋友编纂的 Buffett-Munger Compendium）作为"首次扫描先例"，
整合进 W/C 灵魂封装，并建立可重复的扫描-整合工作流。

**成果**：
- 🏗️ 建立了 8 阶段扫描流水线（见 `scripts/soul/`）与全局 registry（`Resources/Sources/registry/`）
- 📥 抓取 134 份二手综合资料（P3/P4 tier），内容哈希寻址存储于 `raw/` + 段落锚点归一化在 `normalized/`
- ✅ 完成 30 项定向验证（解决 W 灵魂文档中多处 NEEDS VERIFICATION）
- 🔀 抽取 10 条跨大师对比、137 条概念→投资案例→结果链接、243 条决策导向洞察
- 📄 生成 W/C v1.1 灵魂文档（append-only，保留 v1.0 prose 不变，新增 Appendix Z 做多 Agent 辩论输入）
- 🧪 Gate 5 校准回归：见 `calibration_runs/`

**关键设计决定**：
1. 网站编者目的是"知识整理"，我们的目的是"决策驱动"——所有借鉴过一道"决策相关性过滤"
2. 采用 AI 主导审核（L1 自动 + L2 对抗审查），人工仅在关键节点介入
3. Profile.json 的 factor 列表稳定不变（防膨胀）；新洞察沉淀到 red_flags / how_to_evaluate
4. 引入 ROI 衰减防御机制：novelty_rate、decision_delta_rate、concept saturation 监控

**下一次扫描的起点**：`scripts/soul/fetch_vig.py` 和 `scripts/soul/integrate.py` 可作为新扫描的模板复用。

