from dnd_bot.character.abilities import Ability
from dnd_bot.character.base import FeatureMechanicType

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
        "You are free to explore and converse. Investigate clues, interact with the "
        "environment, talk to NPCs using your background and personality. Social skills "
        "(Persuasion, Deception, Insight) and exploration skills (Perception, Investigation) "
        "are both valuable here."
    ),
    "combat": (
        "You are in combat. Act tactically based on your class. "
        "Use class features when advantageous. Protect allies."
    ),
}

_ABILITY_ABBREV = {
    Ability.STRENGTH: "STR", Ability.DEXTERITY: "DEX", Ability.CONSTITUTION: "CON",
    Ability.INTELLIGENCE: "INT", Ability.WISDOM: "WIS", Ability.CHARISMA: "CHA",
}


def _build_class_abilities_context(character) -> str:
    """Build a formatted string of class abilities for the character context.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character

    Returns
    -------
    str
        Formatted class abilities section, or empty string if no features
    """
    resource_types = {FeatureMechanicType.RESOURCE, FeatureMechanicType.TOGGLE}
    lines = []

    for feature in character.class_features:
        mechanic = feature.mechanic
        if mechanic is not None and mechanic.mechanic_type in resource_types:
            resource = character.resources.get_feature(feature.name)
            if resource is not None:
                rest = resource.recover_on.value
                line = (
                    f"  {feature.name}: {feature.description} "
                    f"[{resource.current}/{resource.maximum} uses, {rest} rest]"
                )
                lines.append(line)
                continue
        lines.append(f"  {feature.name} (passive): {feature.description}")

    if not lines:
        return ""

    return "Class Abilities:\n" + "\n".join(lines)


def build_character_context(character, mode: str) -> str:
    """
    Build a character context string for the system prompt.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character
    mode : str
        Current game mode ("exploration" or "combat")

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

    base = (
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
    abilities_section = _build_class_abilities_context(character)
    if abilities_section:
        return base + "\n\n" + abilities_section
    return base
