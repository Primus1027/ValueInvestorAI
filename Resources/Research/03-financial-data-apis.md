# 财务数据 API 详细报告

> 调研日期：2026-04-05
> 覆盖范围：免费/低成本财务数据 API 和开源数据工具

---

## 第一部分：免费财务数据 API 对比总览

| API 服务 | 免费额度 | 数据范围 | 更新频率 | 需要 API Key | 最适合场景 |
|----------|----------|----------|----------|-------------|-----------|
| **yfinance** | 无限制（非官方） | 全球股票/ETF/基金 | 实时+历史 | 否 | 快速原型/学习 |
| **Alpha Vantage** | 25次/天, 5次/分 | 美股/外汇/加密 | 实时+历史 | 是（免费） | 入门开发 |
| **Financial Modeling Prep** | 500MB/月 | 全球股票/财报 | 日频+历史 | 是（免费） | 基本面分析 |
| **Polygon.io** | 5次/分 | 美股/期权/外汇/加密 | 日终+历史 | 是（免费） | 历史数据研究 |
| **Finnhub** | 60次/分 | 美股/全球/加密 | 实时 | 是（免费） | 实时数据+新闻 |
| **SEC EDGAR** | 无限制 | 美股 SEC 文件 | 官方发布频率 | 否（需 UA） | 财报原始数据 |
| **OpenBB Platform** | 开源免费 | 依赖数据源配置 | 依赖数据源 | 依赖数据源 | 统一数据平台 |
| **FinanceToolkit** | 开源免费 | 需配合 FMP 等 | 依赖数据源 | 依赖数据源 | 财务指标计算 |

---

## 第二部分：各 API 详细评估

### 2.1 yfinance（Yahoo Finance 非官方 API）

- **GitHub**: https://github.com/ranaroussi/yfinance
- **安装**: `pip install yfinance`
- **免费额度**: 无明确限制，但有反爬措施
- **数据覆盖**:
  - 全球股票行情（美股、港股、A股等）
  - ETF、共同基金、指数
  - 期权链
  - 公司财务报表
  - 公司基本信息
- **更新频率**: 接近实时（15分钟延迟）
- **是否需要 API Key**: 否
- **推荐理由**:
  - 零成本启动
  - 数据覆盖最广
  - Python 接口最简单
- **限制和注意事项**:
  - 非官方 API，Yahoo 不保证服务稳定性
  - 频繁 IP 封禁和限速问题
  - 数据准确性偶有问题
  - 不适合生产环境的高频使用
  - 2025年起可靠性进一步下降
- **对 ValueInvestorAI 的价值**: 适合开发和测试阶段，不建议作为生产环境唯一数据源

### 2.2 Alpha Vantage

- **网站**: https://www.alphavantage.co/
- **免费额度**:
  - 25 次 API 请求/天
  - 5 次调用/分钟
- **数据覆盖**:
  - 美股实时和历史行情
  - 基本面数据（收入表、资产负债表、现金流）
  - 外汇汇率
  - 加密货币
  - 技术指标（50+ 种）
  - 经济指标
- **更新频率**: 实时（付费），15分钟延迟（免费）
- **是否需要 API Key**: 是（免费注册获取）
- **推荐理由**:
  - API 设计简洁，文档清晰
  - 适合初学者
  - JSON 和 CSV 双格式输出
- **限制和注意事项**:
  - 免费额度极低（25次/天），严重限制批量分析
  - 付费起步 $49.99/月
  - 数据覆盖不如 FMP 全面
- **对 ValueInvestorAI 的价值**: 适合补充数据源，但免费额度太低，难以支撑批量分析

### 2.3 Financial Modeling Prep (FMP)

- **网站**: https://site.financialmodelingprep.com/
- **免费额度**:
  - 500MB 月流量带宽
  - 不限调用次数（受带宽限制）
- **数据覆盖**:
  - 全球股票（美股、国际市场）
  - 完整财务报表（30+ 年历史）
  - 公司概况
  - 实时和历史行情
  - 分析师评级和目标价
  - SEC 文件
  - ETF、加密货币
  - 经济指标
- **更新频率**: 实时行情 + 财报发布后更新
- **是否需要 API Key**: 是（免费注册）
- **推荐理由**:
  - 免费额度相对合理
  - 基本面数据最为丰富（30年+ 财报历史）
  - FinanceToolkit 的默认数据源
  - REST API 设计规范
