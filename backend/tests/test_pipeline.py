import json

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.base import Base
from app.models.batch import BatchJob  # noqa: F401
from app.models.label import Label
from app.services.compliance.engine import ComplianceEngine
from app.services.llm.mock import MockLLMService
from app.services.ocr.mock import MockOCRService
from app.services.pipeline import AnalysisPipeline


@pytest_asyncio.fixture
async def pipeline_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def pipeline():
    ocr = MockOCRService()
    llm = MockLLMService()
    engine = ComplianceEngine(llm)
    return AnalysisPipeline(ocr, engine)


@pytest.mark.asyncio
async def test_pipeline_completes_successfully(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    # Create a label record
    label = Label(
        original_filename="test_label.jpg",
        stored_filepath="/tmp/test_label.jpg",
        file_size_bytes=1024,
        mime_type="image/jpeg",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    # Create an analysis record
    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    # Run the pipeline
    await pipeline.run(analysis.id, label.id, "/tmp/test_label.jpg", pipeline_db)

    # Refresh and verify
    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.extracted_text is not None
    assert "GOVERNMENT WARNING" in analysis.extracted_text
    assert analysis.ocr_confidence is not None
    assert analysis.ocr_duration_ms is not None
    assert analysis.compliance_findings is not None
    assert analysis.overall_verdict is not None
    assert analysis.total_duration_ms is not None
    assert analysis.total_duration_ms > 0


@pytest.mark.asyncio
async def test_pipeline_sets_beverage_type(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="bourbon.jpg",
        stored_filepath="/tmp/bourbon.jpg",
        file_size_bytes=2048,
        mime_type="image/jpeg",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    await pipeline.run(analysis.id, label.id, "/tmp/bourbon.jpg", pipeline_db)

    await pipeline_db.refresh(analysis)
    assert analysis.detected_beverage_type is not None
    assert analysis.detected_brand_name is not None


@pytest.mark.asyncio
async def test_pipeline_with_application_details(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="bourbon.jpg",
        stored_filepath="/tmp/bourbon.jpg",
        file_size_bytes=2048,
        mime_type="image/jpeg",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    app_details = {
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Kentucky Straight Bourbon Whiskey",
        "alcohol_content": "45% Alc./Vol.",
    }

    await pipeline.run(analysis.id, label.id, "/tmp/bourbon.jpg", pipeline_db, app_details)

    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.compliance_findings is not None
    # Should contain matching findings (BRAND_MATCH, CLASS_TYPE_MATCH, etc.)
    findings = json.loads(analysis.compliance_findings)
    matching_ids = [f["rule_id"] for f in findings if f["rule_id"].endswith("_MATCH")]
    assert len(matching_ids) > 0
    assert "BRAND_MATCH" in matching_ids


@pytest.mark.asyncio
async def test_pipeline_without_application_details(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="test.jpg",
        stored_filepath="/tmp/test.jpg",
        file_size_bytes=1024,
        mime_type="image/jpeg",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    await pipeline.run(analysis.id, label.id, "/tmp/test.jpg", pipeline_db)

    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    # Should NOT contain matching findings
    findings = json.loads(analysis.compliance_findings)
    matching_ids = [f["rule_id"] for f in findings if f["rule_id"].endswith("_MATCH")]
    assert len(matching_ids) == 0
