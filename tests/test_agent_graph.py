from unittest.mock import MagicMock, patch

from dnd_bot.agents.player import PlayerAgent, TurnResult
from dnd_bot.agents.tools import COMBAT_TOOLS, EXPLORATION_TOOLS
from dnd_bot.character import Equipment, SpeciesName, create_character, get_species
from dnd_bot.character.skills import Skill


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment = Equipment()
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS]
    char.background.to_prompt_context.return_value = "A warrior."
    return char


def test_player_agent_init():
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    assert agent is not None
    assert agent.character is char
    assert agent.mode == "exploration"


def test_process_turn_returns_turn_result():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "I look around carefully."
    mock_response.tool_calls = []
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("dnd_bot.agents.player.get_llm", return_value=mock_llm):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        result = agent.process_turn("You enter the cave.")
    assert isinstance(result, TurnResult)
    assert result.narrative == "I look around carefully."
    assert result.mode == "exploration"
    assert result.actions == []


def test_change_mode_tool_is_in_agent_tools():
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    assert "change_mode" in [t.name for t in agent.tools]


def test_process_turn_change_mode_updates_agent_mode():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "I ready my weapon!"
    mock_response.tool_calls = [
        {"name": "change_mode", "args": {"mode": "combat"}, "id": "tc1"}
    ]
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("dnd_bot.agents.player.get_llm", return_value=mock_llm):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        result = agent.process_turn("Enemies appear!")

    assert agent.mode == "combat"
    assert result.mode == "combat"


def test_exploration_mode_tools_exclude_combat_only_tools():
    """In exploration mode, attack and make_saving_throw must not be in agent.tools."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    tool_names = {t.name for t in agent.tools}
    assert "attack" not in tool_names
    assert "make_saving_throw" not in tool_names


def test_exploration_mode_tools_include_exploration_tools():
    """In exploration mode, all EXPLORATION_TOOLS must be present in agent.tools."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    tool_names = {t.name for t in agent.tools}
    assert EXPLORATION_TOOLS.issubset(tool_names)


def test_set_mode_to_combat_swaps_tools():
    """After set_mode('combat'), agent.tools should include attack and exclude describe_action."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        agent.set_mode("combat")
    tool_names = {t.name for t in agent.tools}
    assert "attack" in tool_names
    assert "make_saving_throw" in tool_names
    assert "describe_action" not in tool_names
    assert "check_inventory" not in tool_names


def test_combat_mode_tools_include_combat_tools():
    """In combat mode, all COMBAT_TOOLS must be present in agent.tools."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        agent.set_mode("combat")
    tool_names = {t.name for t in agent.tools}
    assert COMBAT_TOOLS.issubset(tool_names)


def test_combat_mode_includes_class_ability_tools():
    """In combat mode, class ability tools (e.g. second_wind for Fighter) must be present."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=3,
    )
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        agent.set_mode("combat")
    tool_names = {t.name for t in agent.tools}
    assert "second_wind" in tool_names
    assert "action_surge" in tool_names


def test_exploration_mode_excludes_class_ability_tools():
    """In exploration mode, combat-only class ability tools must not be present."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=3,
    )
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    tool_names = {t.name for t in agent.tools}
    assert "second_wind" not in tool_names
    assert "action_surge" not in tool_names


def test_set_mode_back_to_exploration_restores_exploration_tools():
    """Switching exploration -> combat -> exploration restores exploration tool set."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        agent.set_mode("combat")
        agent.set_mode("exploration")
    tool_names = {t.name for t in agent.tools}
    assert EXPLORATION_TOOLS.issubset(tool_names)
    assert "attack" not in tool_names


def test_set_mode_roleplay_falls_back_to_exploration_tools():
    """'roleplay' mode is valid but unrecognised by _bind_tools_for_mode, so it falls
    back to the exploration tool set: check_inventory and describe_action present,
    attack absent."""
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        agent.set_mode("roleplay")
    tool_names = {t.name for t in agent.tools}
    assert "check_inventory" in tool_names
    assert "describe_action" in tool_names
    assert "attack" not in tool_names
