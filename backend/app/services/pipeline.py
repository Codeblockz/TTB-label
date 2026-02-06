import json
import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisResult, AnalysisStatus, OverallVerdict
from app.models.label import Label
from app.services.compliance.engine import ComplianceEngine
from app.services.ocr.base import OCRServiceProtocol
from app.services.storage import save_upload

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(
        self,
        ocr_service: OCRServiceProtocol,
        compliance_engine: ComplianceEngine,
    ) -> None:
        self._ocr = ocr_service
        self._compliance = compliance_engine

    async def run(self, analysis_id: str, label_id: str, image_path: str, db: AsyncSession) -> None:
        total_start = time.perf_counter()

        try:
            # Stage 1: OCR
            analysis = await db.get(AnalysisResult, analysis_id)
            if not analysis:
                logger.error("Analysis %s not found", analysis_id)
                return

            analysis.status = AnalysisStatus.PROCESSING_OCR
            await db.commit()

            ocr_result = await self._ocr.extract_text(image_path)

            analysis.extracted_text = ocr_result.text
            analysis.ocr_confidence = ocr_result.confidence
            analysis.ocr_duration_ms = ocr_result.duration_ms

            # Stage 2: Compliance
            analysis.status = AnalysisStatus.PROCESSING_COMPLIANCE
            await db.commit()

            report, compliance_duration_ms = await self._compliance.analyze(ocr_result.text)

            analysis.compliance_findings = json.dumps(
                [f.model_dump() for f in report.findings]
            )
            analysis.overall_verdict = report.overall_verdict
            analysis.compliance_duration_ms = compliance_duration_ms
            analysis.detected_beverage_type = report.beverage_type
            analysis.detected_brand_name = report.brand_name

            # Done
            analysis.status = AnalysisStatus.COMPLETED
            analysis.total_duration_ms = int((time.perf_counter() - total_start) * 1000)
            await db.commit()

            logger.info(
                "Analysis %s completed in %dms (verdict: %s)",
                analysis_id,
                analysis.total_duration_ms,
                analysis.overall_verdict,
            )

        except Exception as exc:
            logger.exception("Analysis %s failed: %s", analysis_id, exc)
            analysis = await db.get(AnalysisResult, analysis_id)
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(exc)
                analysis.total_duration_ms = int((time.perf_counter() - total_start) * 1000)
                await db.commit()
