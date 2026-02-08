import json
from unittest.mock import AsyncMock

import pytest

from app.schemas.compliance import Severity
from app.services.compliance.engine import ComplianceEngine
from app.services.compliance.rules import (
    check_alcohol_content,
    check_brand_name,
    check_class_type,
    check_country_of_origin,
    check_gov_warning_complete,
    check_gov_warning_format,
    check_gov_warning_presence,
    check_name_address,
    check_net_contents,
    run_application_matching,
    run_regex_rules,
)


# --- Test Fixtures ---

FULL_GOV_WARNING = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."""

LOWERCASE_HEADER_WARNING = """Government Warning: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."""

CLAUSE_1_ONLY = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS."""

CLAUSE_2_ONLY = """GOVERNMENT WARNING: (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."""

NO_GOV_WARNING = """OLD TOM DISTILLERY\nKentucky Straight Bourbon Whiskey\n45% Alc./Vol."""


# --- Government Warning Presence Tests ---

class TestGovWarningPresence:
    def test_caps_header_passes(self):
        result = check_gov_warning_presence(FULL_GOV_WARNING)
        assert result.severity == Severity.PASS
        assert result.rule_id == "GOV_WARNING_PRESENCE"

    def test_lowercase_header_passes(self):
        result = check_gov_warning_presence(LOWERCASE_HEADER_WARNING)
        assert result.severity == Severity.PASS

    def test_missing_fails(self):
        result = check_gov_warning_presence(NO_GOV_WARNING)
        assert result.severity == Severity.FAIL


# --- Government Warning Format Tests ---

class TestGovWarningFormat:
    def test_caps_header_passes(self):
        result = check_gov_warning_format(FULL_GOV_WARNING)
        assert result.severity == Severity.PASS
        assert result.rule_id == "GOV_WARNING_FORMAT"

    def test_lowercase_header_warns(self):
        result = check_gov_warning_format(LOWERCASE_HEADER_WARNING)
        assert result.severity == Severity.WARNING

    def test_mixed_case_warns(self):
        text = "Government WARNING: some warning text here"
        result = check_gov_warning_format(text)
        assert result.severity == Severity.WARNING

    def test_missing_header_info(self):
        result = check_gov_warning_format(NO_GOV_WARNING)
        assert result.severity == Severity.INFO


# --- Government Warning Completeness Tests ---

class TestGovWarningComplete:
    def test_both_clauses_pass(self):
        result = check_gov_warning_complete(FULL_GOV_WARNING)
        assert result.severity == Severity.PASS
        assert result.rule_id == "GOV_WARNING_COMPLETE"
        assert "pregnancy:" in result.message
        assert "impairment:" in result.message

    def test_clause_1_only_warns(self):
        result = check_gov_warning_complete(CLAUSE_1_ONLY)
        assert result.severity == Severity.WARNING
        assert "incomplete" in result.message.lower()

    def test_clause_2_only_warns(self):
        result = check_gov_warning_complete(CLAUSE_2_ONLY)
        assert result.severity == Severity.WARNING

    def test_no_header_info(self):
        result = check_gov_warning_complete(NO_GOV_WARNING)
        assert result.severity == Severity.INFO

    def test_lowercase_text_still_matches_clauses(self):
        result = check_gov_warning_complete(LOWERCASE_HEADER_WARNING)
        assert result.severity == Severity.PASS

    def test_partial_clause_warns(self):
        text = "GOVERNMENT WARNING: women should not drink during pregnancy"
        result = check_gov_warning_complete(text)
        # Only 2 clause-1 phrases, 0 clause-2 phrases
        assert result.severity == Severity.WARNING


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


# --- Brand Name Tests ---

class TestBrandName:
    def test_sufficient_text_passes(self):
        result = check_brand_name("OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey")
        assert result.severity == Severity.PASS
        assert result.rule_id == "BRAND_NAME"

    def test_short_text_fails(self):
        result = check_brand_name("short")
        assert result.severity == Severity.FAIL

    def test_empty_text_fails(self):
        result = check_brand_name("")
        assert result.severity == Severity.FAIL

    def test_exactly_at_threshold(self):
        result = check_brand_name("a" * 20)
        assert result.severity == Severity.PASS

    def test_whitespace_only_fails(self):
        result = check_brand_name("          ")
        assert result.severity == Severity.FAIL


