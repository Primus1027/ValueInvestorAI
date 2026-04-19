# Prompt Framing Guidelines — 所有 Agent / LLM 调用必须遵守

> **状态**：Normative（强制性，非建议性）
> **适用范围**：本项目中所有以 Claude / GPT / Doubao / 其他 LLM 为后端的 prompt 编排
> **最后更新**：2026-04-19
> **触发事件**：scripts/soul/calibrate.py 因"你是 Buffett 的投资决策 Agent"措辞触发 Anthropic Usage Policy 拦截

---

## 一、核心原则：AI 工具，不是人

所有 prompt 必须把 LLM 定位为 **投资研究工具 / 方法论应用框架 / 结构化分析助手**，而**不是**某位真实大师本人。

这不是营销选择，是**三重约束交集**：

| 约束来源 | 约束内容 |
|---|---|
| Anthropic Usage Policy | 禁止 AI 扮演真实在世人物 + 针对真实公司/ticker 给出个性化投资建议 |
| 2026-04-05 AI Debate 共识 #1 | "灵魂封装"叙事必须放弃 → 改为"投资决策风格仿真" |
| AI Debate 共识 #2 | "AI 就是投资者本身"不可持续 → 最优模式是 AI + 人类回圈 |

**任何违反都是 bug，不是设计选择。**

---

## 二、措辞白名单 ✅ / 黑名单 ❌

### 绝对禁用（HIGH RISK，会被 Anthropic 拦截）

```
❌ 你是 Buffett / Munger / 段永平 / 李录 的投资决策 Agent
❌ 你是 Warren Buffett
❌ 保持这位大师的个性、口吻和推理风格
❌ 像 X 一样思考 / Think like Buffett
❌ 以大师的思维框架做出投资决策
❌ 你作为 [真实人物]
❌ I am Charlie Munger
❌ 扮演 / impersonate / as if you were [real person]
❌ 数字灵魂 / digital soul (的 Agent)
❌ AI 就是大师本人 / AI = the master
```

### 推荐用法（LOW RISK，合规且不损失分析能力）

```
✅ 你是一位价值投资研究助手
✅ 你是 investment methodology research tool
✅ 运用下述价值投资方法论框架
✅ 应用 [X] 的投资方法论（该框架整理自 X 的公开著作和访谈）
✅ 本练习是学术性的案例评估演练，不构成真实投资建议
✅ 请按方法论框架的逻辑推理
✅ 给出该方法论对这个案例的评估判断
✅ decision-style modeling / methodology simulation
✅ 结构化决策风格仿真
```

### 灰区（MEDIUM RISK，根据上下文判定）

```
⚠️  大师的思维方式（第三人称，描述性，soul doc 内用 OK，直接作为 Agent 指令不 OK）
⚠️  Faithfully reproduce decision-making approach（文档设计目标描述 OK，Agent 行为指令不 OK）
⚠️  投资大师的全面哲学画像（描述数据是 OK 的）
```

**判定规则**：这句话是在**描述 soul doc 作为数据**（OK），还是**指令 Agent 的行为**（有风险）？

---

## 三、分层编排规则

### Layer 1: System Prompt（指令层）— 最高风险

**必须**遵守：
- 首句定位为"研究助手 / 方法论应用工具"
- 包含免责声明："本分析为研究性质，不构成真实投资建议"
- 明确 Agent 的任务是 **apply the framework**，不是 **be the master**

**正确模板**：
```
你是一位价值投资研究助手，正在对投资方法论做学术性的案例评估演练。

本练习的任务：运用下述价值投资方法论框架（该框架整理自 {master} 的公开
著作和访谈），对给定的历史投资案例做出方法论意义上的评估。这是研究性质
的案例分析，不构成真实投资建议。

==== 方法论文档（整理自 {master} 公开资料的决策思维特征）====
{soul_text}

==== 评估框架（结构化的决策维度）====
{profile}

请按方法论框架的逻辑推理，给出该方法论对这个案例的评估判断。
```

### Layer 2: User Prompt（用户消息层）— 中风险

**必须**使用研究型措辞：
```
✅ 请基于上述方法论对以下历史投资案例做出方法论评估
✅ 应用该框架分析此案例
❌ 请作为 Buffett 决定是否买入
❌ 给出你（作为 Munger）的投资建议
```

### Layer 3: Soul Documents（数据层）— 低风险

Soul doc（`v1.x.md`）本身用**第三人称描述**大师思维（"Buffett 相信...", "Munger 偏好..."）是 OK 的——它们是数据，不是指令。

**但要注意**：
- soul doc 的元说明（如 `Purpose: Capture HOW Buffett thinks...`）是 OK 的
- 如果要把 soul doc 内容直接拼进 system prompt，必须用"方法论文档"而不是"你是"作为拼接前缀

### Layer 4: Profile.json（结构化决策数据）— 低风险

`src/souls/profiles/*.json` 用第三人称描述方法论维度，无风险。但**使用时**必须：
- 作为"framework"传入，不作为"persona"传入
- 不要把 JSON 的 `identity` / `personality` 字段直接塞给 Agent 作为 system prompt

