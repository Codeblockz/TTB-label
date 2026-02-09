"""Parameterized tests that validate compliance rules against generated label ground truth."""

import csv
import os

import pytest

from app.schemas.compliance import Severity
from app.services.compliance.rules import run_regex_rules

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
CSV_PATH = os.path.join(FIXTURES_DIR, "generated_labels.csv")


def _load_test_cases() -> list[dict]:
    """Load test cases from the generated labels CSV."""
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _compute_verdict(findings: list) -> str:
    """Compute overall verdict from findings, matching ComplianceEngine logic."""
    severities = [f.severity for f in findings]
    if Severity.FAIL in severities:
        return "fail"
    if Severity.WARNING in severities:
        return "warnings"
    return "pass"


TEST_CASES = _load_test_cases()


@pytest.mark.parametrize(
    "case",
    TEST_CASES,
    ids=[c["filename"] for c in TEST_CASES],
)
class TestGeneratedLabels:
    def test_expected_verdict(self, case: dict) -> None:
        """Verify the overall verdict matches the expected value."""
        text = case["full_label_text"]
        findings = run_regex_rules(text)
        verdict = _compute_verdict(findings)
        assert verdict == case["expected_verdict"], (
            f"{case['filename']}: expected verdict '{case['expected_verdict']}', "
            f"got '{verdict}'"
        )

    def test_expected_failures(self, case: dict) -> None:
        """Verify exactly the expected rules fail (no more, no less)."""
        text = case["full_label_text"]
        findings = run_regex_rules(text)

        expected_fails = set(
            case["expected_failures"].split("|")
        ) if case["expected_failures"] else set()

        actual_fails = {
            f.rule_id for f in findings if f.severity == Severity.FAIL
        }

        assert actual_fails == expected_fails, (
            f"{case['filename']}: expected failures {expected_fails}, "
            f"got {actual_fails}"
        )

    def test_expected_warnings(self, case: dict) -> None:
        """Verify exactly the expected rules warn (no more, no less)."""
        text = case["full_label_text"]
        findings = run_regex_rules(text)

        expected_warns = set(
            case["expected_warnings"].split("|")
        ) if case["expected_warnings"] else set()

        actual_warns = {
            f.rule_id for f in findings if f.severity == Severity.WARNING
        }

        assert actual_warns == expected_warns, (
            f"{case['filename']}: expected warnings {expected_warns}, "
            f"got {actual_warns}"
        )

    def test_image_exists(self, case: dict) -> None:
        """Verify the generated image file actually exists."""
        image_path = os.path.join(FIXTURES_DIR, "generated", case["filename"])
        assert os.path.exists(image_path), (
            f"Image not found: {image_path}"
        )
