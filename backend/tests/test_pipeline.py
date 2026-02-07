import json
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.models.base import Base
from app.models.batch import BatchJob  # noqa: F401
from app.models.label import Label
from app.services.compliance.engine import ComplianceEngine
from app.services.llm.azure_openai import AzureOpenAILLMService
from app.services.ocr.azure_vision import AzureVisionOCRService
from app.services.pipeline import AnalysisPipeline

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_LABEL = os.path.join(FIXTURE_DIR, "river_vodka.png")


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
    ocr = AzureVisionOCRService(settings.azure_vision_endpoint, settings.azure_vision_key)
    llm = AzureOpenAILLMService(
        settings.azure_openai_endpoint,
        settings.azure_openai_key,
        settings.azure_openai_deployment,
        settings.azure_openai_api_version,
    )
    engine = ComplianceEngine(llm)
    return AnalysisPipeline(ocr, engine)


@pytest.mark.asyncio
async def test_pipeline_completes_successfully(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="river_vodka.png",
        stored_filepath=SAMPLE_LABEL,
        file_size_bytes=os.path.getsize(SAMPLE_LABEL),
        mime_type="image/png",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    await pipeline.run(analysis.id, label.id, SAMPLE_LABEL, pipeline_db)

    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.extracted_text is not None
    assert len(analysis.extracted_text) > 50
    assert analysis.ocr_confidence is not None
    assert analysis.ocr_duration_ms is not None
    assert analysis.compliance_findings is not None
    assert analysis.overall_verdict is not None
    assert analysis.total_duration_ms is not None
    assert analysis.total_duration_ms > 0


@pytest.mark.asyncio
async def test_pipeline_sets_beverage_type(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="river_vodka.png",
        stored_filepath=SAMPLE_LABEL,
        file_size_bytes=os.path.getsize(SAMPLE_LABEL),
        mime_type="image/png",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    await pipeline.run(analysis.id, label.id, SAMPLE_LABEL, pipeline_db)

    await pipeline_db.refresh(analysis)
    assert analysis.detected_beverage_type is not None
    assert analysis.detected_brand_name is not None


@pytest.mark.asyncio
async def test_pipeline_with_application_details(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="river_vodka.png",
        stored_filepath=SAMPLE_LABEL,
        file_size_bytes=os.path.getsize(SAMPLE_LABEL),
        mime_type="image/png",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    app_details = {
        "brand_name": "RIVERSTONE",
        "class_type": "Vodka",
        "alcohol_content": "40% Alc./Vol.",
    }

    await pipeline.run(analysis.id, label.id, SAMPLE_LABEL, pipeline_db, app_details)

    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.compliance_findings is not None
    findings = json.loads(analysis.compliance_findings)
    matching_ids = [f["rule_id"] for f in findings if f["rule_id"].endswith("_MATCH")]
    assert len(matching_ids) > 0
    assert "BRAND_MATCH" in matching_ids


@pytest.mark.asyncio
async def test_pipeline_without_application_details(pipeline_db: AsyncSession, pipeline: AnalysisPipeline):
    label = Label(
        original_filename="river_vodka.png",
        stored_filepath=SAMPLE_LABEL,
        file_size_bytes=os.path.getsize(SAMPLE_LABEL),
        mime_type="image/png",
    )
    pipeline_db.add(label)
    await pipeline_db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    pipeline_db.add(analysis)
    await pipeline_db.commit()

    await pipeline.run(analysis.id, label.id, SAMPLE_LABEL, pipeline_db)

    await pipeline_db.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    findings = json.loads(analysis.compliance_findings)
    matching_ids = [f["rule_id"] for f in findings if f["rule_id"].endswith("_MATCH")]
    assert len(matching_ids) == 0
