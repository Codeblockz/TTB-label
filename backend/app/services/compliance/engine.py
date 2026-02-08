import json
import logging
import time

from app.schemas.compliance import ComplianceFinding, ComplianceReport, Severity
from app.services.compliance.prompts import build_bold_check_prompt, build_focused_prompt
from app.services.compliance.rules import (
    run_application_matching,
    run_regex_rules,
)
from app.services.llm.base import LLMServiceProtocol

GOV_WARNING_RULE_IDS = {"GOV_WARNING_FORMAT", "GOV_WARNING_COMPLETE"}

logger = logging.getLogger(__name__)


def _determine_verdict(findings: list[ComplianceFinding]) -> str:
    severities = {f.severity for f in findings}
    if Severity.FAIL in severities:
        return "fail"
    if Severity.WARNING in severities:
        return "warnings"
    return "pass"


class _LLMResult:
    """Parsed LLM response with findings and metadata."""

    def __init__(self, raw_json: str) -> None:
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON, skipping LLM findings")
            data = {}

        self.findings: list[ComplianceFinding] = []
        for item in data.get("findings", []):
            try:
                self.findings.append(ComplianceFinding(**item))
            except Exception:
                logger.warning("Skipping malformed LLM finding: %s", item)

        self.beverage_type: str | None = data.get("beverage_type")
        self.brand_name: str | None = data.get("brand_name")
        self.gov_warning_bold: bool | None = data.get("gov_warning_bold")


def _extract_beverage_type(findings: list[ComplianceFinding]) -> str | None:
    for finding in findings:
        if finding.rule_id == "CLASS_TYPE" and finding.extracted_value:
            return finding.extracted_value
    return None


def _extract_brand_name(text: str) -> str | None:
    lines = text.strip().splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) > 2:
            return stripped
    return None


class ComplianceEngine:
    def __init__(self, llm_service: LLMServiceProtocol) -> None:
        self._llm = llm_service

    async def analyze(
        self,
        text: str,
        application_details: dict | None = None,
        image_path: str | None = None,
    ) -> tuple[ComplianceReport, int]:
        start = time.perf_counter()

        # Step 1: Run all regex rules (instant)
        regex_findings = run_regex_rules(text)

        # Step 2: Run application matching if details provided (instant)
        app_findings: list[ComplianceFinding] = []
        if application_details:
            app_findings = run_application_matching(text, application_details)

        # Step 3: Collect rules that need LLM verification
        failed_rule_ids = [
            f.rule_id for f in regex_findings
            if f.severity == Severity.FAIL
        ]
        warning_gov_ids = [
            f.rule_id for f in regex_findings
            if f.severity == Severity.WARNING and f.rule_id in GOV_WARNING_RULE_IDS
        ]
        rules_for_llm = failed_rule_ids + warning_gov_ids

        # Step 4: Always call LLM (at minimum for bold check)
        if rules_for_llm:
            logger.info("Sending rules to LLM: %s", rules_for_llm)
            prompt = build_focused_prompt(text, rules_for_llm)
        else:
            logger.info("All regex rules passed — calling LLM for bold check only")
            prompt = build_bold_check_prompt(text)

        raw_response = await self._llm.analyze_compliance(
            text, prompt, image_path=image_path,
        )
        llm = _LLMResult(raw_response)

        # Replace failed/warned regex findings with LLM results where available
        if rules_for_llm:
            llm_by_rule = {f.rule_id: f for f in llm.findings}
            needs_llm = set(rules_for_llm)
            merged_findings = []
            for finding in regex_findings:
                if finding.rule_id in needs_llm and finding.rule_id in llm_by_rule:
                    merged_findings.append(llm_by_rule.pop(finding.rule_id))
                else:
                    merged_findings.append(finding)
            merged_findings.extend(llm_by_rule.values())
            regex_findings = merged_findings

        # Fall back to regex extraction if LLM didn't provide metadata
        beverage_type = llm.beverage_type or _extract_beverage_type(regex_findings)
        brand_name = llm.brand_name or _extract_brand_name(text)

        # Step 5: Append bold check finding
        if llm.gov_warning_bold is not None:
            is_bold = llm.gov_warning_bold
            regex_findings.append(ComplianceFinding(
                rule_id="GOV_WARNING_BOLD",
                rule_name="Government Warning Bold Format",
                severity=Severity.PASS if is_bold else Severity.WARNING,
                message=(
                    "'GOVERNMENT WARNING:' appears in required bold type"
                    if is_bold else
                    "'GOVERNMENT WARNING:' may not be in required bold type"
                ),
                regulation_reference="27 CFR 16.21",
            ))

        merged = regex_findings + app_findings
        verdict = _determine_verdict(merged)
        duration_ms = int((time.perf_counter() - start) * 1000)

        report = ComplianceReport(
            findings=merged,
            overall_verdict=verdict,
            beverage_type=beverage_type,
            brand_name=brand_name,
        )
        return report, duration_ms
