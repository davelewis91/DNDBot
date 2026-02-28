from dataclasses import dataclass

from langchain_core.tools import tool

from dnd_bot.character.abilities import Ability
from dnd_bot.character.skills import Skill


@dataclass
class ToolContext:
    """Holds the character reference for tool closures."""

    character: object


def build_tools(ctx: ToolContext) -> list:
    """
    Build LangChain tools bound to a character instance.

    Parameters
    ----------
    ctx : ToolContext
        Context containing the character to bind tools to

    Returns
    -------
    list
        List of LangChain tool objects
    """
    char = ctx.character

    @tool
    def check_status() -> str:
        """Check current HP, conditions, and available resources."""
        conditions = ", ".join(str(c) for c in char.conditions) if char.conditions else "None"
        return f"{char.name}: HP {char.current_hp}/{char.max_hp} | Conditions: {conditions}"

    @tool
    def check_inventory() -> str:
        """List all carried equipment."""
        if not char.equipment:
            return "No equipment."
        return "\n".join(f"- {item.name}" for item in char.equipment)

    @tool
    def skill_check(skill: str, advantage: bool = False, disadvantage: bool = False) -> str:
        """
        Make a skill check using the character's proficiency and modifiers.

        Parameters
        ----------
        skill : Skill name in lowercase (e.g. "perception", "athletics", "sleight_of_hand")
        advantage : Roll with advantage (roll twice, take higher)
        disadvantage : Roll with disadvantage (roll twice, take lower)
        """
        try:
            skill_enum = Skill(skill.lower().replace(" ", "_"))
        except ValueError:
            valid = ", ".join(s.value for s in Skill)
            return f"Unknown skill '{skill}'. Valid skills: {valid}"
        total, die_roll = char.make_skill_check(skill_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"{skill.title()} check{adv_str}: {total} (rolled {die_roll} + {bonus:+d})"

    @tool
    def ability_check(ability: str, advantage: bool = False, disadvantage: bool = False) -> str:
        """
        Make a raw ability check.

        Parameters
        ----------
        ability : Ability name (strength/dexterity/constitution/intelligence/wisdom/charisma)
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            return (
                f"Unknown ability '{ability}'. "
                "Use: strength, dexterity, constitution, intelligence, wisdom, charisma"
            )
        total, die_roll = char.make_ability_check(ability_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"{ability.capitalize()} check{adv_str}: {total} (rolled {die_roll} + {bonus:+d})"

    @tool
    def attack(
        target: str,
        ability: str = "strength",
        is_proficient: bool = True,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> str:
        """
        Make an attack roll against a target.

        Parameters
        ----------
        target : Description of the target
        ability : Ability for the attack — "strength" for melee, "dexterity" for ranged/finesse
        is_proficient : Whether proficient with the weapon (default True)
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            ability_enum = Ability.STRENGTH
        total, die_roll = char.make_attack_roll(
            ability_enum, is_proficient, advantage, disadvantage
        )
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"Attack{adv_str} vs {target}: {total} to hit (rolled {die_roll} + {bonus:+d})"

    @tool
    def make_saving_throw(
        ability: str, advantage: bool = False, disadvantage: bool = False
    ) -> str:
        """
        Make a saving throw.

        Parameters
        ----------
        ability : Ability for the save (e.g. "dexterity", "constitution")
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            return f"Unknown ability '{ability}'."
        total, die_roll = char.make_saving_throw(ability_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return (
            f"{ability.capitalize()} saving throw{adv_str}: "
            f"{total} (rolled {die_roll} + {bonus:+d})"
        )

    @tool
    def speak(message: str, target: str = "") -> str:
        """
        Say something in character.

        Parameters
        ----------
        message : The words to speak
        target : Who you are addressing (optional)
        """
        if target:
            return f'[{char.name} → {target}] "{message}"'
        return f'[{char.name}] "{message}"'

    @tool
    def describe_action(action: str) -> str:
        """
        Describe a non-mechanical action (movement, gestures, expressions).

        Parameters
        ----------
        action : Description of what the character does
        """
        return f"[{char.name}] {action}"

    return [
        check_status,
        check_inventory,
        skill_check,
        ability_check,
        attack,
        make_saving_throw,
        speak,
        describe_action,
    ]