# --- Class/Type Tests ---

class TestClassType:
    def test_whiskey(self):
        result = check_class_type("Kentucky Straight Bourbon Whiskey")
        assert result.severity == Severity.PASS
        assert result.extracted_value is not None

    def test_vodka(self):
        result = check_class_type("Premium Vodka distilled five times")
        assert result.severity == Severity.PASS

    def test_wine_varietal(self):
        result = check_class_type("Napa Valley Cabernet Sauvignon 2019")
        assert result.severity == Severity.PASS

    def test_beer(self):
        result = check_class_type("India Pale Ale brewed with hops")
        assert result.severity == Severity.PASS

    def test_hard_seltzer(self):
        result = check_class_type("Hard Seltzer with natural flavors")
        assert result.severity == Severity.PASS

    def test_no_class_type(self):
        result = check_class_type("Premium Spirit Product 750 mL")
        assert result.severity == Severity.FAIL

    def test_case_insensitive(self):
        result = check_class_type("KENTUCKY STRAIGHT BOURBON WHISKEY")
        assert result.severity == Severity.PASS


# --- Name and Address Tests ---

class TestNameAddress:
    def test_distilled_by(self):
        result = check_name_address("Distilled by Old Tom Distillery, Louisville, KY")
        assert result.severity == Severity.PASS
        assert result.rule_id == "NAME_ADDRESS"

    def test_bottled_by(self):
        result = check_name_address("Bottled by Acme Spirits Co, Napa Valley, CA")
        assert result.severity == Severity.PASS

    def test_imported_by(self):
        result = check_name_address("Imported by Premium Imports Inc, New York, NY")
        assert result.severity == Severity.PASS

    def test_produced_by(self):
        result = check_name_address("Produced by Valley Winery, Sonoma, CA")
        assert result.severity == Severity.PASS

    def test_missing_address(self):
        result = check_name_address("Premium Vodka 750 mL 40% ABV")
        assert result.severity == Severity.FAIL

    def test_manufactured_by(self):
        result = check_name_address("Manufactured by Great Lakes Brewing, Cleveland, OH")
        assert result.severity == Severity.PASS


# --- Country of Origin Tests ---

class TestCountryOfOrigin:
    def test_product_of(self):
        result = check_country_of_origin("Product of Scotland")
        assert result.severity == Severity.PASS
        assert "Scotland" in result.extracted_value

    def test_imported_from(self):
        result = check_country_of_origin("Imported from Mexico")
        assert result.severity == Severity.PASS

    def test_made_in(self):
        result = check_country_of_origin("Made in USA")
        assert result.severity == Severity.PASS

    def test_missing_is_info(self):
        result = check_country_of_origin("Premium Vodka 750 mL")
        assert result.severity == Severity.INFO
        assert result.rule_id == "COUNTRY_ORIGIN"

    def test_producto_de(self):
        result = check_country_of_origin("Producto de Mexico")
        assert result.severity == Severity.PASS


# --- Application Matching Tests ---

COMPLETE_LABEL = """OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Distilled by Old Tom Distillery, Louisville, KY
Product of USA"""

COMPLETE_LABEL_WITH_WARNING = FULL_GOV_WARNING + "\n\n" + COMPLETE_LABEL


