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
---"""
