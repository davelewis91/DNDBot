from dataclasses import dataclass

from langchain_core.tools import tool

from dnd_bot.character.abilities import Ability
from dnd_bot.character.skills import Skill
from dnd_bot.dice import Dice, roll
from dnd_bot.items.weapons import get_weapon


@dataclass
class ToolContext:
    """Holds the character reference for tool closures."""

    character: object


def _resolve_weapon(char, weapon_name: str):
    """Find a weapon in the character's equipment by partial name match."""
    weapon_lower = weapon_name.lower()
    for prefix in ("my ", "the ", "a "):
        weapon_lower = weapon_lower.removeprefix(prefix)
    for weapon_id in char.equipment.weapon_ids:
        if weapon_lower in weapon_id or weapon_id in weapon_lower:
            try:
                return get_weapon(weapon_id)
            except KeyError:
                pass
    return None


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
        names = char.equipment.item_names()
        if not names:
            return "No equipment."
        return "\n".join(f"- {name}" for name in names)

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
        weapon: str = "",
        two_handed: bool = False,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> str:
        """
        Make an attack roll and damage roll against a target.

        Parameters
        ----------
        target : Description of the target
        weapon : Weapon name to use (e.g. "longsword", "my dagger"). Omit for unarmed.
        two_handed : Use two-handed grip for versatile weapons
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        weapon_obj = None
        if weapon:
            weapon_obj = _resolve_weapon(char, weapon)
            if weapon_obj is None:
                equipped = ", ".join(char.equipment.weapon_ids) or "none"
                return f"No weapon matching '{weapon}' found. Equipped: {equipped}"

        ability = char.get_attack_ability(weapon_obj)
        total, die_roll = char.make_attack_roll(ability, True, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        is_crit = char.is_critical_hit(die_roll)

        if weapon_obj is None:
            damage_total, formula = char.roll_unarmed_damage()
            crit_prefix = "CRITICAL HIT! " if is_crit else ""
            return (
                f"{crit_prefix}Unarmed strike{adv_str} vs {target}: "
                f"{total} to hit (rolled {die_roll} + {bonus:+d})\n"
                f"  Damage: {damage_total} bludgeoning ({formula})"
            )

        dice = (
            weapon_obj.versatile_dice if two_handed and weapon_obj.versatile_dice
            else weapon_obj.damage_dice
        )
        mod = char.get_ability_modifier(ability)
        if is_crit:
            parsed = Dice.parse(dice)
            damage_total = Dice(count=parsed.count * 2, sides=parsed.sides).roll().total + mod
            crit_prefix = "CRITICAL HIT! "
            dice_notation = f"{parsed.count * 2}d{parsed.sides}"
        else:
            damage_total = roll(dice).total + mod
            crit_prefix = ""
            dice_notation = dice
        return (
            f"{crit_prefix}Attack with {weapon_obj.name}{adv_str} vs {target}: "
            f"{total} to hit (rolled {die_roll} + {bonus:+d})\n"
            f"  Damage: {damage_total} {weapon_obj.damage_type.value} ({dice_notation} + {mod:+d})"
        )

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
