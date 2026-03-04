from unittest.mock import MagicMock, patch

import pytest

from dnd_bot.agents.llm import get_llm


def test_get_llm_ollama_returns_model():
    with patch("dnd_bot.agents.llm.ChatOllama", return_value=MagicMock()):
        result = get_llm(provider="ollama", model="llama3:8b")
    assert result is not None


def test_get_llm_anthropic_returns_model():
    with patch("dnd_bot.agents.llm.ChatAnthropic", return_value=MagicMock()):
        result = get_llm(provider="anthropic", model="claude-haiku-4-5-20251001")
    assert result is not None


def test_get_llm_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_llm(provider="unknown")
