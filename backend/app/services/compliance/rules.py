import re

from app.schemas.compliance import ComplianceFinding, Severity

GOV_WARNING_HEADER_CAPS = re.compile(r"GOVERNMENT\s+WARNING\s*:")
GOV_WARNING_HEADER_ANY = re.compile(r"GOVERNMENT\s+WARNING\s*:", re.IGNORECASE)

CLASS_TYPE_PATTERN = re.compile(
    r"\b("
    r"vodka|whiskey|whisky|bourbon|gin|rum|tequila|mezcal|brandy|cognac"
    r"|scotch|absinthe|schnapps|liqueur|liquor|cordial|aperitif"
    r"|wine|champagne|prosecco|port|sherry|vermouth|sangria|rosé|rose"
    r"|cabernet|chardonnay|merlot|pinot|sauvignon|riesling|zinfandel"
    r"|malbec|syrah|shiraz|tempranillo|moscato|grenache|viognier"
    r"|beer|ale|lager|stout|porter|pilsner|pilsener|ipa|india pale ale"
    r"|malt\s+beverage|hard\s+seltzer|hard\s+cider|cider|sake|soju|mead"
    r")\b",
    re.IGNORECASE,
)

NAME_ADDRESS_PATTERN = re.compile(
    r"(Distilled|Bottled|Produced|Imported|Manufactured|Blended|Made|Packed)"
    r"\s+(by|for|&\s*bottled\s+by)\s+"
    r".+?"
    r",?\s*[A-Z][a-zA-Z\s]+,?\s*[A-Z]{2}",
    re.IGNORECASE,
)

COUNTRY_OF_ORIGIN_PATTERN = re.compile(
    r"(Product\s+of|Imported\s+from|Made\s+in|Produced\s+in|Producto\s+de)\s+[A-Z][a-zA-Z\s]+",
    re.IGNORECASE,
)

GOV_WARNING_CLAUSE_1_PHRASES = [
    r"SURGEON\s+GENERAL",
    r"WOMEN\s+SHOULD\s+NOT\s+DRINK",
    r"DURING\s+PREGNANCY",
    r"RISK\s+OF\s+BIRTH\s+DEFECTS",
]

