from typing import Protocol


class LLMServiceProtocol(Protocol):
    async def analyze_compliance(self, text: str, prompt: str) -> str: ...
