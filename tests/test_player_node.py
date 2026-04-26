from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from dnd_bot.agents.player_node import (
    _build_character_messages,
    _filter_tools_for_mode,
    make_player_node,
)
from dnd_bot.agents.tools import COMBAT_TOOLS, EXPLORATION_TOOLS
from tests.helpers import make_game_state, make_mock_character


def _make_change_mode_stub():
    @tool
    def change_mode(new_mode: str) -> str:
        """Switch the current game mode."""
        return f"Mode changed to {new_mode}"

    return change_mode


def test_filter_tools_for_exploration_excludes_combat_only():
    char = make_mock_character()
    from dnd_bot.agents.tools import ToolContext, build_tools
    all_tools = build_tools(ToolContext(character=char)) + [_make_change_mode_stub()]
    filtered = _filter_tools_for_mode(all_tools, "exploration")
    names = {t.name for t in filtered}
    assert "attack" not in names
    assert "make_saving_throw" not in names
    assert EXPLORATION_TOOLS.issubset(names)


def test_filter_tools_for_combat_includes_attack():
    char = make_mock_character()
    from dnd_bot.agents.tools import ToolContext, build_tools
    all_tools = build_tools(ToolContext(character=char)) + [_make_change_mode_stub()]
    filtered = _filter_tools_for_mode(all_tools, "combat")
    names = {t.name for t in filtered}
    assert "attack" in names
    assert COMBAT_TOOLS.issubset(names)


def test_player_node_returns_messages():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I look around carefully."
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node(model="llama3:8b", provider="ollama")
        result = player_node(state)

    assert "messages" in result
    assert any(m is mock_response for m in result["messages"])


def test_player_node_increments_consecutive_turns():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I act."
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char)
    state["consecutive_agent_turns"] = 2
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["consecutive_agent_turns"] == 3


def test_player_node_unknown_speaker_increments_and_returns():
    """If next_speaker doesn't match any party member, skip gracefully."""
    char = make_mock_character(name="Vorn")
    state = make_game_state(char, next_speaker="Nobody")
    player_node = make_player_node()
    result = player_node(state)
    assert result["consecutive_agent_turns"] == 1
    assert result.get("messages", []) == []


def test_player_node_change_mode_updates_state_mode():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I draw my sword!"
    mock_response.additional_kwargs = {}
    mock_response.tool_calls = [
        {"name": "change_mode", "args": {"new_mode": "combat"}, "id": "tc1"}
    ]
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["mode"] == "combat"


def test_player_node_tool_calls_produce_tool_messages():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "Checking status."
    mock_response.additional_kwargs = {}
    mock_response.tool_calls = [
        {"name": "check_status", "args": {}, "id": "tc2"}
    ]
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].tool_call_id == "tc2"


def test_player_node_tags_character_name_on_response():
    char = make_mock_character(name="Thorin")
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I stand guard."
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["messages"][0].additional_kwargs["character_name"] == "Thorin"


def test_player_node_extracts_importance_from_content():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I charge into battle! [Importance: 7]"
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["messages"][0].additional_kwargs["importance"] == 7.0


def test_player_node_importance_defaults_to_five_when_absent():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I look around."
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["messages"][0].additional_kwargs["importance"] == 5.0


def test_player_node_strips_importance_tag_from_content():
    """The [Importance: X] tag should be removed from the stored message content."""
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "I charge into battle! [Importance: 7]"
    mock_response.tool_calls = []
    mock_response.additional_kwargs = {}
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    state = make_game_state(char, next_speaker=char.name)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert "[Importance:" not in result["messages"][0].content
    assert "I charge into battle!" in result["messages"][0].content
    assert result["messages"][0].additional_kwargs["importance"] == 7.0


# --- _build_character_messages tests ---


def _ai(content, character_name=None, tool_calls=None):
    """Helper to build an AIMessage with optional character_name metadata."""
    kwargs = {}
    if character_name is not None:
        kwargs["character_name"] = character_name
    msg = AIMessage(content=content, additional_kwargs=kwargs)
    if tool_calls:
        msg.tool_calls = tool_calls
    return msg


def test_build_character_messages_keeps_own_ai_messages():
    messages = [
        HumanMessage(content="DM narration"),
        _ai("I swing my axe!", character_name="Vorn"),
    ]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[1], AIMessage)
    assert result[1].content == "I swing my axe!"


def test_build_character_messages_converts_other_ai_messages():
    messages = [
        HumanMessage(content="DM narration"),
        _ai("I meditate quietly.", character_name="Yue"),
    ]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[1], HumanMessage)
    assert result[1].content == "[Yue]: I meditate quietly."


def test_build_character_messages_folds_other_tool_messages():
    messages = [
        _ai(
            "I check the door.",
            character_name="Yue",
            tool_calls=[{"name": "perception", "args": {}, "id": "tc1"}],
        ),
        ToolMessage(content="Rolled 15", tool_call_id="tc1"),
    ]
    result = _build_character_messages(messages, "Vorn")
    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert "[Yue]:" in result[0].content
    assert "[Tool result: Rolled 15]" in result[0].content


def test_build_character_messages_keeps_own_tool_messages():
    messages = [
        _ai(
            "I attack!",
            character_name="Vorn",
            tool_calls=[{"name": "attack", "args": {}, "id": "tc2"}],
        ),
        ToolMessage(content="Hit for 8 damage", tool_call_id="tc2"),
    ]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[0], AIMessage)
    assert isinstance(result[1], ToolMessage)
    assert result[1].content == "Hit for 8 damage"


def test_build_character_messages_preserves_human_messages():
    messages = [
        HumanMessage(content="You enter a tavern."),
        _ai("I look around.", character_name="Vorn"),
    ]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "You enter a tavern."


def test_build_character_messages_treats_missing_metadata_as_own():
    messages = [_ai("Some response without metadata")]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[0], AIMessage)


def test_build_character_messages_handles_block_format_content():
    block_content = [
        {"type": "text", "text": "I cast a spell."},
        {"type": "text", "text": "It glows brightly."},
    ]
    messages = [_ai(block_content, character_name="Yue")]
    result = _build_character_messages(messages, "Vorn")
    assert isinstance(result[0], HumanMessage)
    assert "[Yue]: I cast a spell.\nIt glows brightly." == result[0].content
