# ValueInvestorAI 开源技术与信息资源调研综合报告

> 调研日期：2026-04-05
> 调研方法：WebSearch 全网搜索 + 项目分析
> 详细报告索引见文末

---

## 一、调研概述

本次调研覆盖 ValueInvestorAI 项目所需的 6 大类资源，共发现并评估了 **50+ 个开源项目、API 服务和信息资源**。以下为综合分析和推荐。

---

## 二、核心发现

### 2.1 开源价值投资决策系统（详见 01-opensource-investing-tools.md）

**关键发现**: 多智能体 AI 金融分析框架正在快速发展，已有多个成熟项目可供参考。

| 项目 | GitHub 地址 | 核心价值 |
|------|------------|---------|
| **TradingAgents** | github.com/TauricResearch/TradingAgents | 多 Agent LLM 交易框架，架构参考 |
| **FinRobot** | github.com/AI4Finance-Foundation/FinRobot | AI Agent 金融平台，文档分析能力 |
| **FinGPT** | github.com/AI4Finance-Foundation/FinGPT | 开源金融大模型，NLP 底层 |
| **OpenBB Platform** | github.com/OpenBB-finance/OpenBB | 统一金融数据平台 |
| **valinvest** | github.com/astro30/valinvest | 价值投资评估工具 |
| **ValueInvesting-AI-Analysis** | github.com/Tetleysteabags/ValueInvesting-AI-Analysis | AI 价值投资分析 |

**推荐策略**: 以 TradingAgents 架构为参考，自定义价值投资专用 Agent 角色（基本面分析师、估值分析师、护城河分析师、风险评估师），集成 OpenBB 作为统一数据层。

### 2.2 回测与虚拟交易系统（详见 01-opensource-investing-tools.md）

**关键发现**: Python 回测框架生态成熟，各有适用场景。

| 框架 | 速度 | 适用场景 | 维护状态 |
|------|------|---------|---------|
| **VectorBT** | 极快 | 大规模量化研究 | 活跃 |
| **QuantConnect Lean** | 快 | 企业级全功能 | 非常活跃 |
| **Zipline-reloaded** | 慢 | 因子研究 | 活跃 |
| **Backtrader** | 中等 | 入门学习 | 维护模式 |
| **Backtesting.py** | 快 | 快速原型 | 活跃 |

**推荐策略**: 日常开发用 VectorBT（速度快），复杂策略用 QuantConnect Lean（功能全），快速验证想法用 Backtesting.py。

### 2.3 价值投资哲学与大师资源（详见 02-master-resources.md）

**关键发现**: 核心投资大师的资料可免费获取，且覆盖面足够构建知识库。

#### 巴菲特资源

- 致股东信 1957-2025：Berkshire 官网 + Nick Vitucci 合集 PDF + Internet Archive
- 股东大会记录：CNBC Buffett Archive
- 采访文字记录：Tilson Funds 资源页

#### 芒格资源

- 千页合集 PDF：My Money Blog 整理
- 《穷查理宝典》：Stripe Press 在线版 + Internet Archive 全文
- 演讲记录：Worldly Partners Archive

#### 段永平资源

- 《段永平投资问答录》投资逻辑篇 + 商业逻辑篇：雪球特别版 PDF 免费下载
- 雪球问答历史整理

#### 李录资源

- 《文明、现代化、价值投资与中国》：中国电子书平台
- 哥伦比亚大学演讲（2006/2010/2021）：多个免费文字记录来源

**推荐策略**: 优先收集 PDF 格式的文档，使用 OCR + NLP 建立结构化知识库，按投资原则、估值方法、商业分析、心理学等维度组织。

### 2.4 财务数据 API（详见 03-financial-data-apis.md）

**关键发现**: 完全免费的方案可以支撑 MVP 阶段，生产环境建议混合方案。

#### 免费额度排名

| API | 免费调用量 | 最适合 |
|-----|----------|-------|
| **SEC EDGAR** | 无限制 | 美股财报原始数据 |
| **Finnhub** | 60次/分钟 | 新闻和实时行情 |
| **yfinance** | 无明确限制 | 快速原型 |
| **FMP** | 500MB/月 | 基本面分析 |
| **Polygon.io** | 5次/分钟 | 历史价格数据 |
| **Alpha Vantage** | 25次/天 | 补充数据 |

**推荐策略**:

分层数据架构：
- **数据抽象层**: OpenBB Platform（统一接口）
- **财报数据**: SEC EDGAR + EdgarTools（免费、权威）
- **财务指标**: FinanceToolkit + FMP（180+ 指标计算）
- **新闻情绪**: Finnhub（免费额度最大）
- **行情数据**: yfinance（开发） / Polygon.io（生产）

### 2.5 多渠道发布框架（详见 04-publishing-frameworks.md）

**关键发现**: 开源方案可覆盖主要社交平台，但中国平台需要特殊处理。

#### 全球平台

