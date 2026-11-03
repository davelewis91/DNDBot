from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from dnd_bot.cli.game import _summarise_messages


def make_messages(n: int) -> list:
    """Build a list of alternating HumanMessage and AIMessage."""
    msgs = []
    for i in range(n):
        msgs.append(HumanMessage(content=f"DM {i + 1}"))
        ai = MagicMock(spec=AIMessage)
        ai.content = f"Agent {i + 1}"
        ai.tool_calls = []
        msgs.append(ai)
    return msgs


def test_summarise_messages_no_op_when_short():
    """_summarise_messages returns original list unchanged when <= SUMMARISE_KEEP_RECENT."""
    from dnd_bot.cli.game import SUMMARISE_KEEP_RECENT
    messages = make_messages(SUMMARISE_KEEP_RECENT // 2)
    result = _summarise_messages(messages, model="llama3:8b", provider="ollama")
    assert result is messages


def test_summarise_messages_compacts_to_summary_plus_recent():
    """_summarise_messages returns [SystemMessage(summary)] + last SUMMARISE_KEEP_RECENT msgs."""
    from dnd_bot.cli.game import SUMMARISE_KEEP_RECENT
    # Build more messages than the threshold to ensure compaction
    messages = make_messages(20)

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Compact summary here.")

    with patch("dnd_bot.cli.game.get_llm", return_value=mock_llm):
        result = _summarise_messages(messages, model="llama3:8b", provider="ollama")

    assert isinstance(result[0], SystemMessage)
    assert "Compact summary here." in result[0].content
    assert len(result) == SUMMARISE_KEEP_RECENT + 1  # summary + recent


def test_summarise_messages_keeps_exact_recent_count():
    """The last SUMMARISE_KEEP_RECENT messages are preserved verbatim."""
    from dnd_bot.cli.game import SUMMARISE_KEEP_RECENT
    messages = make_messages(20)
    expected_recent = messages[-SUMMARISE_KEEP_RECENT:]

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Summary.")

    with patch("dnd_bot.cli.game.get_llm", return_value=mock_llm):
        result = _summarise_messages(messages, model="llama3:8b", provider="ollama")

    assert result[1:] == expected_recent
