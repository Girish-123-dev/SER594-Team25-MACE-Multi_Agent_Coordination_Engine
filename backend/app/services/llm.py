import json
import logging
import time
from abc import ABC, abstractmethod

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
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


def _usage_tokens(response: types.GenerateContentResponse) -> tuple[int, int]:
    um = response.usage_metadata
    if not um:
        return 0, 0
    inp = um.prompt_token_count or 0
    out = um.candidates_token_count or 0
    return int(inp), int(out)


def _response_text(response: types.GenerateContentResponse) -> str:
    try:
        t = response.text
        if t is not None:
            return t
    except (ValueError, AttributeError):
        pass
    if response.candidates:
        parts = response.candidates[0].content.parts
        return "".join(p.text or "" for p in parts if p.text is not None)
    return ""


class GeminiService(BaseLLMService):
    """Google Gemini API via the unified `google-genai` SDK (Developer API key)."""

    def __init__(self):
        key = (settings.gemini_api_key or settings.google_api_key).strip()
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set")
        self.client = genai.Client(api_key=key)
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

        config_kw: dict = {"max_output_tokens": max_tokens}
        if system_prompt:
            config_kw["system_instruction"] = system_prompt
        config = types.GenerateContentConfig(**config_kw)

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                start = time.time()
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                latency = (time.time() - start) * 1000

                content = _response_text(response)
                input_tokens, output_tokens = _usage_tokens(response)

                parsed = None
                if output_schema:
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        # Gemini often wraps JSON in ```json ... ``` blocks
                        import re
                        m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", content, re.DOTALL)
                        if m:
                            try:
                                parsed = json.loads(m.group(1))
                            except json.JSONDecodeError:
                                logger.warning("LLM returned non-JSON output, returning raw text")
                        else:
                            logger.warning("LLM returned non-JSON output, returning raw text")

                result = LLMResponse(
                    content=content,
                    parsed=parsed,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
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

            except ServerError as e:
                last_error = e
                wait = 2**attempt
                logger.warning(
                    "Gemini server error (attempt %d/%d): %s, retrying in %ds",
                    attempt + 1,
                    self.max_retries,
                    e,
                    wait,
                )
                time.sleep(wait)
            except ClientError as e:
                last_error = e
                if e.code == 429:
                    wait = 2**attempt
                    logger.warning(
                        "Rate limited (attempt %d/%d), retrying in %ds",
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
        _llm = GeminiService()
    return _llm
