from urllib.parse import urlparse

from openai import AsyncAzureOpenAI


class AzureOpenAILLMService:
    def __init__(
        self, endpoint: str, key: str, deployment: str, api_version: str
    ) -> None:
        parsed = urlparse(endpoint)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        self._client = AsyncAzureOpenAI(
            azure_endpoint=base_url,
            api_key=key,
            api_version=api_version,
        )
        self._deployment = deployment

    async def analyze_compliance(self, text: str, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
