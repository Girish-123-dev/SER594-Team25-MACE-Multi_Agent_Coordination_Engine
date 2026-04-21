import json
import logging
import time
from abc import ABC, abstractmethod

import anthropic
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    content: str
    parsed: dict | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    latency_ms: float = 0.0


class BaseLLMService(ABC):
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        output_schema: dict | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse: ...


class AnthropicService(BaseLLMService):
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model_name
        self.max_retries = 3

    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        output_schema: dict | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if output_schema:
            prompt += (
                "\n\nRespond ONLY with valid JSON matching this schema. "
                "No markdown, no extra text.\n"
                f"Schema: {json.dumps(output_schema)}"
            )

        messages = [{"role": "user", "content": prompt}]
        last_error = None

        for attempt in range(self.max_retries):
            try:
                start = time.time()
                kwargs = {"model": self.model, "max_tokens": max_tokens, "messages": messages}
                if system_prompt:
                    kwargs["system"] = system_prompt
                response = self.client.messages.create(**kwargs)
                latency = (time.time() - start) * 1000

                content = response.content[0].text
                parsed = None
                if output_schema:
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning("LLM returned non-JSON output, returning raw text")

                result = LLMResponse(
                    content=content,
                    parsed=parsed,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=self.model,
                    latency_ms=round(latency, 2),
                )
                logger.info(
                    "LLM call: model=%s input_tokens=%d output_tokens=%d latency=%.0fms",
                    self.model,
                    result.input_tokens,
                    result.output_tokens,
                    result.latency_ms,
                )
                return result

            except anthropic.RateLimitError as e:
                last_error = e
                wait = 2**attempt
                logger.warning(
                    "Rate limited (attempt %d/%d), retrying in %ds",
                    attempt + 1,
                    self.max_retries,
                    wait,
                )
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                last_error = e
                if e.status_code >= 500:
                    wait = 2**attempt
                    logger.warning(
                        "Server error %d (attempt %d/%d), retrying in %ds",
                        e.status_code,
                        attempt + 1,
                        self.max_retries,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_error}")


_llm: BaseLLMService | None = None


def get_llm_service() -> BaseLLMService:
    global _llm
    if _llm is None:
        _llm = AnthropicService()
    return _llm
