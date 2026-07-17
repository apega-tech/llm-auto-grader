"""Core data structures shared across the pipeline."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UnitTest:
    """A single executable check for a coding test case."""
    call: str          # e.g. "solution(2, 3)"
    expected: str       # Python literal, evaluated with ast.literal_eval, e.g. "5"


@dataclass
class TestCase:
    """One coding prompt in the eval set."""
    id: str
    category: str        # e.g. "off-by-one", "hallucinated-import", "correct"
    prompt: str
    entry_point: str      # name of the function the response must define
    unit_tests: list[UnitTest]
    rubric_focus: str     # what the LLM judge should pay special attention to


@dataclass
class CheckResult:
    """Result of running a response's code against unit tests."""
    passed: int
    total: int
    errors: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


@dataclass
class JudgeResult:
    """Structured output from the LLM-as-judge pass."""
    correctness: int      # 0-5
    code_quality: int      # 0-5
    safety: int            # 0-5
    flags: list[str]       # short tags, e.g. ["hallucinated_library", "off_by_one"]
    reasoning: str


@dataclass
class EvalResult:
    """Combined result for one (test_case, model_response) pair."""
    test_case_id: str
    model_name: str
    response_code: str
    check: CheckResult
    judge: Optional[JudgeResult]
    final_score: float    # 0-100, blended score used for the dashboard
