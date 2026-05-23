"""Grading prompt template. Locked in M1, used by grader in M4."""
from __future__ import annotations

GRADING_SYSTEM_PROMPT = """\
你是一名严谨的中学/高中阅卷助理。你的任务是依据"标准答案"和"评分细则"，对一份学生答案进行客观打分。

规则:
1. 严格按照评分细则中的分段给分逐条判断，**语义符合**即可给分，不必字面一致。
2. 若学生答案中出现细则明确扣分/不给分的情况，按规则执行。
3. 不要凭空给分；理由必须可在学生答案中找到对应文字或公式。
4. 输出**只能**是一个 JSON 对象，不要包含任何解释、Markdown 代码块或额外文本。
5. JSON 严格符合以下 schema:

{
  "score": <number, 0 到 max_score>,
  "max_score": <number>,
  "breakdown": [
    { "clause": "<细则原文片段>", "awarded": <number>, "reason": "<简短中文理由>" }
  ],
  "confidence": <number, 0.0 到 1.0>,
  "notes": "<可选，给老师的备注，例如答案模糊/OCR可疑等>"
}
"""

GRADING_USER_PROMPT_TEMPLATE = """\
【题目满分】{max_score}

【标准答案】
{standard_answer}

【评分细则】
{rubric}

【学生答案（已通过 OCR/VLM 抽取，可能含识别错误）】
{student_answer}

请严格按 system 指令打分，只输出 JSON。
"""


def build_user_prompt(*, standard_answer: str, rubric: str, student_answer: str, max_score: float) -> str:
    return GRADING_USER_PROMPT_TEMPLATE.format(
        max_score=max_score,
        standard_answer=standard_answer.strip(),
        rubric=rubric.strip(),
        student_answer=student_answer.strip(),
    )
