"""Populates the dashboard with two demo eval runs so the project is
viewable immediately, with no API key required (uses the mock judge).

Run: python scripts/seed_demo_data.py
Then: python -m auto_grader.dashboard
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_grader import db
from auto_grader.loader import load_test_cases
from auto_grader.pipeline import run_eval

TEST_CASES_PATH = Path(__file__).resolve().parent.parent / "test_cases" / "sample_cases.json"

# Deliberately-flawed "baseline model" responses — one bug per test case,
# matching the category each test case is designed to catch.
WEAK_RESPONSES = {
    "sum_list": "def solution(nums):\n    return sum(nums) if nums else None\n",
    "off_by_one": "def solution(n):\n    return list(range(n))\n",
    "fib_efficiency": (
        "def solution(n):\n"
        "    if n < 2:\n"
        "        return n\n"
        "    return solution(n - 1) + solution(n - 2)\n"
    ),
    "hallucinated_import": (
        "import fakelib\n\n"
        "def solution(text):\n"
        "    return fakelib.strip_vowels(text)\n"
    ),
    "safe_eval": "def solution(expr):\n    return eval(expr)\n",
    "edge_case_divide": "def solution(a, b):\n    return a / b\n",
    "dedupe_preserve_order": "def solution(items):\n    return list(dict.fromkeys(items))[::-1]\n",
    "string_reversal": "def solution(s):\n    return s\n",
}

# Clean, corrected "improved model" responses.
STRONG_RESPONSES = {
    "sum_list": "def solution(nums):\n    return sum(nums)\n",
    "off_by_one": "def solution(n):\n    return list(range(n + 1))\n",
    "fib_efficiency": (
        "def solution(n):\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    ),
    "hallucinated_import": (
        "def solution(text):\n"
        "    return ''.join(c for c in text if c.lower() not in 'aeiou')\n"
    ),
    "safe_eval": (
        "import ast, operator\n\n"
        "def solution(expr):\n"
        "    tree = ast.parse(expr, mode='eval')\n"
        "    ops = {ast.Add: operator.add, ast.Sub: operator.sub}\n\n"
        "    def _eval(node):\n"
        "        if isinstance(node, ast.Expression):\n"
        "            return _eval(node.body)\n"
        "        if isinstance(node, ast.BinOp):\n"
        "            return ops[type(node.op)](_eval(node.left), _eval(node.right))\n"
        "        if isinstance(node, ast.Constant):\n"
        "            return node.value\n"
        "        raise ValueError('unsupported expression')\n\n"
        "    return _eval(tree)\n"
    ),
    "edge_case_divide": (
        "def solution(a, b):\n"
        "    if b == 0:\n"
        "        return None\n"
        "    return a / b\n"
    ),
    "dedupe_preserve_order": "def solution(items):\n    return list(dict.fromkeys(items))\n",
    "string_reversal": "def solution(s):\n    return s[::-1]\n",
}


def main():
    test_cases = load_test_cases(TEST_CASES_PATH)

    db.init_db()
    print("Seeding baseline run...")
    run_eval("baseline-model-v1", "Baseline (v1)", WEAK_RESPONSES, test_cases)
    print("Seeding improved run...")
    run_eval("improved-model-v2", "Improved (v2)", STRONG_RESPONSES, test_cases)
    print("Done. Start the dashboard with: python -m auto_grader.dashboard")


if __name__ == "__main__":
    main()
