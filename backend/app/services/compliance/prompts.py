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

APPLICATION_MATCHING_SECTION = """
Additionally, the following application details have been submitted for this label. Compare each provided field against what you found in the label text and report whether they match:

APPLICATION DETAILS:
%s

For each provided application detail, add a matching finding with:
- rule_id: one of BRAND_MATCH, CLASS_TYPE_MATCH, ALCOHOL_MATCH, NET_CONTENTS_MATCH, NAME_ADDRESS_MATCH, ORIGIN_MATCH
- rule_name: human-readable name (e.g., "Brand Name Match")
- severity: "pass" if the label matches the application, "fail" if it doesn't match
- message: "Expected: [application value]. Found: [label value]." or "Expected: [application value]. Not found on label."
- extracted_value: the relevant text found on the label (null if not found)
- regulation_reference: null

Include these matching findings in the same "findings" array alongside the compliance findings.
"""

FIELD_LABELS = {
    "brand_name": "Brand Name",
    "class_type": "Class/Type Designation",
    "alcohol_content": "Alcohol Content",
    "net_contents": "Net Contents",
    "bottler_name_address": "Bottler Name & Address",
    "country_of_origin": "Country of Origin",
}


def build_prompt(label_text: str, application_details: dict | None = None) -> str:
    prompt = COMPLIANCE_ANALYSIS_PROMPT % label_text

    if not application_details:
        return prompt

    details_lines = [
        f"- {FIELD_LABELS.get(key, key)}: {value}"
        for key, value in application_details.items()
        if value
    ]
    if details_lines:
        details_text = "\n".join(details_lines)
        prompt += APPLICATION_MATCHING_SECTION % details_text

    return prompt
