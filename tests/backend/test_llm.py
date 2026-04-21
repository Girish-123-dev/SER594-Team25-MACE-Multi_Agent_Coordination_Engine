import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.llm import AnthropicService, LLMResponse  # noqa: E402


def _make_mock_response(content: str, input_tokens: int = 50, output_tokens: int = 100):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=content)]
    mock_resp.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return mock_resp


@patch("app.services.llm.settings")
@patch("app.services.llm.anthropic.Anthropic")
def test_complete_returns_llm_response(mock_anthropic_cls, mock_settings):
    mock_settings.anthropic_api_key = "test-key"
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        '{"intent_type": "support_ticket"}'
    )

    service = AnthropicService()
    result = service.complete("test prompt", system_prompt="you are a parser")

    assert isinstance(result, LLMResponse)
    assert result.input_tokens == 50
    assert result.output_tokens == 100
    assert result.content == '{"intent_type": "support_ticket"}'


@patch("app.services.llm.settings")
@patch("app.services.llm.anthropic.Anthropic")
def test_complete_with_json_schema_parsing(mock_anthropic_cls, mock_settings):
    mock_settings.anthropic_api_key = "test-key"
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        '{"intent_type": "faq_query", "summary": "password help"}'
    )

    service = AnthropicService()
    result = service.complete("help", output_schema={"intent_type": "string"})

    assert result.parsed is not None
    assert result.parsed["intent_type"] == "faq_query"


@patch("app.services.llm.settings")
@patch("app.services.llm.anthropic.Anthropic")
def test_complete_handles_non_json_gracefully(mock_anthropic_cls, mock_settings):
    mock_settings.anthropic_api_key = "test-key"
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response("This is not JSON")

    service = AnthropicService()
    result = service.complete("test", output_schema={"key": "string"})

    assert result.parsed is None
    assert result.content == "This is not JSON"


@patch("app.services.llm.settings")
@patch("app.services.llm.anthropic.Anthropic")
def test_token_tracking(mock_anthropic_cls, mock_settings):
    mock_settings.anthropic_api_key = "test-key"
    mock_settings.model_name = "test-model"

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        "ok", input_tokens=25, output_tokens=75
    )

    service = AnthropicService()
    result = service.complete("test")

    assert result.input_tokens == 25
    assert result.output_tokens == 75
    assert result.latency_ms > 0
