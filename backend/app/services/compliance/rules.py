import re

from app.schemas.compliance import ComplianceFinding, Severity

GOV_WARNING_HEADER_PATTERN = re.compile(r"GOVERNMENT\s+WARNING\s*:", re.IGNORECASE)

GOV_WARNING_KEY_PHRASES = [
    r"SURGEON\s+GENERAL",
    r"WOMEN\s+SHOULD\s+NOT\s+DRINK",
    r"ALCOHOLIC\s+BEVERAGES",
    r"DURING\s+PREGNANCY",
    r"RISK\s+OF\s+BIRTH\s+DEFECTS",
    r"CONSUMPTION\s+OF\s+ALCOHOLIC\s+BEVERAGES",
    r"IMPAIRS\s+YOUR\s+ABILITY",
    r"DRIVE\s+A\s+CAR\s+OR\s+OPERATE\s+MACHINERY",
]

ALCOHOL_CONTENT_PATTERN = re.compile(
    r"(\d+\.?\d*)\s*%\s*(Alc\.?/?\s*Vol\.?|ABV)"
    r"|(\d+)\s*Proof",
    re.IGNORECASE,
)

NET_CONTENTS_PATTERN = re.compile(
    r"(\d+\.?\d*)\s*(mL|ml|FL\.?\s*OZ\.?|Liter|Litre|L|cl|oz)",
    re.IGNORECASE,
)


def check_government_warning(text: str) -> ComplianceFinding:
    header_match = GOV_WARNING_HEADER_PATTERN.search(text)
    if not header_match:
        return ComplianceFinding(
            rule_id="GOV_WARNING",
            rule_name="Government Warning Statement",
            severity=Severity.FAIL,
            message="Government warning statement not found on label",
            regulation_reference="27 CFR 16.21",
        )

    matched_phrases = 0
    for phrase_pattern in GOV_WARNING_KEY_PHRASES:
        if re.search(phrase_pattern, text, re.IGNORECASE):
            matched_phrases += 1

    if matched_phrases >= 6:
        return ComplianceFinding(
            rule_id="GOV_WARNING",
            rule_name="Government Warning Statement",
            severity=Severity.PASS,
            message=f"Government warning found with {matched_phrases}/8 key phrases matched",
            extracted_value=header_match.group(0),
            regulation_reference="27 CFR 16.21",
        )

    return ComplianceFinding(
        rule_id="GOV_WARNING",
        rule_name="Government Warning Statement",
        severity=Severity.WARNING,
        message=f"Government warning header found but only {matched_phrases}/8 key phrases matched — may be incomplete",
        extracted_value=header_match.group(0),
        regulation_reference="27 CFR 16.21",
    )


def check_alcohol_content(text: str) -> ComplianceFinding:
    match = ALCOHOL_CONTENT_PATTERN.search(text)
    if not match:
        return ComplianceFinding(
            rule_id="ALCOHOL_CONTENT",
            rule_name="Alcohol Content",
            severity=Severity.FAIL,
            message="Alcohol content not found on label",
            regulation_reference="27 CFR 5.63(a)(3)",
        )

    return ComplianceFinding(
        rule_id="ALCOHOL_CONTENT",
        rule_name="Alcohol Content",
        severity=Severity.PASS,
        message="Alcohol content is displayed on the label",
        extracted_value=match.group(0),
        regulation_reference="27 CFR 5.63(a)(3)",
    )


def check_net_contents(text: str) -> ComplianceFinding:
    match = NET_CONTENTS_PATTERN.search(text)
    if not match:
        return ComplianceFinding(
            rule_id="NET_CONTENTS",
            rule_name="Net Contents",
            severity=Severity.FAIL,
            message="Net contents not found on label",
            regulation_reference="27 CFR 5.63(a)(4)",
        )

    return ComplianceFinding(
        rule_id="NET_CONTENTS",
        rule_name="Net Contents",
        severity=Severity.PASS,
        message="Net contents are displayed on the label",
        extracted_value=match.group(0),
        regulation_reference="27 CFR 5.63(a)(4)",
    )


ALL_REGEX_RULES = [
    check_government_warning,
    check_alcohol_content,
    check_net_contents,
]


def run_regex_rules(text: str) -> list[ComplianceFinding]:
    return [rule(text) for rule in ALL_REGEX_RULES]
