from dnd_bot.character.abilities import Ability

PLAYER_SYSTEM_PROMPT = """\
You are roleplaying as {character_context}

Always stay in character. Make decisions that reflect your personality, \
background, and motivations. Use your class abilities and skills appropriately.

Current mode guidance:
{mode_guidance}

Respond with your character's action. Use the available tools to execute \
mechanical actions (attacks, skill checks, etc.). Keep dialogue brief and \
in-character.

When the situation changes significantly — combat begins, an NPC speaks \
directly to you, or combat ends — call change_mode before acting.
"""

MODE_GUIDANCE = {
    "exploration": (
        "You are exploring. Look for clues, interact with the environment, "
        "use perception and investigation. Be curious but cautious."
    ),
    "combat": (
        "You are in combat. Act tactically based on your class. "
        "Use class features when advantageous. Protect allies."
    ),
    "roleplay": (
        "You are in a social situation. Use your background and personality. "
        "Persuasion, deception, or insight may be useful."
    ),
}

_ABILITY_ABBREV = {
    Ability.STRENGTH: "STR", Ability.DEXTERITY: "DEX", Ability.CONSTITUTION: "CON",
    Ability.INTELLIGENCE: "INT", Ability.WISDOM: "WIS", Ability.CHARISMA: "CHA",
}


def build_character_context(character, mode: str) -> str:
    """
    Build a character context string for the system prompt.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character
    mode : str
        Current game mode ("exploration", "combat", or "roleplay")

    Returns
    -------
    str
        Formatted character context for injection into the system prompt
    """
    ability_lines = "\n".join(
        f"  {abbrev}: {character.get_ability_modifier(ability):+d}"
        for ability, abbrev in _ABILITY_ABBREV.items()
    )
    proficient_skills = character.skills.get_proficient_skills()
    skill_lines = "\n".join(
        f"  {skill.value.replace('_', ' ').title()}: {character.get_skill_bonus(skill):+d}"
        for skill in proficient_skills
    )
    equipment_names = character.equipment.item_names()
    equipment_summary = ", ".join(equipment_names) if equipment_names else "None"
    mode_text = MODE_GUIDANCE.get(mode, "")

    return (
        f"{character.name} - Level {character.level} "
        f"{character.species.name.value.title()} {type(character).__name__}\n"
        f"HP: {character.current_hp}/{character.max_hp}\n\n"
        f"Ability Modifiers:\n{ability_lines}\n\n"
        f"Proficient Skills:\n{skill_lines}\n\n"
        f"Equipment: {equipment_summary}\n\n"
        f"Background:\n{character.background.to_prompt_context()}\n\n"
        f"Current Mode: {mode}\n"
        f"Mode Guidance: {mode_text}"
    )