GOV_WARNING_CLAUSE_2_PHRASES = [
    r"CONSUMPTION\s+OF\s+ALCOHOLIC\s+BEVERAGES",
    r"IMPAIRS\s+YOUR\s+ABILITY",
    r"DRIVE\s+A\s+CAR\s+OR\s+OPERATE\s+MACHINERY",
    r"CAUSE\s+HEALTH\s+PROBLEMS",
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


def _count_clause_matches(text: str, phrases: list[str]) -> int:
    return sum(1 for p in phrases if re.search(p, text, re.IGNORECASE))


def check_gov_warning_presence(text: str) -> ComplianceFinding:
    match = GOV_WARNING_HEADER_ANY.search(text)
    if match:
        return ComplianceFinding(
            rule_id="GOV_WARNING_PRESENCE",
            rule_name="Government Warning Presence",
            severity=Severity.PASS,
            message="Government warning statement found on label",
            extracted_value=match.group(0),
            regulation_reference="27 CFR 16.21",
        )
    return ComplianceFinding(
        rule_id="GOV_WARNING_PRESENCE",
        rule_name="Government Warning Presence",
        severity=Severity.FAIL,
        message="Government warning statement not found on label",
        regulation_reference="27 CFR 16.21",
    )


def check_gov_warning_format(text: str) -> ComplianceFinding:
    if GOV_WARNING_HEADER_CAPS.search(text):
        return ComplianceFinding(
            rule_id="GOV_WARNING_FORMAT",
            rule_name="Government Warning Format",
            severity=Severity.PASS,
            message="'GOVERNMENT WARNING:' is in required ALL CAPS format",
            regulation_reference="27 CFR 16.21",
        )
    if GOV_WARNING_HEADER_ANY.search(text):
        return ComplianceFinding(
            rule_id="GOV_WARNING_FORMAT",
            rule_name="Government Warning Format",
            severity=Severity.WARNING,
            message="'GOVERNMENT WARNING:' is not in required ALL CAPITAL LETTERS",
            regulation_reference="27 CFR 16.21",
        )
    return ComplianceFinding(
        rule_id="GOV_WARNING_FORMAT",
        rule_name="Government Warning Format",
        severity=Severity.INFO,
        message="No government warning header found to check format",
        regulation_reference="27 CFR 16.21",
    )


CLAUSE_MATCH_THRESHOLD = 2


def check_gov_warning_complete(text: str) -> ComplianceFinding:
    if not GOV_WARNING_HEADER_ANY.search(text):
        return ComplianceFinding(
            rule_id="GOV_WARNING_COMPLETE",
            rule_name="Government Warning Completeness",
            severity=Severity.INFO,
            message="No government warning header found to check completeness",
            regulation_reference="27 CFR 16.21",
        )

    c1 = _count_clause_matches(text, GOV_WARNING_CLAUSE_1_PHRASES)
    c2 = _count_clause_matches(text, GOV_WARNING_CLAUSE_2_PHRASES)

    if c1 >= CLAUSE_MATCH_THRESHOLD and c2 >= CLAUSE_MATCH_THRESHOLD:
        return ComplianceFinding(
            rule_id="GOV_WARNING_COMPLETE",
            rule_name="Government Warning Completeness",
            severity=Severity.PASS,
            message=f"Both warning clauses present (pregnancy: {c1}/4, impairment: {c2}/4)",
            regulation_reference="27 CFR 16.21",
        )

    return ComplianceFinding(
        rule_id="GOV_WARNING_COMPLETE",
        rule_name="Government Warning Completeness",
        severity=Severity.WARNING,
        message=f"Government warning incomplete (pregnancy: {c1}/4, impairment: {c2}/4)",
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


MIN_LABEL_TEXT_LENGTH = 20


def check_brand_name(text: str) -> ComplianceFinding:
    if len(text.strip()) >= MIN_LABEL_TEXT_LENGTH:
        return ComplianceFinding(
            rule_id="BRAND_NAME",
            rule_name="Brand Name",
            severity=Severity.PASS,
            message="Label contains sufficient text for brand identification",
            regulation_reference="27 CFR 5.63(a)(1)",
        )

    return ComplianceFinding(
        rule_id="BRAND_NAME",
        rule_name="Brand Name",
        severity=Severity.FAIL,
        message="Label text too short to identify a brand name",
        regulation_reference="27 CFR 5.63(a)(1)",
    )


def check_class_type(text: str) -> ComplianceFinding:
    match = CLASS_TYPE_PATTERN.search(text)
    if not match:
        return ComplianceFinding(
            rule_id="CLASS_TYPE",
            rule_name="Class/Type Designation",
            severity=Severity.FAIL,
            message="No beverage class/type designation found on label",
            regulation_reference="27 CFR 5.63(a)(2)",
        )

    return ComplianceFinding(
        rule_id="CLASS_TYPE",
        rule_name="Class/Type Designation",
        severity=Severity.PASS,
        message="Beverage class/type designation found on label",
        extracted_value=match.group(0),
        regulation_reference="27 CFR 5.63(a)(2)",
    )


def check_name_address(text: str) -> ComplianceFinding:
    match = NAME_ADDRESS_PATTERN.search(text)
    if not match:
        return ComplianceFinding(
            rule_id="NAME_ADDRESS",
            rule_name="Name and Address",
            severity=Severity.FAIL,
            message="Bottler/producer/importer name and address not found on label",
            regulation_reference="27 CFR 5.63(a)(5)",
        )

    return ComplianceFinding(
        rule_id="NAME_ADDRESS",
        rule_name="Name and Address",
        severity=Severity.PASS,
        message="Name and address of responsible party found on label",
        extracted_value=match.group(0),
        regulation_reference="27 CFR 5.63(a)(5)",
    )


def check_country_of_origin(text: str) -> ComplianceFinding:
    match = COUNTRY_OF_ORIGIN_PATTERN.search(text)
    if not match:
        return ComplianceFinding(
            rule_id="COUNTRY_ORIGIN",
            rule_name="Country of Origin",
            severity=Severity.INFO,
            message="No country of origin statement found — not required for domestic products",
            regulation_reference="27 CFR 5.63(a)(6)",
        )

    return ComplianceFinding(
        rule_id="COUNTRY_ORIGIN",
        rule_name="Country of Origin",
        severity=Severity.PASS,
        message="Country of origin statement found on label",
        extracted_value=match.group(0),
        regulation_reference="27 CFR 5.63(a)(6)",
    )


ALL_REGEX_RULES = [
    check_gov_warning_presence,
    check_gov_warning_format,
    check_gov_warning_complete,
    check_alcohol_content,
    check_net_contents,
    check_brand_name,
    check_class_type,
    check_name_address,
    check_country_of_origin,
]


def run_regex_rules(text: str) -> list[ComplianceFinding]:
    return [rule(text) for rule in ALL_REGEX_RULES]


def _word_set(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z0-9]+", text)}


WORD_MATCH_THRESHOLD = 0.7

APPLICATION_MATCH_FIELDS = {
    "brand_name": ("BRAND_MATCH", "Brand Name Match"),
    "class_type": ("CLASS_TYPE_MATCH", "Class/Type Match"),
    "alcohol_content": ("ALCOHOL_MATCH", "Alcohol Content Match"),
    "net_contents": ("NET_CONTENTS_MATCH", "Net Contents Match"),
    "bottler_name_address": ("NAME_ADDRESS_MATCH", "Name & Address Match"),
    "country_of_origin": ("ORIGIN_MATCH", "Country of Origin Match"),
}


def run_application_matching(
    label_text: str, application_details: dict,
) -> list[ComplianceFinding]:
    findings: list[ComplianceFinding] = []
    label_lower = label_text.lower()
    label_words = _word_set(label_text)

    for field_key, (rule_id, rule_name) in APPLICATION_MATCH_FIELDS.items():
        expected = application_details.get(field_key)
        if not expected:
            continue

        # Exact substring match (case-insensitive)
        if expected.lower() in label_lower:
            findings.append(ComplianceFinding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=Severity.PASS,
                message=f"Label contains expected value: {expected}",
                extracted_value=expected,
            ))
            continue

        # Fuzzy word-level match for OCR tolerance
        expected_words = _word_set(expected)
        if not expected_words:
            continue

        matched_words = expected_words & label_words
        match_ratio = len(matched_words) / len(expected_words)

        if match_ratio >= WORD_MATCH_THRESHOLD:
            findings.append(ComplianceFinding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=Severity.PASS,
                message=f"Label approximately matches expected value: {expected} "
                        f"({len(matched_words)}/{len(expected_words)} words found)",
                extracted_value=", ".join(sorted(matched_words)),
            ))
        else:
            findings.append(ComplianceFinding(
                rule_id=rule_id,
                rule_name=rule_name,
                severity=Severity.FAIL,
                message=f"Expected: {expected}. Not found on label.",
            ))

    return findings
