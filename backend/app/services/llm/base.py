from typing import Protocol


class LLMServiceProtocol(Protocol):
    async def analyze_compliance(
        self, text: str, prompt: str, image_path: str | None = None,
    ) -> str: ...
