import json
import logging

from app.models.analysis import AnalysisResult
from app.schemas.analysis import AnalysisResponse
from app.schemas.compliance import ApplicationDetails, ComplianceFinding

logger = logging.getLogger(__name__)


def _parse_json(raw: str | None, parser):
    """Parse a JSON string with the given parser, returning None on failure."""
    if not raw:
        return None
    try:
        return parser(json.loads(raw))
    except Exception:
        logger.warning("Failed to parse JSON from DB: %.200s", raw)
        return None


def _enum_value(field) -> str | None:
    """Extract .value from an enum, or return the string as-is."""
    return field.value if hasattr(field, "value") else field


def to_response(analysis: AnalysisResult) -> AnalysisResponse:
    findings = _parse_json(
        analysis.compliance_findings,
        lambda data: [ComplianceFinding(**f) for f in data],
    )
    app_details = _parse_json(
        analysis.application_details,
        lambda data: ApplicationDetails(**data),
    )

    return AnalysisResponse(
        id=analysis.id,
        label_id=analysis.label_id,
        status=_enum_value(analysis.status),
        extracted_text=analysis.extracted_text,
        ocr_confidence=analysis.ocr_confidence,
        ocr_duration_ms=analysis.ocr_duration_ms,
        compliance_findings=findings,
        application_details=app_details,
        overall_verdict=_enum_value(analysis.overall_verdict),
        compliance_duration_ms=analysis.compliance_duration_ms,
        detected_beverage_type=analysis.detected_beverage_type,
        detected_brand_name=analysis.detected_brand_name,
        error_message=analysis.error_message,
        total_duration_ms=analysis.total_duration_ms,
        image_url=f"/api/analysis/{analysis.id}/image",
        created_at=analysis.created_at,
    )
