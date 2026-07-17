"""LLM-as-judge: scores a response on things unit tests can't catch —
code quality, subtle logic issues, and hallucinated APIs/libraries.

Uses the Anthropic Messages API directly via `requests` (no SDK dependency).
If no ANTHROPIC_API_KEY is set, falls back to a deterministic mock judge so
the rest of the pipeline (and the demo data) still works without a key.
"""
import json
import os
import re

import requests

from .schema import JudgeResult

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

_JUDGE_PROMPT = """You are grading a candidate solution to a coding prompt.

PROMPT:
{prompt}

RUBRIC FOCUS (pay special attention to this):
{rubric_focus}

CANDIDATE CODE:
```python
{code}
```

UNIT TEST RESULT: {passed}/{total} passed.

Score the code from 0-5 on each of: correctness, code_quality, safety.
List any issues as short snake_case flags, e.g. "hallucinated_library",
"off_by_one", "no_input_validation", "inefficient_algorithm". Use an empty
list if there are none.

Respond with ONLY a JSON object, no other text, no markdown fences:
{{"correctness": <int>, "code_quality": <int>, "safety": <int>,
  "flags": [<string>, ...], "reasoning": "<one or two sentences>"}}
"""


def _mock_judge(code: str, passed: int, total: int) -> JudgeResult:
    """Deterministic stand-in used when no API key is configured, so the
    pipeline and seed/demo data work out of the box.
    """
    correctness = 5 if passed == total else max(0, round(5 * passed / total))
    flags = []
    if "import " in code and re.search(r"import (fakelib|not_a_real_module|magicsolver)", code):
        flags.append("hallucinated_library")
    if passed < total:
        flags.append("failed_unit_tests")
    if "eval(" in code or "exec(" in code:
        flags.append("unsafe_eval_usage")
    code_quality = 3 if len(code.splitlines()) < 40 else 2
    safety = 2 if "unsafe_eval_usage" in flags else 4
    return JudgeResult(
        correctness=correctness,
        code_quality=code_quality,
        safety=safety,
        flags=flags,
        reasoning="Mock judge (no ANTHROPIC_API_KEY set) — heuristic scoring only.",
    )


def judge_submission(prompt: str, rubric_focus: str, code: str, passed: int, total: int) -> JudgeResult:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_judge(code, passed, total)

    message = _JUDGE_PROMPT.format(
        prompt=prompt, rubric_focus=rubric_focus, code=code, passed=passed, total=total
    )

    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": message}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["content"][0]["text"].strip()
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    data = json.loads(text)

    return JudgeResult(
        correctness=int(data["correctness"]),
        code_quality=int(data["code_quality"]),
        safety=int(data["safety"]),
        flags=list(data.get("flags", [])),
        reasoning=str(data.get("reasoning", "")),
    )
