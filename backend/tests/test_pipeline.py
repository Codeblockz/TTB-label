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
