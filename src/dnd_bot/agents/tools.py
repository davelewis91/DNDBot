from dataclasses import dataclass

from langchain_core.tools import tool

from dnd_bot.agents.class_tools import build_class_ability_tools
from dnd_bot.character.abilities import Ability
from dnd_bot.character.skills import Skill
from dnd_bot.items.weapons import get_weapon

# Tools available in each game mode. Class ability tools always go to combat.
EXPLORATION_TOOLS = {"check_status", "check_inventory", "skill_check", "ability_check",
                     "speak", "describe_action", "change_mode"}
COMBAT_TOOLS = {"check_status", "attack", "make_saving_throw", "skill_check", "speak",
                "change_mode"}


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
        status = f"{char.name}: HP {char.current_hp}/{char.max_hp} | Conditions: {conditions}"
        resources = [
            f"{r.name} [{r.current}/{r.maximum} remaining, {r.recover_on.value} rest]"
            for r in char.resources.feature_uses.values()
            if r.maximum > 0
        ]
        if resources:
            status += "\nResources: " + ", ".join(resources)
        return status

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
        weapon : Weapon name to use (e.g. "longsword", "my dagger"). Omit for unarmed.
        two_handed : Use two-handed grip for versatile weapons
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
        has_advantage = advantage and not disadvantage
        damage_total, dice_notation = char.roll_weapon_damage(dice, mod, is_crit, has_advantage)
        crit_prefix = "CRITICAL HIT! " if is_crit else ""
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
        target : Who you are addressing (optional)
        """
        if target:
            return f'[{char.name} → {target}] "{message}"'
        return f'[{char.name}] "{message}"'

    @tool
    def describe_action(action: str) -> str:
        """Describe a non-mechanical action (movement, gestures, expressions)."""
        return f"[{char.name}] {action}"

    tools = [
        check_status,
        check_inventory,
        skill_check,
        ability_check,
        attack,
        make_saving_throw,
        speak,
        describe_action,
    ]
    tools.extend(build_class_ability_tools(ctx))
    return tools