class TestApplicationMatching:
    def test_exact_match(self):
        details = {"brand_name": "OLD TOM DISTILLERY"}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 1
        assert findings[0].rule_id == "BRAND_MATCH"
        assert findings[0].severity == Severity.PASS

    def test_case_insensitive_match(self):
        details = {"brand_name": "old tom distillery"}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 1
        assert findings[0].severity == Severity.PASS

    def test_mismatch_fails(self):
        details = {"brand_name": "TOTALLY DIFFERENT BRAND"}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 1
        assert findings[0].severity == Severity.FAIL
        assert "Not found" in findings[0].message

    def test_fuzzy_word_match(self):
        # OCR might garble one word but get the rest right
        details = {"bottler_name_address": "Old Tom Distillery Louisville KY"}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 1
        assert findings[0].severity == Severity.PASS
        assert "words found" in findings[0].message or "expected value" in findings[0].message

    def test_multiple_fields(self):
        details = {
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "alcohol_content": "45% Alc./Vol.",
        }
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 3
        assert all(f.severity == Severity.PASS for f in findings)

    def test_empty_fields_skipped(self):
        details = {"brand_name": "", "class_type": None}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 0

    def test_class_type_match(self):
        details = {"class_type": "Bourbon Whiskey"}
        findings = run_application_matching(COMPLETE_LABEL, details)
        assert len(findings) == 1
        assert findings[0].rule_id == "CLASS_TYPE_MATCH"
        assert findings[0].severity == Severity.PASS


# --- Integration: Run All Regex Rules ---

class TestRunAllRegexRules:
    def test_complete_label_passes_all(self):
        findings = run_regex_rules(COMPLETE_LABEL_WITH_WARNING)
        assert len(findings) == 9
        for f in findings:
            assert f.severity in (Severity.PASS, Severity.INFO), (
                f"{f.rule_id} was {f.severity}, expected PASS or INFO"
            )

    def test_empty_label_fails_all(self):
        findings = run_regex_rules("")
        assert len(findings) == 9
        # GOV_WARNING_PRESENCE=FAIL, GOV_WARNING_FORMAT=INFO, GOV_WARNING_COMPLETE=INFO
        # BRAND_NAME=FAIL, CLASS_TYPE=FAIL, NAME_ADDRESS=FAIL, ALCOHOL_CONTENT=FAIL,
        # NET_CONTENTS=FAIL, COUNTRY_ORIGIN=INFO
        fail_count = sum(1 for f in findings if f.severity == Severity.FAIL)
        info_count = sum(1 for f in findings if f.severity == Severity.INFO)
        assert fail_count == 6
        assert info_count == 3  # COUNTRY_ORIGIN + GOV_WARNING_FORMAT + GOV_WARNING_COMPLETE


# --- Engine Integration Tests ---

def _make_llm_response(
    findings: list | None = None,
    gov_warning_bold: bool | None = None,
    beverage_type: str | None = None,
    brand_name: str | None = None,
) -> str:
    data = {
        "findings": findings or [],
        "beverage_type": beverage_type,
        "brand_name": brand_name,
    }
    if gov_warning_bold is not None:
        data["gov_warning_bold"] = gov_warning_bold
    return json.dumps(data)


