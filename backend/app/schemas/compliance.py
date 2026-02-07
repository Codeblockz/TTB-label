import enum

from pydantic import BaseModel


class Severity(str, enum.Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    INFO = "info"


class ComplianceFinding(BaseModel):
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    extracted_value: str | None = None
    regulation_reference: str | None = None


class ApplicationDetails(BaseModel):
    brand_name: str | None = None
    class_type: str | None = None
    alcohol_content: str | None = None
    net_contents: str | None = None
    bottler_name_address: str | None = None
    country_of_origin: str | None = None


class ComplianceReport(BaseModel):
    findings: list[ComplianceFinding]
    overall_verdict: str
    beverage_type: str | None = None
    brand_name: str | None = None
