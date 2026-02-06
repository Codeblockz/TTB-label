from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings
from app.db.session import async_session_factory as _default_factory
from app.services.compliance.engine import ComplianceEngine
from app.services.llm.base import LLMServiceProtocol
from app.services.llm.mock import MockLLMService
from app.services.ocr.base import OCRServiceProtocol
from app.services.ocr.mock import MockOCRService
from app.services.pipeline import AnalysisPipeline

# Overridable session factory — tests swap this to point at the in-memory DB
session_factory: async_sessionmaker[AsyncSession] = _default_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


def get_ocr_service() -> OCRServiceProtocol:
    if settings.use_mock_services:
        return MockOCRService()
    from app.services.ocr.azure_vision import AzureVisionOCRService
    return AzureVisionOCRService(settings.azure_vision_endpoint, settings.azure_vision_key)


def get_llm_service() -> LLMServiceProtocol:
    if settings.use_mock_services:
        return MockLLMService()
    from app.services.llm.azure_openai import AzureOpenAILLMService
    return AzureOpenAILLMService(
        settings.azure_openai_endpoint,
        settings.azure_openai_key,
        settings.azure_openai_deployment,
        settings.azure_openai_api_version,
    )


def get_pipeline() -> AnalysisPipeline:
    ocr = get_ocr_service()
    llm = get_llm_service()
    engine = ComplianceEngine(llm)
    return AnalysisPipeline(ocr, engine)
