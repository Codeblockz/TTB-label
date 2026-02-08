"""Integration tests using real Azure AI services."""

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
from app.services.pipeline import AnalysisPipeline

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_LABEL = os.path.join(FIXTURE_DIR, "river_vodka.png")


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def real_pipeline():
    from app.services.ocr.azure_vision import AzureVisionOCRService
    from app.services.llm.azure_openai import AzureOpenAILLMService

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
async def test_real_ocr_extracts_text():
    """Azure Vision OCR reads text from a real vodka label image."""
    from app.services.ocr.azure_vision import AzureVisionOCRService

    ocr = AzureVisionOCRService(settings.azure_vision_endpoint, settings.azure_vision_key)
    result = await ocr.extract_text(SAMPLE_LABEL)

    assert len(result.text) > 50, f"OCR returned too little text: {result.text!r}"
    assert result.confidence > 0.5
    assert result.duration_ms > 0

    # The image is a vodka label — expect common label terms
    text_upper = result.text.upper()
    assert any(
        term in text_upper
        for term in ["VODKA", "PROOF", "ALC", "DISTILL"]
    ), f"OCR text doesn't contain expected vodka label terms: {result.text[:300]}"


@pytest.mark.asyncio
async def test_real_llm_returns_compliance_json():
    """Azure OpenAI returns valid compliance JSON for bourbon label text."""
    import json

    from app.services.llm.azure_openai import AzureOpenAILLMService
    from app.services.compliance.prompts import COMPLIANCE_ANALYSIS_PROMPT

    llm = AzureOpenAILLMService(
        settings.azure_openai_endpoint,
        settings.azure_openai_key,
        settings.azure_openai_deployment,
        settings.azure_openai_api_version,
    )

    sample_text = (
        "KNOB CREEK\n"
        "Kentucky Straight Bourbon Whiskey\n"
        "Small Batch aged nine years\n"
        "100 PROOF\n"
        "750 mL\n"
        "50% Alc./Vol.\n"
        "Distilled and Bottled by Knob Creek Distilling Co., Clermont, KY"
    )
    prompt = COMPLIANCE_ANALYSIS_PROMPT % sample_text
    raw = await llm.analyze_compliance(sample_text, prompt)

    data = json.loads(raw)
    assert "findings" in data, f"LLM response missing 'findings': {raw[:300]}"
    assert isinstance(data["findings"], list)
    assert len(data["findings"]) > 0

    for finding in data["findings"]:
        assert "rule_id" in finding
        assert "severity" in finding
        assert finding["severity"] in ("pass", "fail", "warning", "info")


@pytest.mark.asyncio
async def test_real_full_pipeline(db: AsyncSession, real_pipeline: AnalysisPipeline):
    """Full pipeline with real Azure OCR + LLM against a real vodka label image."""
    label = Label(
        original_filename="river_vodka.png",
        stored_filepath=SAMPLE_LABEL,
        file_size_bytes=os.path.getsize(SAMPLE_LABEL),
        mime_type="image/png",
    )
    db.add(label)
    await db.flush()

    analysis = AnalysisResult(label_id=label.id, status=AnalysisStatus.PENDING)
    db.add(analysis)
    await db.commit()

    await real_pipeline.run(analysis.id, label.id, SAMPLE_LABEL, db)

    await db.refresh(analysis)

    # Pipeline completed successfully
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.error_message is None

    # OCR produced results
    assert analysis.extracted_text is not None
    assert len(analysis.extracted_text) > 50
    assert analysis.ocr_confidence is not None
    assert analysis.ocr_confidence > 0.5
    assert analysis.ocr_duration_ms is not None

    # Compliance analysis produced results
    assert analysis.compliance_findings is not None
    assert analysis.overall_verdict is not None
    assert analysis.overall_verdict in ("pass", "fail", "warnings")
    assert analysis.compliance_duration_ms is not None

    # Metadata extracted
    assert analysis.detected_beverage_type is not None

    # Performance budget: under 15s (generous for real API calls)
    assert analysis.total_duration_ms is not None
    assert analysis.total_duration_ms < 15000, (
        f"Pipeline took {analysis.total_duration_ms}ms — exceeds 15s budget"
    )

    print(f"\n--- Real Pipeline Results ---")
    print(f"OCR text ({len(analysis.extracted_text)} chars): {analysis.extracted_text[:200]}...")
    print(f"Verdict: {analysis.overall_verdict}")
    print(f"Beverage type: {analysis.detected_beverage_type}")
    print(f"Brand: {analysis.detected_brand_name}")
    print(f"Total time: {analysis.total_duration_ms}ms")
