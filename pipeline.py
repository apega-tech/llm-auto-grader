"""Orchestrates the full grading flow for one model's set of responses:
run unit tests -> run LLM judge -> blend into a final score -> persist.
"""
from . import db
from .judge import judge_submission
from .runner import run_submission
from .schema import EvalResult, TestCase

# Blend weights for the final 0-100 score shown on the dashboard.
UNIT_TEST_WEIGHT = 0.6
JUDGE_WEIGHT = 0.4


def score_response(test_case: TestCase, code: str) -> EvalResult:
    check = run_submission(code, test_case)
    judge = judge_submission(
        prompt=test_case.prompt,
        rubric_focus=test_case.rubric_focus,
        code=code,
        passed=check.passed,
        total=check.total,
    )

    unit_score = check.pass_rate * 100
    judge_score = ((judge.correctness + judge.code_quality + judge.safety) / 15) * 100
    final = round(UNIT_TEST_WEIGHT * unit_score + JUDGE_WEIGHT * judge_score, 1)

    return EvalResult(
        test_case_id=test_case.id,
        model_name="",  # filled in by caller
        response_code=code,
        check=check,
        judge=judge,
        final_score=final,
    )


def run_eval(model_name: str, label: str, responses: dict[str, str], test_cases: dict[str, TestCase]) -> int:
    """responses: {test_case_id: code}. Returns the new run_id."""
    db.init_db()
    run_id = db.create_run(model_name, label)
    for tc_id, code in responses.items():
        test_case = test_cases[tc_id]
        result = score_response(test_case, code)
        result.model_name = model_name
        db.save_result(run_id, result)
    return run_id
