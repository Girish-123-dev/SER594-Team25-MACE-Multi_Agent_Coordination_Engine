import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.llm import GeminiService, LLMResponse  # noqa: E402


def _make_mock_response(content: str, input_tokens: int = 50, output_tokens: int = 100):
    mock_um = MagicMock()
    mock_um.prompt_token_count = input_tokens
    mock_um.candidates_token_count = output_tokens
    mock_resp = MagicMock()
    mock_resp.text = content
    mock_resp.usage_metadata = mock_um
    mock_resp.candidates = []
    return mock_resp


@patch("app.services.llm.settings")
@patch("app.services.llm.genai.Client")
def test_complete_returns_llm_response(mock_client_cls, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.google_api_key = ""
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response(
        '{"intent_type": "support_ticket"}'
    )

    service = GeminiService()
    result = service.complete("test prompt", system_prompt="you are a parser")

    assert isinstance(result, LLMResponse)
    assert result.input_tokens == 50
    assert result.output_tokens == 100
    assert result.content == '{"intent_type": "support_ticket"}'


@patch("app.services.llm.settings")
@patch("app.services.llm.genai.Client")
def test_complete_with_json_schema_parsing(mock_client_cls, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.google_api_key = ""
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response(
        '{"intent_type": "faq_query", "summary": "password help"}'
    )

    service = GeminiService()
    result = service.complete("help", output_schema={"intent_type": "string"})

    assert result.parsed is not None
    assert result.parsed["intent_type"] == "faq_query"


@patch("app.services.llm.settings")
@patch("app.services.llm.genai.Client")
def test_complete_handles_non_json_gracefully(mock_client_cls, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.google_api_key = ""
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response("This is not JSON")

    service = GeminiService()
    result = service.complete("test", output_schema={"key": "string"})

    assert result.parsed is None
    assert result.content == "This is not JSON"


@patch("app.services.llm.settings")
@patch("app.services.llm.genai.Client")
def test_token_tracking(mock_client_cls, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.google_api_key = ""
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response(
        "ok", input_tokens=25, output_tokens=75
    )

    service = GeminiService()
    result = service.complete("test")

    assert result.input_tokens == 25
    assert result.output_tokens == 75
    assert result.latency_ms > 0
