"""
GPT-5.3-thinking adversarial review of Soul Documents v1.0
Uses OpenRouter API (OpenAI-compatible) to review each master's soul document.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from openai import AsyncOpenAI

OPENROUTER_API_KEY = "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"
MODEL = "openai/gpt-5.4-20260305"

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

DOCS_DIR = Path(__file__).parent.parent / "src" / "souls" / "documents"
REVIEWS_DIR = DOCS_DIR / "reviews"

REVIEW_PROMPT_EN = """You are an adversarial reviewer for a Soul Document — a comprehensive philosophical profile of an investment master, used to power an AI agent that thinks like this person.

Your job is NOT to polish or improve the writing. Your job is to perform 5 specific adversarial checks and report findings with surgical precision.

## The Document to Review

{document}

## The Other Two Masters' Documents (for cross-comparison)

### Master {other1_name}:
{other1_summary}

### Master {other2_name}:
{other2_summary}

## Your 5 Adversarial Checks

### Check 1: FABRICATION DETECTION
Flag any statement that:
- Sounds plausible but may not be factually accurate
- Attributes specific quotes without clear sourcing
- Describes specific events, dates, or numbers that could be LLM confabulation
- Presents speculation as established fact

For each finding: quote the exact text, explain why it's suspicious, rate confidence (HIGH/MEDIUM/LOW that it's fabricated).

### Check 2: CONVERGENCE DETECTION
Flag any content that:
- Uses generic value investing language that could apply to ANY investor
- Is too similar to what was said in the other two masters' documents
- Presents this master's unique thinking in terms that are interchangeable with another master
- Falls back on "textbook" investment principles instead of this person's specific approach

For each finding: quote the exact text, identify which other master it sounds like, suggest how to make it genuinely distinctive.

### Check 3: DEPTH DETECTION
Flag any content that:
- States a principle without explaining its boundary conditions
- Describes a reasoning chain as "he analyzed it and decided to buy" without showing the actual steps
- Uses vague language ("thorough analysis", "careful evaluation") instead of specifics
- Claims a principle exists without showing how it manifests in actual decisions

For each finding: quote the exact text, explain what's missing, suggest what deeper content should replace it.

### Check 4: CONTRADICTION DETECTION
Flag any content where:
- A principle in one module contradicts a reasoning chain in another
- The "iron laws" are violated in the case studies without acknowledgment
- The failure cases don't actually match the claimed lessons learned
- The differentiation claims are contradicted elsewhere in the document

For each finding: quote both contradicting passages, explain the inconsistency.

### Check 5: OMISSION DETECTION
Identify the most important aspects of this master's thinking that are MISSING:
- Key investments not discussed
- Important philosophical positions not covered
- Critical life events that shaped their thinking but are absent
- Well-known quotes or concepts that should be included

For each finding: describe what's missing, explain why it matters, rate importance (CRITICAL/IMPORTANT/NICE-TO-HAVE).

## Output Format

For each check, provide findings in this structure:

```
## Check N: [CHECK NAME]

### Finding N.1
- **Text:** "[exact quote from document]"
- **Issue:** [what's wrong]
- **Confidence:** HIGH/MEDIUM/LOW
- **Suggested Fix:** [specific recommendation]

### Finding N.2
...
```

End with a **Summary** section: overall quality score (1-10), top 3 most critical issues, and whether this document is ready for v1.0 after fixes or needs major rewrite.

Be thorough. Be harsh. This document will be used to make real investment decisions. False accuracy is worse than admitted gaps.
"""

REVIEW_PROMPT_ZH = """你是一个灵魂文档的对抗性审阅者。灵魂文档是投资大师的全面哲学画像，用于驱动一个像这个人一样思考的 AI agent。

你的工作不是润色文字。你的工作是执行 5 项具体的对抗性检查，并以外科手术般的精确度报告发现。

## 待审阅文档

{document}

## 另外两位大师的文档（用于交叉比较）

### {other1_name} 大师：
{other1_summary}

### {other2_name} 大师：
{other2_summary}

## 5 项对抗性检查

### 检查 1：虚构检测
标记任何：
- 听起来合理但可能不是事实准确的陈述
- 没有明确来源的具体引语
- 可能是 LLM 编造的具体事件、日期或数字
- 把推测当作既定事实

每项发现：引用原文、解释为什么可疑、标注置信度（HIGH/MEDIUM/LOW，指"被虚构"的可能性）

### 检查 2：趋同检测
标记任何：
- 使用通用价值投资语言，可以套用在任何投资者身上的内容
- 与另外两位大师文档中的表述过于相似
- 用可以互换的方式呈现这位大师的独特思维
- 退回到"教科书"投资原则而非这个人的具体方法