- **限制和注意事项**:
  - 500MB 带宽对大规模批量分析仍有限制
  - 部分高级数据端点需付费
  - 付费计划起步 $14/月（Starter）
- **对 ValueInvestorAI 的价值**: **强烈推荐作为主要基本面数据源**，30年+ 的财报历史数据对价值投资分析至关重要

### 2.4 Polygon.io

- **网站**: https://polygon.io/
- **免费额度**:
  - 5 次 API 调用/分钟
  - 日终（End-of-Day）数据
  - 历史数据访问
- **数据覆盖**:
  - 美股（10,000+ 股票）
  - 期权
  - 外汇
  - 加密货币
  - 指数
- **更新频率**: 免费版仅日终数据，付费版实时
- **是否需要 API Key**: 是（免费注册）
- **推荐理由**:
  - 数据质量高
  - API 设计现代（REST + WebSocket）
  - 历史数据深度好
- **限制和注意事项**:
  - 免费版每分钟仅 5 次调用
  - 实时数据需付费（$29/月起）
  - 基本面数据不如 FMP 丰富
- **对 ValueInvestorAI 的价值**: 适合补充价格数据，但基本面数据能力不足

### 2.5 Finnhub

- **网站**: https://finnhub.io/
- **免费额度**:
  - **60 次 API 调用/分钟**（最慷慨）
  - 实时美股报价
  - WebSocket 流式数据（最多 50 个品种）
- **数据覆盖**:
  - 全球股票行情
  - 公司新闻和媒体情绪
  - 公司基本面数据
  - SEC 文件
  - IPO 日历
  - 经济数据
  - 另类数据（社交情绪等）
- **更新频率**: 实时
- **是否需要 API Key**: 是（免费注册）
- **推荐理由**:
  - **免费额度最慷慨**（60次/分钟远超其他服务）
  - 新闻和情绪数据是独特优势
  - WebSocket 支持实时推送
- **限制和注意事项**:
  - 基本面数据深度不如 FMP
  - 高级情绪分析需付费
  - 付费计划起步 $50/月
- **对 ValueInvestorAI 的价值**: **推荐作为新闻和情绪数据的主要来源**，免费额度充足

### 2.6 SEC EDGAR（官方免费）

- **网站**: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- **数据端点**:
  - 提交历史: `https://data.sec.gov/submissions/CIK##########.json`
  - XBRL 财务数据: `https://data.sec.gov/api/xbrl/`
  - 全文搜索: EDGAR Full-Text Search
- **免费额度**: 完全免费，无限制
- **数据覆盖**:
  - 所有美股 SEC 申报文件
  - 10-K、10-Q、8-K、13F、Form 4 等
  - XBRL 结构化财务数据
  - 公司和个人的申报历史
- **更新频率**: 实时（SEC 发布后即可获取）
- **是否需要 API Key**: 否（但需要设置 User-Agent Header）
- **推荐理由**:
  - **完全免费、无任何限制**
  - 最权威的一手财务数据来源
  - 覆盖所有上市公司
- **限制和注意事项**:
  - 仅覆盖美国上市公司
  - 原始数据需要解析处理
  - 需要遵守 SEC 的访问频率建议（10 请求/秒以内）
- **对 ValueInvestorAI 的价值**: **必须集成的核心数据源**，是最可靠的免费财务数据来源

#### EdgarTools — SEC EDGAR Python 库

- **GitHub**: https://github.com/dgunning/edgartools
- **PyPI**: https://pypi.org/project/edgartools/
- **简介**: 将 SEC EDGAR 申报文件转化为结构化数据的 Python 库
- **核心特性**:
  - 无需 API Key、无订阅、无速率限制
  - 支持所有 SEC 表格类型
  - 自动解析 XBRL 财务报表
  - 提取结构化的财务报表数据
- **推荐理由**: **免费且功能强大，是访问 SEC 数据的首选 Python 库**

### 2.7 OpenBB Platform

- **GitHub**: https://github.com/OpenBB-finance/OpenBB
- **网站**: https://openbb.co/
- **简介**: 开源金融数据和分析平台，统一接口访问近 100 个数据源
- **核心特性**:
  - 统一 API 设计，学一个接口即可访问所有数据
  - REST API + Python SDK
  - MCP Server 支持（可对接 AI Agent）
  - 支持自定义数据提供商集成
  - Open Data Platform (ODP) 架构
