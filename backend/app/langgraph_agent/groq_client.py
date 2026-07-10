import json
import logging
from collections.abc import AsyncIterator
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import AIConfigurationError, AIProviderError, AIResponseValidationError


logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT", bound=BaseModel)


class GroqClient:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise AIConfigurationError("GROQ_API_KEY is required for AI assistant responses.")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, AIProviderError)),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def complete(self, messages: list[dict[str, str]], response_format: dict[str, str] | None = None) -> str:
        payload: dict[str, Any] = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": settings.groq_temperature,
            "max_tokens": settings.groq_max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(self.base_url, headers=self.headers, json=payload)

                print("PAYLOAD:", payload)
                print("STATUS:", response.status_code)
                print("BODY:", response.text)

                response.raise_for_status()

                data = response.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.exception("Groq completion request failed")
            raise AIProviderError("Groq did not return a successful completion after retries.") from exc

    async def complete_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        text = await self.complete(messages, response_format={"type": "json_object"})
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Groq returned malformed JSON", extra={"raw_response": text[:500]})
            raise AIResponseValidationError("The AI returned malformed JSON.") from exc
        if not isinstance(parsed, dict):
            raise AIResponseValidationError("The AI JSON response must be an object.")
        return parsed

    async def complete_model(self, messages: list[dict[str, str]], model: type[ModelT]) -> ModelT:
        payload = await self.complete_json(messages)
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Groq JSON failed Pydantic validation", extra={"model": model.__name__, "errors": exc.errors()})
            raise AIResponseValidationError(f"The AI response did not match {model.__name__}.") from exc

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": settings.groq_temperature,
            "max_tokens": settings.groq_max_tokens,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self.base_url, headers=self.headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line.removeprefix("data: ").strip()
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {}).get("content")
                        if delta:
                            yield delta
        except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError) as exc:
            logger.exception("Groq streaming request failed")
            raise AIProviderError("Groq streaming failed.") from exc
