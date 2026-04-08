"""LLM client wrapping the OpenAI-compatible API exposed by Ollama."""

import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the OpenAI SDK pointing at Ollama's /v1 endpoint."""

    def __init__(self, base_url: str, model: str):
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key="ollama")
        logger.info("LLMClient ready — model=%s  url=%s", model, base_url)

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Send a chat completion and return the text content."""
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return resp.choices[0].message.content or ""
