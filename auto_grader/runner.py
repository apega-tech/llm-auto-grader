"""Runs untrusted model-generated code against unit tests in a subprocess.

Deliberately does NOT use exec()/eval() in-process. Each submission is written
to a temp file and run as its own subprocess with a hard timeout, so a bad or
malicious response can't touch this process or hang the pipeline.
"""
import ast
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from .schema import CheckResult, TestCase

TIMEOUT_SECONDS = 5

_HARNESS_TEMPLATE = """
{solution_code}

import ast, json, sys

_results = []
_checks = {checks!r}

for _call, _expected in _checks:
    try:
        _actual = eval(_call)
        _expected_val = ast.literal_eval(_expected)
        _results.append({{"ok": _actual == _expected_val, "error": None}})
    except Exception as e:
        _results.append({{"ok": False, "error": f"{{type(e).__name__}}: {{e}}"}})

print(json.dumps(_results))
"""


def run_submission(code: str, test_case: TestCase) -> CheckResult:
    """Execute `code` (which must define test_case.entry_point) against all
    of test_case.unit_tests, in an isolated subprocess with a timeout.
    """
    checks = [(t.call, t.expected) for t in test_case.unit_tests]
    harness = _HARNESS_TEMPLATE.format(
        solution_code=textwrap.dedent(code),
        checks=checks,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "submission.py"
        script_path.write_text(harness)

        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                passed=0,
                total=len(checks),
                errors=[f"Timed out after {TIMEOUT_SECONDS}s (possible infinite loop)"],
            )

        if proc.returncode != 0:
            return CheckResult(
                passed=0,
                total=len(checks),
                errors=[f"Submission crashed: {proc.stderr.strip()[-500:]}"],
            )

        try:
            import json
            results = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception as e:
            return CheckResult(
                passed=0,
                total=len(checks),
                errors=[f"Could not parse test output: {e}"],
            )

        passed = sum(1 for r in results if r["ok"])
        errors = [r["error"] for r in results if r["error"]]
        return CheckResult(passed=passed, total=len(checks), errors=errors)
