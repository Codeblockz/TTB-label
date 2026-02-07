import asyncio
import json
import random


MOCK_LLM_RESPONSE = {
    "findings": [
        {
            "rule_id": "BRAND_NAME",
            "rule_name": "Brand Name",
            "severity": "pass",
            "message": "Brand name 'OLD TOM DISTILLERY' is clearly displayed",
            "extracted_value": "OLD TOM DISTILLERY",
            "regulation_reference": "27 CFR 5.63"
        },
        {
            "rule_id": "CLASS_TYPE",
            "rule_name": "Class/Type Designation",
            "severity": "pass",
            "message": "Class/type 'Kentucky Straight Bourbon Whiskey' is properly identified",
            "extracted_value": "Kentucky Straight Bourbon Whiskey",
            "regulation_reference": "27 CFR 5.66"
        },
        {
            "rule_id": "NAME_ADDRESS",
            "rule_name": "Name and Address",
            "severity": "pass",
            "message": "Bottler name and address found: 'Old Tom Distillery, Louisville, Kentucky'",
            "extracted_value": "Old Tom Distillery, Louisville, Kentucky",
            "regulation_reference": "27 CFR 5.66(a)"
        },
        {
            "rule_id": "COUNTRY_ORIGIN",
            "rule_name": "Country of Origin",
            "severity": "info",
            "message": "Domestic product — 'Product of USA' indicated. Country of origin not required for domestic products.",
            "extracted_value": "Product of USA",
            "regulation_reference": "27 CFR 5.63(a)(5)"
        },
        {
            "rule_id": "GOV_WARNING_FORMAT",
            "rule_name": "Government Warning Format",
            "severity": "pass",
            "message": "GOVERNMENT WARNING header appears in all capital letters as required",
            "extracted_value": "GOVERNMENT WARNING:",
            "regulation_reference": "27 CFR 16.21"
        },
        {
            "rule_id": "GOV_WARNING_COMPLETE",
            "rule_name": "Government Warning Completeness",
            "severity": "pass",
            "message": "Both required warning clauses are present: pregnancy risk and impaired ability",
            "extracted_value": None,
            "regulation_reference": "27 CFR 16.21"
        }
    ],
    "beverage_type": "Distilled Spirits",
    "brand_name": "OLD TOM DISTILLERY"
}


MOCK_MATCHING_FINDINGS = [
    {
        "rule_id": "BRAND_MATCH",
        "rule_name": "Brand Name Match",
        "severity": "pass",
        "message": "Expected: OLD TOM DISTILLERY. Found: OLD TOM DISTILLERY.",
        "extracted_value": "OLD TOM DISTILLERY",
        "regulation_reference": None
    },
    {
        "rule_id": "CLASS_TYPE_MATCH",
        "rule_name": "Class/Type Match",
        "severity": "pass",
        "message": "Expected: Kentucky Straight Bourbon Whiskey. Found: Kentucky Straight Bourbon Whiskey.",
        "extracted_value": "Kentucky Straight Bourbon Whiskey",
        "regulation_reference": None
    },
    {
        "rule_id": "ALCOHOL_MATCH",
        "rule_name": "Alcohol Content Match",
        "severity": "pass",
        "message": "Expected: 45% Alc./Vol.. Found: 45% Alc./Vol..",
        "extracted_value": "45% Alc./Vol.",
        "regulation_reference": None
    },
    {
        "rule_id": "NET_CONTENTS_MATCH",
        "rule_name": "Net Contents Match",
        "severity": "pass",
        "message": "Expected: 750 mL. Found: 750 mL.",
        "extracted_value": "750 mL",
        "regulation_reference": None
    },
    {
        "rule_id": "NAME_ADDRESS_MATCH",
        "rule_name": "Name & Address Match",
        "severity": "pass",
        "message": "Expected: Old Tom Distillery, Louisville, Kentucky. Found: Old Tom Distillery, Louisville, Kentucky.",
        "extracted_value": "Old Tom Distillery, Louisville, Kentucky",
        "regulation_reference": None
    },
    {
        "rule_id": "ORIGIN_MATCH",
        "rule_name": "Country of Origin Match",
        "severity": "pass",
        "message": "Expected: USA. Found: Product of USA.",
        "extracted_value": "Product of USA",
        "regulation_reference": None
    },
]


class MockLLMService:
    async def analyze_compliance(self, text: str, prompt: str) -> str:
        await asyncio.sleep(random.uniform(0.8, 1.2))
        response = dict(MOCK_LLM_RESPONSE)
        if "APPLICATION DETAILS:" in prompt:
            response = {
                **MOCK_LLM_RESPONSE,
                "findings": MOCK_LLM_RESPONSE["findings"] + MOCK_MATCHING_FINDINGS,
            }
        return json.dumps(response)
