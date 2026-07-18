"""Loads test case definitions from JSON into TestCase objects."""
import json
from pathlib import Path

from .schema import TestCase, UnitTest


def load_test_cases(path: str | Path) -> dict[str, TestCase]:
    data = json.loads(Path(path).read_text())
    cases = {}
    for item in data:
        unit_tests = [UnitTest(call=u["call"], expected=u["expected"]) for u in item["unit_tests"]]
        tc = TestCase(
            id=item["id"],
            category=item["category"],
            prompt=item["prompt"],
            entry_point=item["entry_point"],
            unit_tests=unit_tests,
            rubric_focus=item["rubric_focus"],
        )
        cases[tc.id] = tc
    return cases
