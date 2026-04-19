# value-investing-gurus.pages.dev 扫描（scan_2026-04-19_vig）

**抓取时间**：2026-04-19T13:58:06.153119+00:00 → 2026-04-19T14:01:59.506166+00:00

**编者**：用户的投资人朋友（见方法论文章《我用AI整理了巴菲特和芒格69年的思想遗产》）

**抓取统计**：
- 尝试：134
- 成功：53
- 重复：0
- 失败：81

**覆盖**：
- zh 全部：120 篇（concept 63 + source 43 + synthesis 12 + entity 2）
- en 选择性：entity + synthesis（14 篇，用于双语校对）
- 跳过：en concept/source（与已有 primary 冗余）

**Tier 分级**：
- concept/synthesis/entity：P4（编者综合）
- source：P3（编者对原件的提炼，我们多数已有 P0 原件）

**如何使用**：
- 浏览：`concept/` `synthesis/` `source/` `entity/` 子目录下的 `.zh.md` 文件
- 每个文件含 YAML frontmatter 标注来源 + 主题 + tier + masters
- 段落锚点 `<!-- p:XXXXXX -->` 便于 extraction 回溯

**下一步**：
- Phase B：LLM 按决策导向 prompt 抽取 extractions
- Phase C-E：匹配 → 验证 NEEDS VERIFICATION → 整合到 W/C v1.1