| 平台 | API 可行性 | 推荐方案 |
|------|-----------|---------|
| **X/Twitter** | 免费版可发帖（1500条/月） | tweepy + 官方 API |
| **Medium** | API 可发布文章 | 官方 Integration Token |
| **LinkedIn** | 审批复杂但可行 | Mixpost 中间层 |

#### 中国平台

| 平台 | API 可行性 | 推荐方案 |
|------|-----------|---------|
| **微信公众号** | 需认证企业号 | AIWriteX 开源工具 |
| **小红书** | MCP 方案可用 | xiaohongshu-mcp |

#### 统一管理

- **Mixpost**（开源自托管，MIT 协议）作为核心发布调度层
- **Ayrshare**（SaaS）作为备选的统一 API
- **Activepieces/n8n**（开源自动化）编排发布工作流

**推荐策略**: 第一阶段先做 Medium + X，第二阶段加入微信公众号 + 小红书，第三阶段引入 Mixpost 统一管理。

---

## 三、推荐技术栈总览

```
┌─────────────────────────────────────────────────┐
│              ValueInvestorAI 系统架构              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │         AI Agent 层 (自研)                 │  │
│  │  参考: TradingAgents + FinRobot 架构       │  │
│  │  角色: 价值分析师 / 估值师 / 风控师         │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────┴───────────────────────────┐  │
│  │         知识库层                           │  │
│  │  巴菲特/芒格/段永平/李录 投资哲学          │  │
│  │  向量数据库 (ChromaDB/Pinecone)            │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────┴───────────────────────────┐  │
│  │         数据层                             │  │
│  │  OpenBB Platform (统一数据抽象)            │  │
│  │  SEC EDGAR + FMP + Finnhub + yfinance     │  │
│  │  FinanceToolkit (财务指标计算)             │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────┴───────────────────────────┐  │
│  │         回测层                             │  │
│  │  VectorBT (快速回测)                      │  │
│  │  QuantConnect Lean (复杂策略)             │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────┴───────────────────────────┐  │
│  │         发布层                             │  │
│  │  Mixpost (调度管理)                       │  │
│  │  Medium / X / 微信公众号 / 小红书          │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 四、实施路线图

### 第一阶段：MVP（1-2个月）

| 模块 | 技术选择 | 成本 |
|------|---------|------|
| 数据获取 | SEC EDGAR + yfinance + Finnhub 免费版 | $0 |
| 财务分析 | FinanceToolkit | $0 |
| AI 分析 | 自研 Agent（参考 TradingAgents 架构） | LLM API 成本 |
| 知识库 | 巴菲特致股东信 + 芒格演讲（PDF 处理） | $0 |
| 回测 | Backtesting.py（快速验证） | $0 |
| 发布 | Medium API + X 免费版 | $0 |

**预估月成本**: LLM API ~$20-50

### 第二阶段：Beta（3-4个月）

| 模块 | 升级内容 | 成本变化 |
|------|---------|---------|
| 数据获取 | + FMP + OpenBB Platform | +$14/月 |
| AI 分析 | 完善 Agent 角色，加入段永平/李录知识库 | - |
| 回测 | 升级到 VectorBT | $0 |
| 发布 | + 微信公众号 + 小红书 | $0 |

**预估月成本**: ~$50-80

### 第三阶段：Production（5-6个月）

| 模块 | 升级内容 | 成本变化 |
|------|---------|---------|
| 数据获取 | + Polygon.io + 多数据源冗余 | +$29/月 |
| 回测 | + QuantConnect Lean（复杂策略） | $0 |
| 发布 | Mixpost 统一管理 + LinkedIn | 服务器成本 |

**预估月成本**: ~$100-150

---

## 五、风险与注意事项

### 5.1 技术风险

1. **yfinance 不稳定性**: 非官方 API，生产环境需要备选方案
2. **社交平台 API 变更**: 特别是 X/Twitter 的定价策略不稳定
3. **中国平台合规**: 微信公众号和小红书对金融内容审核严格

### 5.2 法律风险

1. **投资建议免责**: 所有发布内容必须包含免责声明
2. **版权问题**: 使用投资大师资料时需注意版权（引用 vs. 全文复制）
3. **数据使用条款**: 各 API 的使用条款需要遵守

### 5.3 缓解措施

1. 建立多数据源冗余机制
2. 使用中间层（OpenBB、Mixpost）降低对单一服务的依赖
3. 实施内容审核机制（AI + 人工双重审核）
4. 定期跟踪 API 变更和平台政策更新

---

## 六、详细报告索引

| 编号 | 文件名 | 内容 |
|------|--------|------|
| 01 | `01-opensource-investing-tools.md` | 开源价值投资决策系统 + 回测系统详细报告 |
| 02 | `02-master-resources.md` | 投资大师资料 + 价值投资哲学资源详细报告 |
| 03 | `03-financial-data-apis.md` | 财务数据 API 详细评估报告 |
| 04 | `04-publishing-frameworks.md` | 多渠道发布框架详细报告 |

所有文件位于: `/Users/ying/Documents/Desktop/ValueInvestorAI/Resources/Research/`
