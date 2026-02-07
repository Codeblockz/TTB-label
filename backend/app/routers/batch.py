import asyncio
import csv
import io
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_pipeline
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.batch import BatchJob, BatchStatus
from app.models.label import Label
from app.routers import ALLOWED_MIME_TYPES
from app.schemas.batch import BatchDetailResponse, BatchResponse
from app.services.pipeline import AnalysisPipeline
from app.services.storage import save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/batch", tags=["batch"])


async def _run_batch_pipeline(batch_id: str, items: list[dict], pipeline: AnalysisPipeline) -> None:
    from app.dependencies import session_factory

    async with session_factory() as db:
        batch = await db.get(BatchJob, batch_id)
        if not batch:
            return
        batch.status = BatchStatus.PROCESSING
        await db.commit()

        for item in items:
            try:
                await pipeline.run(
                    item["analysis_id"],
                    item["label_id"],
                    item["image_path"],
                    db,
                    item.get("application_details"),
                )
                batch.completed_labels += 1
            except Exception as exc:
                logger.exception("Batch item failed: %s", exc)
                batch.failed_labels += 1
            await db.commit()

        batch.status = BatchStatus.COMPLETED
        await db.commit()


@router.post("/upload")
async def upload_batch(
    files: list[UploadFile],
    csv_file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Parse CSV for application details
    csv_content = await csv_file.read()
    csv_text = csv_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(csv_text))

    details_by_filename: dict[str, dict] = {}
    for row in reader:
        filename = row.get("filename", "").strip()
        if filename:
            details: dict[str, str] = {}
            for field in [
                "brand_name", "class_type", "alcohol_content",
                "net_contents", "bottler_name_address", "country_of_origin",
            ]:
                value = row.get(field, "").strip()
                if value:
                    details[field] = value
            details_by_filename[filename.lower()] = details

    batch = BatchJob(total_labels=len(files))
    db.add(batch)
    await db.flush()

    items = []
    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            continue

        stored_path, file_size = await save_upload(file)

        # Match filename to CSV row (case-insensitive)
        filename = file.filename or "unknown"
        app_details = details_by_filename.get(filename.lower())

        label = Label(
            original_filename=filename,
            stored_filepath=stored_path,
            file_size_bytes=file_size,
            mime_type=file.content_type or "application/octet-stream",
            batch_id=batch.id,
        )
        db.add(label)
        await db.flush()

        analysis = AnalysisResult(
            label_id=label.id,
            status=AnalysisStatus.PENDING,
            application_details=json.dumps(app_details) if app_details else None,
        )
        db.add(analysis)
        await db.flush()

        items.append({
            "analysis_id": analysis.id,
            "label_id": label.id,
            "image_path": stored_path,
            "application_details": app_details,
        })

    await db.commit()

    pipeline = get_pipeline()
    background_tasks.add_task(_run_batch_pipeline, batch.id, items, pipeline)

    return {"batch_id": batch.id, "total_labels": len(items)}


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    batch = await db.get(BatchJob, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = await db.execute(
        select(AnalysisResult)
        .join(Label)
        .where(Label.batch_id == batch_id)
        .order_by(AnalysisResult.created_at)
    )
    analyses = result.scalars().all()

    from app.routers.analysis import _to_response

    return BatchDetailResponse(
        batch=BatchResponse.model_validate(batch),
        analyses=[_to_response(a) for a in analyses],
    )


@router.get("/{batch_id}/stream")
async def stream_batch_progress(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    batch = await db.get(BatchJob, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    async def event_generator():
        from app.dependencies import session_factory

        while True:
            async with session_factory() as session:
                batch = await session.get(BatchJob, batch_id)
                if not batch:
                    break

                data = {
                    "status": batch.status.value if hasattr(batch.status, "value") else batch.status,
                    "total": batch.total_labels,
                    "completed": batch.completed_labels,
                    "failed": batch.failed_labels,
                }
                yield f"data: {json.dumps(data)}\n\n"

                if batch.status in (BatchStatus.COMPLETED, BatchStatus.FAILED):
                    break

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