失败列表（如有）：
```json
[
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/business_quality.txt: IncompleteRead(36545 bytes read, 3614 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/business_quality.txt",
    "article_id": "business_quality",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/accounting_quality.txt: IncompleteRead(32790 bytes read, 3988 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/accounting_quality.txt",
    "article_id": "accounting_quality",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/capital_allocation.txt: IncompleteRead(43434 bytes read, 196 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/capital_allocation.txt",
    "article_id": "capital_allocation",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/acquisition_strategy.txt: IncompleteRead(36545 bytes read, 968 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/acquisition_strategy.txt",
    "article_id": "acquisition_strategy",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/circle_of_competence.txt: IncompleteRead(36545 bytes read, 3655 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/circle_of_competence.txt",
    "article_id": "circle_of_competence",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/cognitive_biases.txt: IncompleteRead(35176 bytes read, 4042 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/cognitive_biases.txt",
    "article_id": "cognitive_biases",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/competitive_moat.txt: IncompleteRead(40306 bytes read, 1166 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/competitive_moat.txt",
    "article_id": "competitive_moat",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/commodity_economics.txt: IncompleteRead(17027 bytes read, 4612 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/commodity_economics.txt",
    "article_id": "commodity_economics",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/communication.txt: IncompleteRead(15660 bytes read, 878 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/communication.txt",
    "article_id": "communication",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/compounding.txt: IncompleteRead(28331 bytes read, 3510 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/compounding.txt",
    "article_id": "compounding",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/concentrated_investing.txt: IncompleteRead(34822 bytes read, 4559 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/concentrated_investing.txt",
    "article_id": "concentrated_investing",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/corporate_governance.txt: IncompleteRead(41004 bytes read, 566 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/corporate_governance.txt",
    "article_id": "corporate_governance",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/fixed_income.txt: IncompleteRead(12918 bytes read, 1611 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/fixed_income.txt",
    "article_id": "fixed_income",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/free_cash_flow.txt: IncompleteRead(7446 bytes read, 3167 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/free_cash_flow.txt",
    "article_id": "free_cash_flow",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/decision_making.txt: IncompleteRead(39283 bytes read, 593 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/decision_making.txt",
    "article_id": "decision_making",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/friction_costs.txt: IncompleteRead(29350 bytes read, 3506 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/friction_costs.txt",
    "article_id": "friction_costs",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/institutional_imperative.txt: IncompleteRead(37556 bytes read, 1680 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/institutional_imperative.txt",
    "article_id": "institutional_imperative",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/inflation.txt: IncompleteRead(33851 bytes read, 4773 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/inflation.txt",
    "article_id": "inflation",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/insurance_economics.txt: IncompleteRead(28727 bytes read, 2529 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/insurance_economics.txt",
    "article_id": "insurance_economics",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/intrinsic_value.txt: IncompleteRead(54738 bytes read, 5872 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/intrinsic_value.txt",
    "article_id": "intrinsic_value",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/learning_and_growth.txt: IncompleteRead(39283 bytes read, 1333 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/learning_and_growth.txt",
    "article_id": "learning_and_growth",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/inversion.txt: IncompleteRead(26962 bytes read, 2566 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/inversion.txt",
    "article_id": "inversion",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/leverage_and_risk.txt: IncompleteRead(40294 bytes read, 1955 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/leverage_and_risk.txt",
    "article_id": "leverage_and_risk",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/liquidity.txt: IncompleteRead(18792 bytes read, 3765 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/liquidity.txt",
    "article_id": "liquidity",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/lollapalooza_effect.txt: IncompleteRead(7450 bytes read, 2678 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/lollapalooza_effect.txt",
    "article_id": "lollapalooza_effect",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/management.txt: IncompleteRead(36545 bytes read, 3501 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/management.txt",
    "article_id": "management",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/margin_of_safety.txt: IncompleteRead(35176 bytes read, 3669 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/margin_of_safety.txt",
    "article_id": "margin_of_safety",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/mental_models.txt: IncompleteRead(30713 bytes read, 3064 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/mental_models.txt",
    "article_id": "mental_models",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/market_psychology.txt: IncompleteRead(36545 bytes read, 3166 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/market_psychology.txt",
    "article_id": "market_psychology",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/opportunity_cost.txt: IncompleteRead(36545 bytes read, 4602 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/opportunity_cost.txt",
    "article_id": "opportunity_cost",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/owner_operator_mindset.txt: IncompleteRead(40652 bytes read, 1451 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/owner_operator_mindset.txt",
    "article_id": "owner_operator_mindset",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/partnership_principles.txt: IncompleteRead(36545 bytes read, 3312 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/partnership_principles.txt",
    "article_id": "partnership_principles",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/passive_vs_active_investing.txt: IncompleteRead(26962 bytes read, 2962 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/passive_vs_active_investing.txt",
    "article_id": "passive_vs_active_investing",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/private_market_value.txt: IncompleteRead(11947 bytes read, 2100 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/private_market_value.txt",
    "article_id": "private_market_value",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/preparation_and_decisiveness.txt: IncompleteRead(25593 bytes read, 3029 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/preparation_and_decisiveness.txt",
    "article_id": "preparation_and_decisiveness",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/portfolio_management.txt: IncompleteRead(34826 bytes read, 1866 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/portfolio_management.txt",
    "article_id": "portfolio_management",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/return_on_capital.txt: IncompleteRead(33451 bytes read, 2453 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/return_on_capital.txt",
    "article_id": "return_on_capital",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/tax_efficiency.txt: IncompleteRead(44759 bytes read, 2453 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/tax_efficiency.txt",
    "article_id": "tax_efficiency",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/shareholder_returns.txt: IncompleteRead(36189 bytes read, 2452 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/shareholder_returns.txt",
    "article_id": "shareholder_returns",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/special_situations.txt: IncompleteRead(19757 bytes read, 4917 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/special_situations.txt",
    "article_id": "special_situations",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/temperament_and_discipline.txt: IncompleteRead(34828 bytes read, 2869 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/temperament_and_discipline.txt",
    "article_id": "temperament_and_discipline",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/concepts/valuation.txt: IncompleteRead(36589 bytes read, 3825 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/concepts/valuation.txt",
    "article_id": "valuation",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/entities/warren_buffett.txt: IncompleteRead(7841 bytes read, 1343 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/entities/warren_buffett.txt",
    "article_id": "warren_buffett",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/academic_economics_strengths_and_faults_charlie_munger_ucsb_2003.txt: IncompleteRead(15037 bytes read, 1227 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/academic_economics_strengths_and_faults_charlie_munger_ucsb_2003.txt",
    "article_id": "academic_economics_strengths_and_faults_charlie_munger_ucsb_2003",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_i.txt: IncompleteRead(28683 bytes read, 2488 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_i.txt",
    "article_id": "acquired_podcast_berkshire_hathaway_part_i",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_ii.txt: IncompleteRead(29700 bytes read, 2970 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_ii.txt",
    "article_id": "acquired_podcast_berkshire_hathaway_part_ii",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_iii.txt: IncompleteRead(26604 bytes read, 2238 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/acquired_podcast_berkshire_hathaway_part_iii.txt",
    "article_id": "acquired_podcast_berkshire_hathaway_part_iii",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2014.txt: IncompleteRead(28375 bytes read, 3121 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2014.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2014",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2013.txt: IncompleteRead(21882 bytes read, 1816 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2013.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2013",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2016.txt: IncompleteRead(25593 bytes read, 499 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2016.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2016",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2015.txt: IncompleteRead(24224 bytes read, 2648 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2015.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2015",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2019.txt: IncompleteRead(14287 bytes read, 1203 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2019.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2019",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2017.txt: IncompleteRead(12299 bytes read, 4017 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2017.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2017",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2022.txt: IncompleteRead(7840 bytes read, 2750 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2022.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2022",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2020.txt: IncompleteRead(13316 bytes read, 1470 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2020.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2020",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2024.txt: IncompleteRead(10170 bytes read, 418 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2024.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2024",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2025.txt: IncompleteRead(11549 bytes read, 4307 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/berkshire_hathaway_shareholder_letter_2025.txt",
    "article_id": "berkshire_hathaway_shareholder_letter_2025",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_from_japan_on_trading_companies_apr_2023.txt: IncompleteRead(21530 bytes read, 2685 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_from_japan_on_trading_companies_apr_2023.txt",
    "article_id": "cnbc_buffett_from_japan_on_trading_companies_apr_2023",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_gates_munger_on_squawk_box_may_2014.txt: IncompleteRead(20513 bytes read, 1340 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_gates_munger_on_squawk_box_may_2014.txt",
    "article_id": "cnbc_buffett_gates_munger_on_squawk_box_may_2014",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_charlie_munger_a_life_of_wit_and_wisdom_final_interview_nov_2023.txt: IncompleteRead(7840 bytes read, 2819 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_charlie_munger_a_life_of_wit_and_wisdom_final_interview_nov_2023.txt",
    "article_id": "cnbc_charlie_munger_a_life_of_wit_and_wisdom_final_interview_nov_2023",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_post_ceo_transition_interview_mar_2026.txt: IncompleteRead(14287 bytes read, 2611 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_buffett_post_ceo_transition_interview_mar_2026.txt",
    "article_id": "cnbc_buffett_post_ceo_transition_interview_mar_2026",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_gates_buffett_keeping_america_great_columbia_2009.txt: IncompleteRead(14289 bytes read, 1922 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/cnbc_gates_buffett_keeping_america_great_columbia_2009.txt",
    "article_id": "cnbc_gates_buffett_keeping_america_great_columbia_2009",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/complete_buffett_partnership_letters_1957_70_warren_buffet_z_librarysk_1libsk_z_.txt: IncompleteRead(32088 bytes read, 1220 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/complete_buffett_partnership_letters_1957_70_warren_buffet_z_librarysk_1libsk_z_.txt",
    "article_id": "complete_buffett_partnership_letters_1957_70_warren_buffet_z_librarysk_1libsk_z_",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/warren_buffett_talk_at_university_of_florida_1998.txt: IncompleteRead(19753 bytes read, 294 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/warren_buffett_talk_at_university_of_florida_1998.txt",
    "article_id": "warren_buffett_talk_at_university_of_florida_1998",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/poor_charlies_almanack_expanded_third_edition.txt: IncompleteRead(38921 bytes read, 1284 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/poor_charlies_almanack_expanded_third_edition.txt",
    "article_id": "poor_charlies_almanack_expanded_third_edition",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/sources/wesco_financial_charlie_munger_letters_1983_2009.txt: IncompleteRead(32438 bytes read, 4465 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/sources/wesco_financial_charlie_munger_letters_1983_2009.txt",
    "article_id": "wesco_financial_charlie_munger_letters_1983_2009",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/buffett_munger_evolution.txt: IncompleteRead(11947 bytes read, 832 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/buffett_munger_evolution.txt",
    "article_id": "buffett_munger_evolution",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/management_evaluation.txt: IncompleteRead(10578 bytes read, 3401 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/management_evaluation.txt",
    "article_id": "management_evaluation",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/mental_models_lattice.txt: IncompleteRead(12918 bytes read, 1935 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/mental_models_lattice.txt",
    "article_id": "mental_models_lattice",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/moat_identification_framework.txt: IncompleteRead(13316 bytes read, 1269 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/moat_identification_framework.txt",
    "article_id": "moat_identification_framework",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/valuation_in_practice.txt: IncompleteRead(7442 bytes read, 4042 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/zh/articles/syntheses/valuation_in_practice.txt",
    "article_id": "valuation_in_practice",
    "lang": "zh"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/entities/charlie_munger.txt: IncompleteRead(7446 bytes read, 2556 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/entities/charlie_munger.txt",
    "article_id": "charlie_munger",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/berkshire_organizational_model.txt: IncompleteRead(12916 bytes read, 1862 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/berkshire_organizational_model.txt",
    "article_id": "berkshire_organizational_model",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/capital_allocation_ceo_most_important_job.txt: IncompleteRead(11947 bytes read, 1958 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/capital_allocation_ceo_most_important_job.txt",
    "article_id": "capital_allocation_ceo_most_important_job",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/buffett_munger_evolution.txt: IncompleteRead(11543 bytes read, 2297 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/buffett_munger_evolution.txt",
    "article_id": "buffett_munger_evolution",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/insurance_float_machine.txt: IncompleteRead(10178 bytes read, 4933 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/insurance_float_machine.txt",
    "article_id": "insurance_float_machine",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/intrinsic_value_theory_and_practice.txt: IncompleteRead(12924 bytes read, 1258 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/intrinsic_value_theory_and_practice.txt",
    "article_id": "intrinsic_value_theory_and_practice",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/management_evaluation.txt: IncompleteRead(12922 bytes read, 2012 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/management_evaluation.txt",
    "article_id": "management_evaluation",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/mental_models_lattice.txt: IncompleteRead(13316 bytes read, 3341 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/mental_models_lattice.txt",
    "article_id": "mental_models_lattice",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/mistakes_and_lessons.txt: IncompleteRead(11547 bytes read, 583 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/mistakes_and_lessons.txt",
    "article_id": "mistakes_and_lessons",
    "lang": "en"
  },
  {
    "error": "Failed https://value-investing-gurus.pages.dev/api/en/articles/syntheses/valuation_in_practice.txt: IncompleteRead(10578 bytes read, 2110 more expected)",
    "url": "https://value-investing-gurus.pages.dev/api/en/articles/syntheses/valuation_in_practice.txt",
    "article_id": "valuation_in_practice",
    "lang": "en"
  }
]
```
