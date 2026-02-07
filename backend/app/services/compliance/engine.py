import json
import logging
import time

from app.schemas.compliance import ComplianceFinding, ComplianceReport, Severity
from app.services.compliance.prompts import build_prompt
from app.services.compliance.rules import run_regex_rules
from app.services.llm.base import LLMServiceProtocol

logger = logging.getLogger(__name__)

REGEX_RULE_IDS = {"GOV_WARNING", "ALCOHOL_CONTENT", "NET_CONTENTS"}


def _determine_verdict(findings: list[ComplianceFinding]) -> str:
    severities = {f.severity for f in findings}
    if Severity.FAIL in severities:
        return "fail"
    if Severity.WARNING in severities:
        return "warnings"
    return "pass"


def _parse_llm_findings(raw_json: str) -> tuple[list[ComplianceFinding], str | None, str | None]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON, skipping LLM findings")
        return [], None, None

    findings = []
    for item in data.get("findings", []):
        try:
            findings.append(ComplianceFinding(**item))
        except Exception:
            logger.warning("Skipping malformed LLM finding: %s", item)

    return findings, data.get("beverage_type"), data.get("brand_name")


class ComplianceEngine:
    def __init__(self, llm_service: LLMServiceProtocol) -> None:
        self._llm = llm_service

    async def analyze(self, text: str, application_details: dict | None = None) -> tuple[ComplianceReport, int]:
        start = time.perf_counter()

        regex_findings = run_regex_rules(text)

        prompt = build_prompt(text, application_details)
        raw_response = await self._llm.analyze_compliance(text, prompt)
        llm_findings, beverage_type, brand_name = _parse_llm_findings(raw_response)

        # Merge: regex takes precedence for rules it covers
        merged = list(regex_findings)
        for finding in llm_findings:
            if finding.rule_id not in REGEX_RULE_IDS:
                merged.append(finding)

        verdict = _determine_verdict(merged)
        duration_ms = int((time.perf_counter() - start) * 1000)

        report = ComplianceReport(
            findings=merged,
            overall_verdict=verdict,
            beverage_type=beverage_type,
            brand_name=brand_name,
        )
        return report, duration_ms
