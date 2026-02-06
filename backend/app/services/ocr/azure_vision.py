import asyncio
import time

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

from app.services.ocr.base import OCRResult


class AzureVisionOCRService:
    def __init__(self, endpoint: str, key: str) -> None:
        self._client = ImageAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )

    def _extract_sync(self, image_data: bytes) -> object:
        result = self._client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.READ],
        )
        return result

    async def extract_text(self, image_path: str) -> OCRResult:
        start = time.perf_counter()

        with open(image_path, "rb") as f:
            image_data = f.read()

        result = await asyncio.to_thread(self._extract_sync, image_data)

        lines: list[str] = []
        confidences: list[float] = []
        if result.read and result.read.blocks:
            for block in result.read.blocks:
                for line in block.lines:
                    lines.append(line.text)
                    for word in line.words:
                        confidences.append(word.confidence)

        text = "\n".join(lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        duration_ms = int((time.perf_counter() - start) * 1000)

        return OCRResult(text=text, confidence=avg_confidence, duration_ms=duration_ms)
