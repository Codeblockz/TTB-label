import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_pipeline
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.label import Label
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.schemas.compliance import ComplianceFinding
from app.services.pipeline import AnalysisPipeline
from app.services.storage import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}


def _to_response(analysis: AnalysisResult) -> AnalysisResponse:
    findings = None
    if analysis.compliance_findings:
        try:
            raw = json.loads(analysis.compliance_findings)
            findings = [ComplianceFinding(**f) for f in raw]
        except (json.JSONDecodeError, Exception):
            findings = None

    return AnalysisResponse(
        id=analysis.id,
        label_id=analysis.label_id,
        status=analysis.status.value if hasattr(analysis.status, "value") else analysis.status,
        extracted_text=analysis.extracted_text,
        ocr_confidence=analysis.ocr_confidence,
        ocr_duration_ms=analysis.ocr_duration_ms,
        compliance_findings=findings,
        overall_verdict=analysis.overall_verdict.value if hasattr(analysis.overall_verdict, "value") else analysis.overall_verdict,
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
) -> None:
    from app.dependencies import session_factory

    async with session_factory() as db:
        await pipeline.run(analysis_id, label_id, image_path, db)


@router.post("/single")
async def analyze_single(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    stored_path, file_size = await save_upload(file)

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
    )
    db.add(analysis)
    await db.commit()

    pipeline = get_pipeline()
    background_tasks.add_task(_run_pipeline, analysis.id, label.id, stored_path, pipeline)

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
