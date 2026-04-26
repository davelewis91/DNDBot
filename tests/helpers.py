from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage

from dnd_bot.character import Equipment, SpeciesName, get_species
from dnd_bot.character.skills import Skill


def make_mock_character(name="Thorin", hp=28, max_hp=32):
    """Create a MagicMock character with sensible defaults for testing."""
    char = MagicMock()
    char.name = name
    char.character_class = "Fighter"
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = hp
    char.max_hp = max_hp
    char.conditions = []
    char.equipment = Equipment()
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS]
    char.background.to_prompt_context.return_value = "A warrior."
    char.class_features = []
    char.resources.feature_uses = {}
    return char


def make_game_state(party, mode="exploration", messages=None, next_speaker=None,
                    consecutive=0, initiative_order=None):
    """Create a GameState dict for testing."""
    return {
        "messages": messages or [HumanMessage(content="You enter a tavern.")],
        "mode": mode,
        "party": party if isinstance(party, list) else [party],
        "initiative_order": initiative_order or [],
        "initiative_rolls": {},
        "initiative_index": 0,
        "next_speaker": next_speaker,
        "consecutive_agent_turns": consecutive,
    }
