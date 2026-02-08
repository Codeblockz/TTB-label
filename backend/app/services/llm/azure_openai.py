import base64
import mimetypes
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

    async def analyze_compliance(
        self, text: str, prompt: str, image_path: str | None = None,
    ) -> str:
        if image_path:
            content: list[dict] = [{"type": "text", "text": prompt}]
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })
            messages = [{"role": "user", "content": content}]
        else:
            messages = [{"role": "user", "content": prompt}]

        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