class TestComplianceEngine:
    @pytest.mark.asyncio
    async def test_always_calls_llm_for_bold_check(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        # LLM SHOULD be called (for bold check)
        mock_llm.analyze_compliance.assert_called_once()
        assert report.overall_verdict == "pass"

    @pytest.mark.asyncio
    async def test_bold_check_prompt_when_all_regex_pass(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        engine = ComplianceEngine(mock_llm)
        await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        prompt = mock_llm.analyze_compliance.call_args[0][1]
        assert "bold" in prompt.lower()
        # Should NOT have focused rule checks
        assert "GOV_WARNING_PRESENCE" not in prompt
        assert "CLASS_TYPE" not in prompt

    @pytest.mark.asyncio
    async def test_bold_true_appends_pass_finding(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        bold_finding = next(
            (f for f in report.findings if f.rule_id == "GOV_WARNING_BOLD"), None,
        )
        assert bold_finding is not None
        assert bold_finding.severity == Severity.PASS

    @pytest.mark.asyncio
    async def test_bold_false_appends_warning_finding(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=False,
        )

        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        bold_finding = next(
            (f for f in report.findings if f.rule_id == "GOV_WARNING_BOLD"), None,
        )
        assert bold_finding is not None
        assert bold_finding.severity == Severity.WARNING
        assert report.overall_verdict == "warnings"

    @pytest.mark.asyncio
    async def test_no_bold_finding_when_not_in_response(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response()

        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        bold_finding = next(
            (f for f in report.findings if f.rule_id == "GOV_WARNING_BOLD"), None,
        )
        assert bold_finding is None

    @pytest.mark.asyncio
    async def test_calls_llm_on_regex_failure(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            findings=[{
                "rule_id": "CLASS_TYPE",
                "rule_name": "Class/Type Designation",
                "severity": "pass",
                "message": "LLM found: Artisanal Spirit",
                "extracted_value": "Artisanal Spirit",
                "regulation_reference": "27 CFR 5.63(a)(2)",
            }],
            gov_warning_bold=True,
            beverage_type="Distilled Spirits",
            brand_name="OLD TOM DISTILLERY",
        )

        # Missing a recognizable class/type for regex
        text = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.

OLD TOM DISTILLERY
Artisanal Spirit crafted in small batches
45% Alc./Vol. (90 Proof)
750 mL
Distilled by Old Tom Distillery, Louisville, KY
Product of USA"""

        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(text)

        # LLM should have been called
        mock_llm.analyze_compliance.assert_called_once()
        prompt = mock_llm.analyze_compliance.call_args[0][1]
        assert "CLASS_TYPE" in prompt

        # The LLM result should replace the failed regex finding
        class_type_finding = next(
            f for f in report.findings if f.rule_id == "CLASS_TYPE"
        )
        assert class_type_finding.severity == Severity.PASS
        assert "LLM found" in class_type_finding.message

    @pytest.mark.asyncio
    async def test_llm_gets_gov_warning_warnings(self):
        """Gov warning format/completeness WARNINGs should trigger LLM verification."""
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        # Lowercase header triggers GOV_WARNING_FORMAT warning
        text = """Government Warning: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.

OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Distilled by Old Tom Distillery, Louisville, KY
Product of USA"""

        engine = ComplianceEngine(mock_llm)
        await engine.analyze(text)

        prompt = mock_llm.analyze_compliance.call_args[0][1]
        assert "GOV_WARNING_FORMAT" in prompt

    @pytest.mark.asyncio
    async def test_image_path_threaded_to_llm(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        engine = ComplianceEngine(mock_llm)
        await engine.analyze(
            COMPLETE_LABEL_WITH_WARNING, image_path="/tmp/label.jpg",
        )

        _, kwargs = mock_llm.analyze_compliance.call_args
        assert kwargs["image_path"] == "/tmp/label.jpg"

    @pytest.mark.asyncio
    async def test_includes_application_matching(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        app_details = {"brand_name": "OLD TOM DISTILLERY"}
        engine = ComplianceEngine(mock_llm)
        report, _ = await engine.analyze(
            COMPLETE_LABEL_WITH_WARNING, application_details=app_details,
        )

        rule_ids = [f.rule_id for f in report.findings]
        assert "BRAND_MATCH" in rule_ids

    @pytest.mark.asyncio
    async def test_focused_prompt_only_includes_failed_rules(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        # Missing class type AND name/address
        text = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.

OLD TOM DISTILLERY
Artisanal Spirit 2024
45% Alc./Vol. (90 Proof)
750 mL"""

        engine = ComplianceEngine(mock_llm)
        await engine.analyze(text)

        prompt = mock_llm.analyze_compliance.call_args[0][1]
        assert "CLASS_TYPE" in prompt
        assert "NAME_ADDRESS" in prompt
        # Rules that passed should NOT be in the focused prompt
        assert "GOV_WARNING_PRESENCE" not in prompt
        assert "ALCOHOL_CONTENT" not in prompt
        assert "NET_CONTENTS" not in prompt

    @pytest.mark.asyncio
    async def test_returns_duration_ms(self):
        mock_llm = AsyncMock()
        mock_llm.analyze_compliance.return_value = _make_llm_response(
            gov_warning_bold=True,
        )

        engine = ComplianceEngine(mock_llm)
        _, duration_ms = await engine.analyze(COMPLETE_LABEL_WITH_WARNING)

        assert isinstance(duration_ms, int)
        assert duration_ms >= 0
        # With mocked LLM, compliance step should complete well under 1 second
        assert duration_ms < 1000, (
            f"Compliance engine took {duration_ms}ms with mocked LLM — too slow"
        )
