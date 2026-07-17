#!/usr/bin/env python3
"""CLI entry point: run a full evaluation and store it as a new dashboard run.

Usage:
    python run_eval.py --model gpt-4o-mini --label "GPT-4o mini" --responses my_responses.json

`my_responses.json` should map test_case_id -> submitted code, e.g.:
{
  "sum_list": "def solution(nums):\\n    return sum(nums)\\n",
  "off_by_one": "def solution(n):\\n    return list(range(n + 1))\\n"
}

Only include the test case IDs you have responses for — see
test_cases/sample_cases.json for the full set of IDs and prompts.

Set ANTHROPIC_API_KEY in your environment (or a .env file, see .env.example)
to use the real LLM judge. Without it, a deterministic mock judge is used
instead, so the pipeline still runs end-to-end.
"""
import argparse
import json
from pathlib import Path

from auto_grader.loader import load_test_cases
from auto_grader.pipeline import run_eval

TEST_CASES_PATH = Path(__file__).resolve().parent / "test_cases" / "sample_cases.json"


def main():
    parser = argparse.ArgumentParser(description="Run an LLM response eval and save it to the dashboard.")
    parser.add_argument("--model", required=True, help="Model name/tag for this run, e.g. gpt-4o-mini")
    parser.add_argument("--label", default="", help="Human-readable label shown on the dashboard")
    parser.add_argument("--responses", required=True, help="Path to a JSON file of {test_case_id: code}")
    args = parser.parse_args()

    test_cases = load_test_cases(TEST_CASES_PATH)
    responses = json.loads(Path(args.responses).read_text())

    unknown = set(responses) - set(test_cases)
    if unknown:
        raise SystemExit(f"Unknown test case id(s) in responses file: {unknown}")

    run_id = run_eval(args.model, args.label or args.model, responses, test_cases)
    print(f"Saved as run {run_id}. Start the dashboard to view it: python -m auto_grader.dashboard")


if __name__ == "__main__":
    main()
