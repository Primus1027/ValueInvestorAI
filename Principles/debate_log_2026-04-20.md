# Principles Board Debate — Full Log (2026-04-20)

## Phase 1: Independent Seed Drafts

Each of 3 methodology research assistants independently proposed seed principles.

- **buffett**: 14 seeds
- **munger**: 13 seeds
- **duan**: 15 seeds

## Phase 2: Neutral Comparative Analysis (Opus, anonymized)

- Anonymized mapping (for privacy): {'buffett': 'B', 'munger': 'C', 'duan': 'A'}
- Double-run consistency rate: 20%
- Double-run disagreements: 12
- Total stances produced: 15

## Phase 2.5: Revise Round (each master sees comparative analysis, revises)

- **buffett**: kept 9, modified 5, withdrew 0, new 2 → final 16
- **munger**: kept 13, modified 0, withdrew 0, new 0 → final 13
- **duan**: kept 11, modified 4, withdrew 0, new 3 → final 18

## Phase 3a: Semantic Deduplication (Sonnet)

- Total clusters: 32
- HARD (3/3): 4
- SOFT (2/3): 6
- DROPPED (1/3): 22

## Phase 3b+3c: Vote Tally + Rendering

Produced:
- `Principles/v1.0.md` (4 HARD principles)
- `Principles/soul-level-preferences.md` (6 SOFT + 22 DROPPED)
- `Principles/v1.0.schema.json`
- `Principles/company_data_contract.md`
- `Principles/critique_matrix.jsonl`

---

## Appendix: Cluster Details


### HARD

- `cl_01` [qualitative_required] 若无法用极少句子（1–3句）向普通智识水平者清晰解释公司的盈利机制、护城河来源与客户粘性，则归入'太难'堆直接拒绝 — masters: ['buffett', 'duan', 'munger']
- `cl_02` [quantitative_hard] 长期平均资本回报率（ROIC 或等价的非杠杆 ROE）低于 15% 的公司标记业务质量/护城河不足警告 — masters: ['buffett', 'duan', 'munger']
- `cl_03` [quantitative_hard] 主要竞争对手多年营收复合增速持续高于本公司时标记护城河侵蚀警告 — masters: ['buffett', 'duan', 'munger']
- `cl_04` [qualitative_required] 管理层在对外沟通中以营收/EBITDA 为核心业绩叙事而系统性回避 ROIC/FCF 等资本回报指标（或报表须依赖大量脚注才能理解基本经济模型）标记资本配置与会 — masters: ['buffett', 'duan', 'munger']

### SOFT

- `cl_05` [qualitative_required] 护城河完全依赖单一专利、单一监管许可或单一客户（>50% 营收）的公司直接拒绝（qualitative_required 表述版本） — masters: ['buffett', 'munger']
- `cl_07` [valuation_method] 以精确 DCF 电子表格或依赖多重关键独立假设的复杂多情景模型为主要估值依据时拒绝该估值结论 — masters: ['buffett', 'duan']
- `cl_08` [quantitative_hard] 现金流转化率显著低于盈利（FCF/净利润 或 OCF/净利润）持续偏低的公司标记利润质量警告 — masters: ['buffett', 'duan']
- `cl_09` [valuation_method] 在业务质量、护城河持久性与管理层诚信前置验证完成之前，以估值指标（P/E、P/B、EV/EBITDA 等）为投资推荐首要依据时拒绝该结论 — masters: ['duan', 'munger']
- `cl_10` [position_sizing] 投资组合持仓数量超过 10 只标记过度分散警告（集中持仓纪律） — masters: ['buffett', 'duan']
- `cl_11` [qualitative_required] 评估竞争优势需具备前沿/高度专业技术知识（或行业不在能力圈清单内）的标的直接拒绝——能力圈铁律 — masters: ['buffett', 'duan']

### DROPPED

- `cl_06` [veto_line] 护城河完全依赖单一专利、单一监管许可或单一核心客户（>50% 营收）直接拒绝（veto_line 表述版本，与 cl_05 语义重合但 category 不同， — masters: ['duan']
- `cl_12` [quantitative_hard] 负债/EBITDA 超过 3 倍的公司直接拒绝 — masters: ['buffett']
- `cl_13` [quantitative_hard] 利息覆盖率低于 5 倍的公司直接拒绝 — masters: ['buffett']
- `cl_14` [quantitative_hard] ROE 连续 3 年以上下滑且同期行业中位 ROE 未同向下滑标记护城河侵蚀警告 — masters: ['buffett']
- `cl_15` [quantitative_hard] 毛利率连续 5 年以上下降的公司标记定价权丧失警告 — masters: ['buffett']
- `cl_16` [veto_line] 投资论据以宏观经济预测为核心前提时直接拒绝 — masters: ['buffett']
- `cl_17` [veto_line] 以季度收益超预期/低预期节奏为核心买卖依据直接拒绝 — masters: ['buffett']
- `cl_18` [valuation_method] 以尚未实现的市场机会（TAM 占比、期权价值、推测性产品线）为主要估值依据时拒绝 — masters: ['buffett']
- `cl_19` [veto_line] 牛市论点依赖超过2个相互独立关键假设同时成立的投资直接否决 — masters: ['munger']
- `cl_20` [veto_line] 金融机构或投资载体资产/权益杠杆 ≥25 倍直接否决 — masters: ['munger']
- `cl_21` [position_sizing] 新投资的风险调整预期回报未显著优于现有最高信念持仓时拒绝纳入（机会成本纪律） — masters: ['munger']
- `cl_22` [veto_line] 股票回购执行期间核心内部人净卖出直接否决 — masters: ['munger']
- `cl_23` [quantitative_hard] 过去5年财报中出现超过3次一次性调整项目的公司标记会计诚信警告 — masters: ['munger']
- `cl_24` [quantitative_hard] 分析模型依赖超过20个独立关键假设归入'太难'堆 — masters: ['munger']
- `cl_25` [quantitative_hard] 经营性现金流连续3年为负的公司直接拒绝 — masters: ['duan']
- `cl_26` [veto_line] 任何使用借贷资金（融资融券、配资等）的投资方案直接拒绝 — masters: ['duan']
- `cl_27` [veto_line] 任何做空头寸直接拒绝 — masters: ['duan']
- `cl_28` [qualitative_required] 有监管机构认定的财务造假或重大虚假陈述历史记录的公司直接拒绝 — masters: ['duan']
- `cl_29` [quantitative_hard] 核心管理层12个月内净减持超过总股本5%标记信心警告（若与回购同期则升级为veto） — masters: ['duan']
- `cl_30` [quantitative_hard] 有息负债率连续3年上升且最新值超过50%标记资产负债表风险警告 — masters: ['duan']
- `cl_31` [veto_line] 以'赛道''风口''蓝海''政策红利'等概念为核心买入理由直接拒绝 — masters: ['duan']
- `cl_32` [position_sizing] 预设持有期不足10年的买入论点直接拒绝 — masters: ['duan']
