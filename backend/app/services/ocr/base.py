from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class OCRLine:
    text: str
    bounding_polygon: list[tuple[int, int]]


@dataclass
class OCRResult:
    text: str
    confidence: float
    duration_ms: int
    lines: list[OCRLine] = field(default_factory=list)


class OCRServiceProtocol(Protocol):
    async def extract_text(self, image_path: str) -> OCRResult: ...
