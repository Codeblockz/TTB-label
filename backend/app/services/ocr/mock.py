import asyncio
import random

from app.services.ocr.base import OCRResult

MOCK_LABEL_TEXT = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.

OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
Distilled and Bottled by Old Tom Distillery, Louisville, Kentucky

45% Alc./Vol. (90 Proof)
750 mL

Product of USA"""


class MockOCRService:
    async def extract_text(self, image_path: str) -> OCRResult:
        await asyncio.sleep(random.uniform(0.3, 0.7))
        return OCRResult(
            text=MOCK_LABEL_TEXT,
            confidence=0.94,
            duration_ms=random.randint(400, 600),
        )
