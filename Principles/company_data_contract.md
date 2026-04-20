# Company Data Contract for PrinciplesEngine

> Generated: 2026-04-20
> Purpose: 定义 MVP 阶段（未来 Path A）yfinance / edgartools adapter
> 需要提供给 PrinciplesEngine.evaluate() 的 company_data 字段。
>
> **Normative schema**: `company_data_contract.schema.json` (JSON Schema draft-07)。
> 本 Markdown 是人类可读伴随文档。两者不一致时以 JSON Schema 为准。

## 要求字段（从 HARD rules 反推）

### 基础财务（quantitative_hard / veto_line）
- `financials.roe_latest` (number): 最新年度 ROE（%）
- `financials.roe_5yr_avg` (number): 过去 5 年平均 ROE
- `financials.roe_5yr_min` (number): 过去 5 年最低 ROE
- `financials.debt_to_equity` (number): 资产负债率
- `financials.free_cash_flow_positive_years` (number): 过去 N 年内 FCF 为正的年份数
- `financials.revenue_growth_5yr` (number): 过去 5 年营收复合增长率
- `financials.gross_margin` (number): 毛利率
- `financials.net_margin` (number): 净利率
- `financials.pe_ratio` (number): 市盈率
- `financials.pb_ratio` (number): 市净率
- `financials.years_of_profitability_in_10` (number): 过去 10 年盈利年数

### 业务定性（qualitative_required）
- `business.is_in_circle_of_competence` (bool): 是否在能力圈内（由大师 2/3 表决）
- `business.is_simple_to_explain` (bool): 商业模式能否用 1-2 句话解释清楚
- `management.integrity_score` (number | null): 管理层诚信评分（0-10，或 null 如未评估）
- `management.capital_allocation_track_record` (string): 资本配置历史评价
- `moat.identified_types` (list[string]): 已识别护城河类型（brand/cost/network/switching/regulatory）

### 仓位相关（position_sizing）
- `portfolio.total_holdings_count` (number): 当前总持仓数
- `portfolio.target_position_pct` (number): 目标仓位百分比（0-1）
- `portfolio.concentration_top5_pct` (number): 前 5 大持仓总占比

## 未来 MVP adapter 责任

1. `yfinance_adapter.py`: 拉取 financials.* 字段（大部分免费可得）
2. `edgartools_adapter.py`: 拉取 10-K / 13F 补充字段
3. `qualitative_resolver.py`: 通过 Agent (Layer 1) 评估 business.* 和 management.* 字段（需要 LLM）
4. `portfolio_tracker.py`: 维护 portfolio.* 实时字段

本 contract 在 v1.0 Principles 冻结；MVP 阶段实现 adapters 必须对齐此 schema。