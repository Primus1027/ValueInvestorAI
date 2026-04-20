# Soul-Level Preferences (非 Layer 0)

> Generated: 2026-04-20

本文档记录**未达成三方全票共识**的 principle candidates，
**不作为 Layer 0 硬约束执行**。仅供 Layer 1 Agent 参考。

- SOFT (2/3 多数): 6
- DROPPED (1/3 单方): 22


## SOFT Preferences（2/3 多数共识）

### 1. 护城河完全依赖单一专利、单一监管许可或单一客户（>50% 营收）的公司直接拒绝（qualitative_required 表述版本）

- **Cluster ID**: `cl_05`
- **Category**: `qualitative_required`
- **Supported by**: buffett, munger (2/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (threshold=0.5, severity=veto): 护城河来源高度集中于单一专利、单一许可证或单一客户（占营收 50% 以上）的公司直接拒绝投资
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-moat_compounding`
  - **munger** (threshold=0.5, severity=veto): 护城河完全依赖单一专利、单一监管许可或单一客户关系的公司直接否决
    Source: `munger/.../specific-conditions-under-which-munger-says-pass`

### 2. 以精确 DCF 电子表格或依赖多重关键独立假设的复杂多情景模型为主要估值依据时拒绝该估值结论

- **Cluster ID**: `cl_07`
- **Category**: `valuation_method`
- **Supported by**: buffett, duan (2/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (severity=veto): 以精确多年 DCF 电子表格（含逐年增长率和精确折现率）为主要估值方法时拒绝该估值结论
    Source: `buffett/.../rule-2-never-use-formal-spreadsheet-dcf-as-the-primary-valuation-method`
  - **duan** (severity=veto): 以DCF模型或复杂多情景Excel模型作为唯一估值依据，或买入结论依赖超过3个关键独立假设同时成立，直接拒绝
    Source: `duan/.../不做清单`

### 3. 现金流转化率显著低于盈利（FCF/净利润 或 OCF/净利润）持续偏低的公司标记利润质量警告

- **Cluster ID**: `cl_08`
- **Category**: `quantitative_hard`
- **Supported by**: buffett, duan (2/3)
- **Severity**: `warning`
- **阈值分歧** ⚠: buffett=0.8, duan=0.5

**每个方法论框架的 variant**:
  - **buffett** (threshold=0.8, severity=warning): 5 年平均自由现金流转化率（FCF/净利润）低于 80% 的公司标记警告
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-资本密集度`
  - **duan** (threshold=0.5, severity=warning): 经营现金流/净利润比值3年均值低于0.5，标记利润质量警告
    Source: `duan/.../本分的真实含义`

### 4. 在业务质量、护城河持久性与管理层诚信前置验证完成之前，以估值指标（P/E、P/B、EV/EBITDA 等）为投资推荐首要依据时拒绝该结论

- **Cluster ID**: `cl_09`
- **Category**: `valuation_method`
- **Supported by**: duan, munger (2/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **munger** (severity=veto): 在确认业务质量、护城河持久性、管理层诚信之前，禁止以估值指标（P/E、P/B、EV/EBITDA）作为投资推荐的主要依据
    Source: `munger/.../tier-1-iron-laws-never-violated`
  - **duan** (severity=veto): 仅凭低PE或低PB提出买入、未先完成商业模式和企业文化论证的投资论点，直接拒绝
    Source: `duan/.../案例-4ge2008一次教训`

### 5. 投资组合持仓数量超过 10 只标记过度分散警告（集中持仓纪律）

- **Cluster ID**: `cl_10`
- **Category**: `position_sizing`
- **Supported by**: buffett, duan (2/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **buffett** (threshold=10, severity=warning): 拒绝任何将投资组合分散至 10 只及以上个股的配置建议，或纳入新标的时未证明其风险调整预期回报显著优于现有最低信念持仓
    Source: `buffett/.../21-concentrated-positions`
  - **duan** (threshold=10, severity=warning): 单一投资组合持仓超过10只股票，标记过度分散警告
    Source: `duan/.../仓位管理方式`

### 6. 评估竞争优势需具备前沿/高度专业技术知识（或行业不在能力圈清单内）的标的直接拒绝——能力圈铁律

- **Cluster ID**: `cl_11`
- **Category**: `qualitative_required`
- **Supported by**: buffett, duan (2/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (severity=veto): 评估竞争优势必须依赖前沿技术专业知识的公司直接拒绝投资
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-能力圈`
  - **duan** (severity=veto): 标的所属行业不在段永平能力圈列表内，直接拒绝进行分析
    Source: `duan/.../铁律从不违反`


## DROPPED Candidates（1/3 单方提案）

*以下 principles 仅在单一方法论框架下提出，保留作为 soul-specific 偏好，
不升级到跨框架层面。*

### 1. 护城河完全依赖单一专利、单一监管许可或单一核心客户（>50% 营收）直接拒绝（veto_line 表述版本，与 cl_05 语义重合但 category 不同，按聚类规则保留）

- **Cluster ID**: `cl_06`
- **Category**: `veto_line`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (threshold=0.5, severity=veto): 公司护城河完全依赖单一专利、单一监管许可或单一核心客户（贡献收入超过50%），直接拒绝
    Source: `soul/investment_philosophy/moat_analysis/structural_requirements`

### 2. 负债/EBITDA 超过 3 倍的公司直接拒绝

- **Cluster ID**: `cl_12`
- **Category**: `quantitative_hard`
- **Supported by**: buffett (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (threshold=3, severity=veto): 负债/EBITDA 超过 3 倍的公司直接拒绝投资
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-财务堡垒`

### 3. 利息覆盖率低于 5 倍的公司直接拒绝

- **Cluster ID**: `cl_13`
- **Category**: `quantitative_hard`
- **Supported by**: buffett (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (threshold=5, severity=veto): 利息覆盖率低于 5 倍的公司直接拒绝投资
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-财务堡垒`

### 4. ROE 连续 3 年以上下滑且同期行业中位 ROE 未同向下滑标记护城河侵蚀警告

- **Cluster ID**: `cl_14`
- **Category**: `quantitative_hard`
- **Supported by**: buffett (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **buffett** (threshold=3, severity=warning): ROE 连续 3 年及以上下滑、且同期行业中位 ROE 未出现同向下滑的公司标记护城河侵蚀风险
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-投资标准`

### 5. 毛利率连续 5 年以上下降的公司标记定价权丧失警告

- **Cluster ID**: `cl_15`
- **Category**: `quantitative_hard`
- **Supported by**: buffett (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **buffett** (threshold=5, severity=warning): 毛利率连续 5 年以上下降的公司标记定价权丧失警告
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-pricing_power`

### 6. 投资论据以宏观经济预测为核心前提时直接拒绝

- **Cluster ID**: `cl_16`
- **Category**: `veto_line`
- **Supported by**: buffett (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (severity=veto): 投资论据以宏观经济预测（利率走势、GDP 增速、美联储政策）为核心前提时直接拒绝
    Source: `buffett/module-7-behavioral-rules-self-check-checklist/mental-models-he-does-not-use`

### 7. 以季度收益超预期/低预期节奏为核心买卖依据直接拒绝

- **Cluster ID**: `cl_17`
- **Category**: `veto_line`
- **Supported by**: buffett (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (severity=veto): 以季度收益超预期或低预期作为核心买卖依据时直接拒绝该推荐
    Source: `buffett/.../rule-3-never-recommend-based-on-quarterly-earnings-momentum`

### 8. 以尚未实现的市场机会（TAM 占比、期权价值、推测性产品线）为主要估值依据时拒绝

- **Cluster ID**: `cl_18`
- **Category**: `valuation_method`
- **Supported by**: buffett (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **buffett** (severity=veto): 以尚未实现的市场机会（TAM 占比、期权价值、推测性未来产品线）为主要估值依据时拒绝该结论
    Source: `buffett/appendix-decision-grade-insights-vig-scan-2026-04/factor-估值方法`

### 9. 牛市论点依赖超过2个相互独立关键假设同时成立的投资直接否决

- **Cluster ID**: `cl_19`
- **Category**: `veto_line`
- **Supported by**: munger (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **munger** (threshold=2, severity=veto): 牛市论点依赖超过2个相互独立的关键假设必须同时成立的投资直接否决
    Source: `munger/.../tier-1-iron-laws-never-violated`

### 10. 金融机构或投资载体资产/权益杠杆 ≥25 倍直接否决

- **Cluster ID**: `cl_20`
- **Category**: `veto_line`
- **Supported by**: munger (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **munger** (threshold=25, severity=veto): 金融机构或投资载体资产/权益杠杆倍数达到或超过25倍时直接否决
    Source: `munger/appendix-z-cross-master-comparisons-vig-scan-2026-04/杠杆与资本结构`

### 11. 新投资的风险调整预期回报未显著优于现有最高信念持仓时拒绝纳入（机会成本纪律）

- **Cluster ID**: `cl_21`
- **Category**: `position_sizing`
- **Supported by**: munger (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **munger** (severity=warning): 新投资的预期风险调整回报若不显著高于当前组合最高信念持仓的预期回报，则拒绝纳入组合
    Source: `munger/.../tier-2-strong-preferences-default-behavior-overridable`

### 12. 股票回购执行期间核心内部人净卖出直接否决

- **Cluster ID**: `cl_22`
- **Category**: `veto_line`
- **Supported by**: munger (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **munger** (severity=veto): 公司实施股票回购计划期间核心内部高管（CEO/CFO/董事会成员）存在净卖出记录的公司直接否决
    Source: `munger/.../evaluating-management-incentives`

### 13. 过去5年财报中出现超过3次一次性调整项目的公司标记会计诚信警告

- **Cluster ID**: `cl_23`
- **Category**: `quantitative_hard`
- **Supported by**: munger (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **munger** (threshold=3, severity=warning): 过去5年财务报告中出现超过3次'一次性调整项目'的公司拒绝投资
    Source: `munger/.../accounting-quality-and-promotional-management`

### 14. 分析模型依赖超过20个独立关键假设归入'太难'堆

- **Cluster ID**: `cl_24`
- **Category**: `quantitative_hard`
- **Supported by**: munger (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **munger** (threshold=20, severity=warning): 投资论点分析模型依赖超过20个独立关键假设时归入'太难'堆，拒绝推进
    Source: `munger/.../the-too-hard-pile-vs-no-brainer-decisions`

### 15. 经营性现金流连续3年为负的公司直接拒绝

- **Cluster ID**: `cl_25`
- **Category**: `quantitative_hard`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (threshold=2, severity=veto): 经营性现金流连续3年均为负的公司直接拒绝
    Source: `duan/.../铁律从不违反`

### 16. 任何使用借贷资金（融资融券、配资等）的投资方案直接拒绝

- **Cluster ID**: `cl_26`
- **Category**: `veto_line`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (threshold=0, severity=veto): 任何涉及借钱投资（融资融券、配资等）的投资方案直接拒绝
    Source: `duan/.../不做清单`

### 17. 任何做空头寸直接拒绝

- **Cluster ID**: `cl_27`
- **Category**: `veto_line`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (threshold=0, severity=veto): 任何做空头寸直接拒绝
    Source: `duan/.../不做清单`

### 18. 有监管机构认定的财务造假或重大虚假陈述历史记录的公司直接拒绝

- **Cluster ID**: `cl_28`
- **Category**: `qualitative_required`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (severity=veto): 有监管机构认定的财务造假或重大虚假陈述历史记录的公司直接拒绝
    Source: `duan/.../本分的真实含义`

### 19. 核心管理层12个月内净减持超过总股本5%标记信心警告（若与回购同期则升级为veto）

- **Cluster ID**: `cl_29`
- **Category**: `quantitative_hard`
- **Supported by**: duan (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **duan** (threshold=0.05, severity=warning): 核心管理层过去12个月净减持超过总股本5%，标记管理层信心警告；若减持期间公司同步实施股份回购，则升级为直接拒绝
    Source: `duan/.../段永平的决策问话清单`

### 20. 有息负债率连续3年上升且最新值超过50%标记资产负债表风险警告

- **Cluster ID**: `cl_30`
- **Category**: `quantitative_hard`
- **Supported by**: duan (1/3)
- **Severity**: `warning`

**每个方法论框架的 variant**:
  - **duan** (threshold=0.5, severity=warning): 有息负债率连续3年上升且最新值超过50%，标记资产负债表风险警告
    Source: `duan/.../铁律从不违反`

### 21. 以'赛道''风口''蓝海''政策红利'等概念为核心买入理由直接拒绝

- **Cluster ID**: `cl_31`
- **Category**: `veto_line`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (severity=veto): 以'赛道热'、'风口'、'蓝海市场'等概念作为核心买入理由，直接拒绝
    Source: `duan/.../案例-5他说不的理由-比说是更重要`

### 22. 预设持有期不足10年的买入论点直接拒绝

- **Cluster ID**: `cl_32`
- **Category**: `position_sizing`
- **Supported by**: duan (1/3)
- **Severity**: `veto`

**每个方法论框架的 variant**:
  - **duan** (threshold=10, severity=veto): 若投资论点中预设持有期不足10年，禁止买入
    Source: `duan/.../铁律从不违反`
