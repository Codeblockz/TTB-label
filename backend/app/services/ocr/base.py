from dataclasses import dataclass
from typing import Protocol


@dataclass
class OCRResult:
    text: str
    confidence: float
    duration_ms: int


class OCRServiceProtocol(Protocol):
    async def extract_text(self, image_path: str) -> OCRResult: ...
