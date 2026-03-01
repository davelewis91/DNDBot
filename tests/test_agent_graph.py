from unittest.mock import MagicMock, patch

from dnd_bot.agents.player import PlayerAgent
from dnd_bot.character import Equipment, SpeciesName, get_species
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


def test_process_turn_returns_string():
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
    assert isinstance(result, str)
    assert len(result) > 0