- **开源协议**: Apache 2.0
- **免费部分**: 开源核心免费，数据取决于底层数据源的免费额度
- **推荐理由**:
  - 作为数据抽象层，极大简化多数据源管理
  - MCP 支持可直接与 AI Agent 集成
  - 活跃的社区和持续更新
- **限制和注意事项**:
  - OpenBB Workspace 企业版需付费
  - 底层数据源仍需要各自的 API Key
- **对 ValueInvestorAI 的价值**: **推荐作为数据抽象层**，统一管理所有数据源

### 2.8 FinanceToolkit

- **GitHub**: https://github.com/JerBouma/FinanceToolkit
- **PyPI**: https://pypi.org/project/financetoolkit/
- **简介**: 透明高效的金融分析工具包
- **核心特性**:
  - 180+ 财务比率和指标
  - 150+ 财务度量计算
  - 30+ 年财务报表数据
  - 覆盖股票、期权、货币、加密、ETF、基金、指数等
  - 性能和风险度量（Sharpe Ratio、VaR 等）
  - 配套 Finance Database（300,000+ 品种）
- **开源协议**: MIT
- **数据来源**: 主要依赖 Financial Modeling Prep API
- **推荐理由**:
  - 计算方法完全透明，可审计
  - 涵盖价值投资需要的所有财务指标
  - 与 FMP 搭配使用效果最佳
- **限制和注意事项**:
  - 需要 FMP API Key（免费版有限制）
  - 是计算层而非数据层
- **对 ValueInvestorAI 的价值**: **强烈推荐作为核心财务分析计算引擎**

---

## 第三部分：其他值得关注的数据源

### 3.1 EODHD (End of Day Historical Data)

- **网站**: https://eodhd.com/
- **免费额度**: 有限的免费试用
- **数据覆盖**: 全球数十个交易所，股票和基本面数据
- **推荐理由**: 国际市场覆盖最广
- **注意事项**: 免费额度有限

### 3.2 Alpaca

- **网站**: https://alpaca.markets/
- **特点**: 交易平台自带数据 API
- **推荐理由**: 如果需要同时实现交易功能
- **注意事项**: 主要面向美股交易者

### 3.3 Quandl (Nasdaq Data Link)

- **网站**: https://data.nasdaq.com/
- **特点**: 经济和另类数据的重要来源
- **推荐理由**: 宏观经济数据丰富
- **注意事项**: 2018年被 Nasdaq 收购后部分数据集变为付费

---

## 第四部分：推荐数据架构

### 4.1 分层数据策略

```
┌─────────────────────────────────────┐
│        ValueInvestorAI 应用层        │
├─────────────────────────────────────┤
│     FinanceToolkit (财务指标计算)     │
├─────────────────────────────────────┤
│    OpenBB Platform (统一数据抽象层)   │
├─────────────┬───────────┬───────────┤
│ SEC EDGAR   │    FMP    │  Finnhub  │
│ (财报原数据) │ (基本面)  │ (新闻情绪) │
├─────────────┼───────────┼───────────┤
│  yfinance   │ Polygon   │ Alpha V.  │
│ (行情备份)   │ (价格数据) │ (补充)    │
└─────────────┴───────────┴───────────┘
```

### 4.2 按用途推荐

| 用途 | 主要数据源 | 备用数据源 |
|------|-----------|-----------|
| 财务报表（美股） | SEC EDGAR + EdgarTools | FMP |
| 财务指标计算 | FinanceToolkit + FMP | 自研计算 |
| 实时行情 | Finnhub | yfinance |
| 历史价格 | Polygon.io | yfinance |
| 新闻和情绪 | Finnhub | FinGPT |
| 公司基本信息 | FMP | OpenBB |
| 宏观经济数据 | Alpha Vantage | FRED |
| 统一数据管理 | OpenBB Platform | 自研适配层 |

### 4.3 成本估算

| 方案 | 月成本 | 适用阶段 |
|------|--------|----------|
| 全免费方案 | $0 | MVP/原型验证 |
| 基础付费方案 | ~$30-50/月 | 早期产品（FMP Starter + Polygon Basic） |
| 专业方案 | ~$100-200/月 | 成熟产品（多数据源付费版） |

### 4.4 实施优先级

1. **第一阶段（MVP）**: SEC EDGAR + EdgarTools + yfinance + Finnhub 免费版
2. **第二阶段（Beta）**: 加入 FMP + FinanceToolkit + OpenBB Platform
3. **第三阶段（Production）**: 根据需求升级付费方案，加入 Polygon 等