每项发现：引用原文、指出像哪位大师、建议如何差异化

### 检查 3：深度检测
标记任何：
- 陈述原则但没解释其边界条件
- 用"他分析后决定买入"代替实际的推理步骤
- 使用模糊语言（"深入分析"、"仔细评估"）而非具体内容
- 声称某原则存在但没展示它如何在实际决策中体现

每项发现：引用原文、解释缺少什么、建议应替换为什么更深入的内容

### 检查 4：矛盾检测
标记任何：
- 一个模块中的原则与另一个模块中的推理链矛盾
- 案例研究中违反了"铁律"但没承认
- 失败案例与声称的教训不匹配
- 差异化声明在文档其他地方被矛盾

每项发现：引用两段矛盾的文字、解释不一致之处

### 检查 5：遗漏检测
识别这位大师思维中最重要的缺失方面：
- 未讨论的关键投资
- 未覆盖的重要哲学立场
- 塑造了其思维但缺失的关键人生事件
- 应被包含的知名语录或概念

每项发现：描述缺失内容、解释为什么重要、标注重要性（CRITICAL/IMPORTANT/NICE-TO-HAVE）

## 输出格式

对每项检查，按此结构提供发现：

```
## 检查 N：[检查名称]

### 发现 N.1
- **原文：** "[文档中的确切引用]"
- **问题：** [有什么问题]
- **置信度：** HIGH/MEDIUM/LOW
- **修改建议：** [具体建议]

### 发现 N.2
...
```

最后附 **总结** 部分：总体质量分（1-10）、最关键的 3 个问题、以及这份文档在修复后是否可以作为 v1.0 还是需要大幅重写。

要彻底。要严格。这份文档将用于做真实的投资决策。虚假的准确性比承认的空白更危险。
"""


def make_summary(text: str, max_chars: int = 3000) -> str:
    """Extract a summary of a document for cross-comparison (first N chars of key sections)."""
    lines = text.split('\n')
    summary_parts = []
    current_section = ""
    for line in lines:
        if line.startswith('## '):
            current_section = line
            summary_parts.append(f"\n{line}")
        elif line.startswith('### ') and len(summary_parts) < 20:
            summary_parts.append(line)
        elif line.strip() and not line.startswith('#') and len('\n'.join(summary_parts)) < max_chars:
            summary_parts.append(line)
    return '\n'.join(summary_parts)[:max_chars]


async def review_document(master_code: str, doc_path: Path, other_docs: dict) -> str:
    """Review a single soul document using GPT."""
    doc_text = doc_path.read_text()

    other_names = [k for k in other_docs if k != master_code]
    other1_name, other2_name = other_names[0], other_names[1]
    other1_summary = make_summary(other_docs[other1_name])
    other2_summary = make_summary(other_docs[other2_name])

    is_chinese = master_code == "Y"
    prompt_template = REVIEW_PROMPT_ZH if is_chinese else REVIEW_PROMPT_EN

    prompt = prompt_template.format(
        document=doc_text,
        other1_name=other1_name,
        other1_summary=other1_summary,
        other2_name=other2_name,
        other2_summary=other2_summary,
    )

    print(f"[{master_code}] Sending to GPT-5.3-thinking... ({len(doc_text)} chars)")

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=16000,
    )

    review_text = response.choices[0].message.content
    usage = response.usage
    print(f"[{master_code}] Review complete. Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out")

    return review_text


async def main():
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    doc_files = {
        "W": DOCS_DIR / "W-buffett-soul-v1.0.md",
        "C": DOCS_DIR / "C-munger-soul-v1.0.md",
        "Y": DOCS_DIR / "Y-duan-soul-v1.0.md",
    }

    # Load all documents for cross-comparison
    all_docs = {}
    for code, path in doc_files.items():
        if not path.exists():
            print(f"ERROR: {path} not found")
            sys.exit(1)
        all_docs[code] = path.read_text()

    # Run all 3 reviews in parallel
    tasks = []
    for code, path in doc_files.items():
        tasks.append(review_document(code, path, all_docs))

    results = await asyncio.gather(*tasks)

    # Save reviews
    for (code, _), review in zip(doc_files.items(), results):
        review_path = REVIEWS_DIR / f"{code}-review-gpt5.3.md"
        review_path.write_text(review)
        print(f"[{code}] Review saved to {review_path}")

    print("\nAll reviews complete.")


if __name__ == "__main__":
    asyncio.run(main())
