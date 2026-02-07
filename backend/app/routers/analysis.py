import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_pipeline
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.label import Label
from app.routers import ALLOWED_MIME_TYPES
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.schemas.compliance import ApplicationDetails, ComplianceFinding
from app.services.pipeline import AnalysisPipeline
from app.services.storage import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _parse_json(raw: str | None, parser):
    """Parse a JSON string with the given parser, returning None on failure."""
    if not raw:
        return None
    try:
        return parser(json.loads(raw))
    except Exception:
        return None


def _enum_value(field) -> str | None:
    """Extract .value from an enum, or return the string as-is."""
    return field.value if hasattr(field, "value") else field


def _to_response(analysis: AnalysisResult) -> AnalysisResponse:
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
        created_at=analysis.created_at,
    )


async def _run_pipeline(
    analysis_id: str,
    label_id: str,
    image_path: str,
    pipeline: AnalysisPipeline,
    application_details: dict | None = None,
) -> None:
    from app.dependencies import session_factory

    async with session_factory() as db:
        await pipeline.run(analysis_id, label_id, image_path, db, application_details)


@router.post("/single")
async def analyze_single(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    brand_name: str = Form(...),
    class_type: str | None = Form(None),
    alcohol_content: str | None = Form(None),
    net_contents: str | None = Form(None),
    bottler_name_address: str | None = Form(None),
    country_of_origin: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    stored_path, file_size = await save_upload(file)

    app_details = {
        key: value
        for key, value in {
            "brand_name": brand_name,
            "class_type": class_type,
            "alcohol_content": alcohol_content,
            "net_contents": net_contents,
            "bottler_name_address": bottler_name_address,
            "country_of_origin": country_of_origin,
        }.items()
        if value is not None
    }

    label = Label(
        original_filename=file.filename or "unknown",
        stored_filepath=stored_path,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(label)
    await db.flush()

    analysis = AnalysisResult(
        label_id=label.id,
        status=AnalysisStatus.PENDING,
        application_details=json.dumps(app_details),
    )
    db.add(analysis)
    await db.commit()

    pipeline = get_pipeline()
    background_tasks.add_task(_run_pipeline, analysis.id, label.id, stored_path, pipeline, app_details)

    return {"analysis_id": analysis.id}


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    analysis = await db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_response(analysis)


@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    verdict: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(AnalysisResult).order_by(AnalysisResult.created_at.desc())

    if verdict:
        query = query.where(AnalysisResult.overall_verdict == verdict)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    analyses = result.scalars().all()

    return AnalysisListResponse(
        items=[_to_response(a) for a in analyses],
        total=total,
        page=page,
        page_size=page_size,
    )
