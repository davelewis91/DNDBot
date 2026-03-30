from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from dnd_bot.agents.player_node import _filter_tools_for_mode, make_player_node
from dnd_bot.agents.tools import COMBAT_TOOLS, EXPLORATION_TOOLS
from dnd_bot.character import SpeciesName, get_species
from dnd_bot.character.skills import Skill


def make_mock_character(name="Thorin"):
    char = MagicMock()
    char.name = name
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    from dnd_bot.character import Equipment
    char.equipment = Equipment()
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS]
    char.background.to_prompt_context.return_value = "A warrior."
    char.roll_initiative.return_value = (15, 12)
    char.class_features = []
    char.resources.feature_uses = {}
    return char


def make_game_state(char, mode="exploration", messages=None):
    return {
        "messages": messages or [HumanMessage(content="You enter a tavern.")],
        "mode": mode,
        "party": [char],
        "initiative_order": [],
        "initiative_index": 0,
        "next_speaker": char.name,
        "consecutive_agent_turns": 0,
    }


def _make_change_mode_stub():
    from langchain_core.tools import tool

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

    state = make_game_state(char)
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
    state = make_game_state(char)
    state["next_speaker"] = "Nobody"
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

    state = make_game_state(char)
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

    state = make_game_state(char)
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

    state = make_game_state(char)
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

    state = make_game_state(char)
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

    state = make_game_state(char)
    with patch("dnd_bot.agents.player_node.get_llm", return_value=mock_llm):
        player_node = make_player_node()
        result = player_node(state)

    assert result["messages"][0].additional_kwargs["importance"] == 5.0