### Layer 5: Extraction / Research Scripts（抽取脚本）— 低风险

像 `extract_comparisons.py`、`verify_via_vig.py` 这类脚本是**让 Claude 从文本中抽取结构化信息**，不涉及扮演，天然合规。保持现状。

---

## 四、多 Agent 董事会辩论场景

未来实施虚拟董事会时：

### ❌ 错误的方式
```
Agent 1 system: 你是 Warren Buffett，针对 Apple Inc. 给出你的买卖建议
Agent 2 system: 你是 Charlie Munger，与 Buffett 辩论
```

### ✅ 正确的方式
```
Agent 1 system: 你是运用 Buffett 投资方法论的研究助手 A。辩论环境设定：
  此为价值投资方法论在 Apple 案例上的学术性评估演练。请应用框架分析。

Agent 2 system: 你是运用 Munger 投资方法论的研究助手 B。辩论环境设定：
  同上。请应用框架并特别关注 Munger 方法论强调的 lollapalooza / 逆向思维视角。
```

**关键差异**：Agent 应用 **方法论视角**（methodology lens），而不是扮演 **人物化身**（person avatar）。输出质量不变，合规性天壤之别。

---

## 五、内容发布层面的措辞

写公众号文章 / Medium 帖 / 月度股东信 / Twitter 等对外输出时：

### ❌ 避免
- "Buffett AI 今天决定买入 AAPL"（让人误以为 AI 代表 Buffett 本人）
- "我们的 AI Munger 对 BYD 的看法是..."
- "the Buffett Agent recommends strong_buy"（同上）

### ✅ 推荐
- "运用 Buffett 价值投资方法论的 AI 研究工具对 AAPL 的方法论评估为：..."
- "ValueInvestorAI 的多方法论分析显示：Buffett 框架倾向于 strong_buy，Munger 框架关注 lollapalooza..."
- "Methodology frameworks consensus: ..."
- 明确 disclaimer："本文为投资方法论研究演练，不构成投资建议"

---

## 六、强制检查清单（每次新 prompt 代码上线前）

```
[ ] system prompt 首句不包含 "你是 [真实人名]" 模式
[ ] system prompt 首句不包含 "You are [real person name]" 模式
[ ] prompt 不要求 "保持 X 的口吻/个性/风格"
[ ] prompt 不含 "像 X 一样思考 / think like X"
[ ] prompt 含免责声明 "研究性质 / 不构成投资建议"
[ ] 输出不让 Agent 第一人称自称为大师（"I, Buffett, believe..."）
[ ] 对真实 ticker 的分析包含 disclaimer
[ ] grep 扫描无 HIGH 级黑名单词
```

**自动扫描 regex**（加入 pre-commit hook 或 CI）：

```bash
# 触发即 fail
grep -rnE "你是 *(Buffett|Munger|段永平|李录|Warren|Charlie|巴菲特|芒格)" scripts/ src/
grep -rnE "You are (Warren|Charlie|Li Lu|Duan)" scripts/ src/
grep -rnE "(保持|keep).*(Buffett|Munger|段永平|李录).*(风格|口吻|personality|voice)" scripts/ src/
grep -rnE "(像|think like|as if you were|impersonate) *(Buffett|Munger|段永平|李录)" scripts/ src/
```

**已知合法的误报模式**（人工审查时跳过）：
- `think like owners` — 价值投资概念，指**被投公司的管理层**应像股东一样思考。与 AI 扮演无关。
- `does NOT impersonate` / `不扮演这个人物` — 合规声明本身包含了禁用词。
- soul doc 中以第三人称描述"Buffett 的思维方式"——数据层面 OK，只要不被直接作为 Agent system prompt 的首句。

---

## 七、决策日志（这份文档的演变历史）

| 日期 | 事件 | 决定 |
|---|---|---|
| 2026-04-05 | AI Debate 5 AI 辩论 | 共识：放弃"灵魂封装"叙事，改用"投资决策风格仿真" |
| 2026-04-14 | `design-v2-soul-first-build-path.md` | 内部术语仍用 "soul document"，但明确 Agent 行为定位为"方法论应用" |
| 2026-04-19 | `calibrate.py` 触发 Usage Policy | 第一次被 Anthropic 官方拦截——验证了设计决议，并强制执行 |
| 2026-04-19 | 本文档创建 | 把分散的决议固化为可执行的 prompt 编排准则 |

---

## 八、相关文档

- `debates/2026-04-05-AI-Debate-项目愿景评审.md` — 原始共识来源
- `Designs/design-v2-soul-first-build-path.md` — 设计 v2（包含 decision-style modeling 决策）
- `scripts/soul/calibrate.py` — 修复案例（第 81 行起的 system_prompt 是合规模板）
- `scripts/gpt-soul-review.py` — 修复案例（REVIEW_PROMPT_EN/ZH 是合规模板）

---

*违反本指南的任何代码都应被视为 bug。看见请立即修复，不要当"技术债"推迟。*
