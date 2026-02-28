from dnd_bot.agents.prompts import build_character_context, PLAYER_SYSTEM_PROMPT, MODE_GUIDANCE
from dnd_bot.character.skills import Skill
from unittest.mock import MagicMock


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = "Dwarf"
    char.current_hp = 28
    char.max_hp = 32
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS, Skill.PERCEPTION]
    char.background.to_prompt_context.return_value = "A gruff dwarven warrior."
    char.equipment = []
    return char


def test_build_character_context_contains_name():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "Thorin" in ctx


def test_build_character_context_contains_hp():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "28/32" in ctx


def test_build_character_context_contains_mode():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "exploration" in ctx.lower()


def test_player_system_prompt_is_string():
    assert isinstance(PLAYER_SYSTEM_PROMPT, str)


def test_mode_guidance_has_all_modes():
    assert "combat" in MODE_GUIDANCE
    assert "exploration" in MODE_GUIDANCE
    assert "roleplay" in MODE_GUIDANCE
