from datetime import datetime

from pydantic import BaseModel

from app.schemas.compliance import ApplicationDetails, ComplianceFinding


class AnalysisResponse(BaseModel):
    id: str
    label_id: str
    status: str
    extracted_text: str | None = None
    ocr_confidence: float | None = None
    ocr_duration_ms: int | None = None
    compliance_findings: list[ComplianceFinding] | None = None
    application_details: ApplicationDetails | None = None
    overall_verdict: str | None = None
    compliance_duration_ms: int | None = None
    detected_beverage_type: str | None = None
    detected_brand_name: str | None = None
    error_message: str | None = None
    total_duration_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    items: list[AnalysisResponse]
    total: int
    page: int
    page_size: int
