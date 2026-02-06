from app.schemas.compliance import Severity
from app.services.compliance.rules import (
    check_alcohol_content,
    check_government_warning,
    check_net_contents,
    run_regex_rules,
)


# --- Government Warning Tests ---

FULL_GOV_WARNING = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."""

PARTIAL_GOV_WARNING = """GOVERNMENT WARNING: WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY."""

NO_GOV_WARNING = """OLD TOM DISTILLERY\nKentucky Straight Bourbon Whiskey\n45% Alc./Vol."""


class TestGovernmentWarning:
    def test_full_warning_passes(self):
        result = check_government_warning(FULL_GOV_WARNING)
        assert result.severity == Severity.PASS
        assert result.rule_id == "GOV_WARNING"
        assert "8/8" in result.message

    def test_partial_warning_is_warning(self):
        result = check_government_warning(PARTIAL_GOV_WARNING)
        assert result.severity == Severity.WARNING
        assert "key phrases" in result.message

    def test_missing_warning_fails(self):
        result = check_government_warning(NO_GOV_WARNING)
        assert result.severity == Severity.FAIL

    def test_case_insensitive_header(self):
        text = "Government Warning: " + FULL_GOV_WARNING.split(":", 1)[1]
        result = check_government_warning(text)
        assert result.severity == Severity.PASS


# --- Alcohol Content Tests ---

class TestAlcoholContent:
    def test_percent_alc_vol(self):
        result = check_alcohol_content("45% Alc./Vol.")
        assert result.severity == Severity.PASS
        assert "45% Alc./Vol." in result.extracted_value

    def test_abv_format(self):
        result = check_alcohol_content("12.5% ABV")
        assert result.severity == Severity.PASS

    def test_proof_format(self):
        result = check_alcohol_content("90 Proof")
        assert result.severity == Severity.PASS
        assert "90 Proof" in result.extracted_value

    def test_missing_alcohol_content(self):
        result = check_alcohol_content("Old Tom Distillery Kentucky Bourbon")
        assert result.severity == Severity.FAIL

    def test_alc_vol_with_parenthetical_proof(self):
        result = check_alcohol_content("45% Alc./Vol. (90 Proof)")
        assert result.severity == Severity.PASS


# --- Net Contents Tests ---

class TestNetContents:
    def test_ml_format(self):
        result = check_net_contents("750 mL")
        assert result.severity == Severity.PASS
        assert "750 mL" in result.extracted_value

    def test_fl_oz_format(self):
        result = check_net_contents("12 FL OZ")
        assert result.severity == Severity.PASS

    def test_fl_oz_with_period(self):
        result = check_net_contents("12 FL. OZ.")
        assert result.severity == Severity.PASS

    def test_liter_format(self):
        result = check_net_contents("1 Liter")
        assert result.severity == Severity.PASS

    def test_missing_net_contents(self):
        result = check_net_contents("Old Tom Distillery Kentucky Bourbon")
        assert result.severity == Severity.FAIL


# --- Integration ---

class TestRunAllRegexRules:
    def test_complete_label_passes_all(self):
        text = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.

OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL"""
        findings = run_regex_rules(text)
        assert len(findings) == 3
        assert all(f.severity == Severity.PASS for f in findings)

    def test_empty_label_fails_all(self):
        findings = run_regex_rules("")
        assert len(findings) == 3
        assert all(f.severity == Severity.FAIL for f in findings)
