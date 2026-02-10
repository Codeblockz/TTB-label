import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.dependencies import get_db, get_pipeline
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.label import Label
from app.routers import ALLOWED_MIME_TYPES
from app.routers.converters import to_response
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse, BulkDeleteRequest, BulkDeleteResponse
from app.services.pipeline import AnalysisPipeline
from app.services.storage import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


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
    brand_name: str = Form(""),
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


@router.get("/{analysis_id}/image")
async def get_analysis_image(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.label))
        .where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis or not analysis.label:
        raise HTTPException(status_code=404, detail="Image not found")

    upload_dir = Path(settings.upload_dir).resolve()
    image_path = Path(analysis.label.stored_filepath).resolve()
    if not image_path.is_relative_to(upload_dir):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(analysis.label.stored_filepath, media_type=analysis.label.mime_type)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    analysis = await db.get(AnalysisResult, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return to_response(analysis)


async def _delete_one(analysis: AnalysisResult, db: AsyncSession) -> None:
    """Delete an analysis and its associated label + image file."""
    label = analysis.label
    if label:
        try:
            os.remove(label.stored_filepath)
        except FileNotFoundError:
            pass

    await db.delete(analysis)
    if label:
        await db.delete(label)


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.label))
        .where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await _delete_one(analysis, db)
    await db.commit()

    return Response(status_code=204)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_analyses(
    body: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    deleted = 0
    for analysis_id in body.ids:
        result = await db.execute(
            select(AnalysisResult)
            .options(selectinload(AnalysisResult.label))
            .where(AnalysisResult.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            await _delete_one(analysis, db)
            deleted += 1
    await db.commit()
    return BulkDeleteResponse(deleted=deleted)


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
        items=[to_response(a) for a in analyses],
        total=total,
        page=page,
        page_size=page_size,
    )
