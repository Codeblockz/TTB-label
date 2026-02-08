COMPLIANCE_ANALYSIS_PROMPT = """You are an expert TTB (Alcohol and Tobacco Tax and Trade Bureau) compliance analyst. Analyze the following alcohol beverage label text and check for these mandatory elements:

1. **Brand Name** — Is a brand name clearly identifiable?
2. **Class/Type Designation** — Is the beverage class/type specified (e.g., "Kentucky Straight Bourbon Whiskey", "Cabernet Sauvignon", "India Pale Ale")?
3. **Name and Address** — Is the name and address of the bottler, producer, or importer present?
4. **Country of Origin** — For imported products, is the country of origin stated? For domestic products, note "not required" or note if "Product of USA" or similar is present.
5. **Government Warning Format** — Does the "GOVERNMENT WARNING:" header appear in all capital letters?
6. **Government Warning Completeness** — Are both required clauses present? (1) pregnancy risk and (2) impaired ability to drive/operate machinery.

For each check, return a JSON object with these fields:
- rule_id: one of BRAND_NAME, CLASS_TYPE, NAME_ADDRESS, COUNTRY_ORIGIN, GOV_WARNING_FORMAT, GOV_WARNING_COMPLETE
- rule_name: human-readable name
- severity: "pass", "warning", "fail", or "info"
- message: brief explanation of what was found or missing
- extracted_value: the relevant text extracted from the label (null if not found)
- regulation_reference: the applicable CFR reference

Also include:
- beverage_type: the detected beverage type (e.g., "Distilled Spirits", "Wine", "Malt Beverage")
- brand_name: the detected brand name

Return ONLY valid JSON in this format:
{
  "findings": [...],
  "beverage_type": "...",
  "brand_name": "..."
}

LABEL TEXT:
---
%s
---
"""

FOCUSED_RULE_DESCRIPTIONS = {
    "BRAND_NAME": "Is a brand name clearly identifiable on this label?",
    "CLASS_TYPE": "Is a beverage class/type specified (e.g., vodka, whiskey, wine, beer)?",
    "NAME_ADDRESS": "Is the name and address of the bottler, producer, or importer present?",
    "COUNTRY_ORIGIN": "For imported products, is the country of origin stated?",
    "GOV_WARNING_PRESENCE": "Is any form of a government warning statement present on this label?",
    "GOV_WARNING_FORMAT": "Is 'GOVERNMENT WARNING:' in ALL CAPITAL LETTERS as required by 27 CFR 16.21?",
    "GOV_WARNING_COMPLETE": (
        "Are BOTH required clauses of the government warning present? "
        "(1) Pregnancy risk from the Surgeon General, and "
        "(2) Impaired ability to drive/operate machinery and health problems."
    ),
    "ALCOHOL_CONTENT": "Is the alcohol content (ABV or proof) displayed?",
    "NET_CONTENTS": "Are the net contents (volume) displayed?",
}

FOCUSED_PROMPT_TEMPLATE = """You are an expert TTB compliance analyst. A regex-based scan of this alcohol label could not confirm the following specific items. Please check ONLY these items:

%s

For each item, return a JSON finding with:
- rule_id: the rule ID shown above
- rule_name: human-readable name
- severity: "pass", "warning", "fail", or "info"
- message: brief explanation of what was found or missing
- extracted_value: the relevant text from the label (null if not found)
- regulation_reference: the applicable CFR reference

Also check the label image: Is "GOVERNMENT WARNING:" displayed in BOLD TYPE as required by 27 CFR 16.21?
Bold means the "GOVERNMENT WARNING:" header text has noticeably heavier/thicker strokes compared to the surrounding warning body text. Compare the weight of the header against the rest of the warning statement — if the header is visually heavier and stands out from the body text, it is bold. Return true if the header is bolder than the body text, false only if they appear the same weight.
Include "gov_warning_bold": true or false in your JSON response.

Also include:
- beverage_type: the detected beverage type (e.g., "Distilled Spirits", "Wine", "Malt Beverage")
- brand_name: the detected brand name

Return ONLY valid JSON in this format:
{
  "findings": [...],
  "gov_warning_bold": true or false,
  "beverage_type": "...",
  "brand_name": "..."
}

LABEL TEXT:
---
%s
---
"""

BOLD_CHECK_PROMPT = """You are an expert TTB compliance analyst. All text-based compliance checks passed for this alcohol label. Check the label image for one remaining item:

Is the "GOVERNMENT WARNING:" header displayed in BOLD TYPE as required by 27 CFR 16.21?
Bold means the "GOVERNMENT WARNING:" header text has noticeably heavier/thicker strokes compared to the surrounding warning body text. Compare the visual weight of the header against the rest of the warning statement. If the header appears visually heavier and stands out from the body text, it IS bold — return true. Only return false if the header and body text appear to be the same weight/thickness.

Also include:
- beverage_type: the detected beverage type (e.g., "Distilled Spirits", "Wine", "Malt Beverage")
- brand_name: the detected brand name

Return ONLY valid JSON:
{
  "gov_warning_bold": true or false,
  "beverage_type": "...",
  "brand_name": "..."
}

LABEL TEXT:
---
%s
---
"""


def build_focused_prompt(label_text: str, failed_rule_ids: list[str]) -> str:
    checks = []
    for rule_id in failed_rule_ids:
        description = FOCUSED_RULE_DESCRIPTIONS.get(rule_id, rule_id)
        checks.append(f"- {rule_id}: {description}")

    checks_text = "\n".join(checks)
    return FOCUSED_PROMPT_TEMPLATE % (checks_text, label_text)


def build_bold_check_prompt(label_text: str) -> str:
    return BOLD_CHECK_PROMPT % label_text
