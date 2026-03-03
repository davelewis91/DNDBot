"""Class-specific ability tools for D&D character agents.

Provides LangChain tool factories for each character class, building
tools that expose class features as callable agent actions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

from dnd_bot.character import Barbarian, Fighter, Monk, OpenHand, Rogue
from dnd_bot.character.skills import Skill

if TYPE_CHECKING:
    from .tools import ToolContext


def build_class_ability_tools(ctx: ToolContext) -> list:
    """
    Build class-specific LangChain tools for the given character.

    Parameters
    ----------
    ctx : ToolContext
        Context containing the character to build tools for.

    Returns
    -------
    list
        List of LangChain tool objects for the character's class abilities.
    """
    char = ctx.character
    tools = []
    if isinstance(char, Fighter):
        tools.extend(_build_fighter_tools(char))
    if isinstance(char, Barbarian):
        tools.extend(_build_barbarian_tools(char))
    if isinstance(char, Monk):
        tools.extend(_build_monk_tools(char))
    if isinstance(char, Rogue):
        tools.extend(_build_rogue_tools(char))
    return tools


def _build_fighter_tools(char: Fighter) -> list:
    """
    Build Fighter-specific tools.

    Parameters
    ----------
    char : Fighter
        The Fighter character to bind tools to.

    Returns
    -------
    list
        List of Fighter tools: second_wind, action_surge.
    """

    @tool
    def second_wind() -> str:
        """Use Second Wind to heal 1d10 + Fighter level HP as a Bonus Action."""
        healed = char.use_second_wind()
        if healed == 0:
            return "Second Wind not available (no uses remaining)."
        return f"Second Wind: healed {healed} HP. HP now {char.current_hp}/{char.max_hp}."

    @tool
    def action_surge() -> str:
        """Use Action Surge to gain one additional action this turn."""
        if not char.use_action_surge():
            return "Action Surge not available."
        return "Action Surge used! You gain one additional action this turn."

    return [second_wind, action_surge]


def _build_barbarian_tools(char: Barbarian) -> list:
    """
    Build Barbarian-specific tools.

    Parameters
    ----------
    char : Barbarian
        The Barbarian character to bind tools to.

    Returns
    -------
    list
        List of Barbarian tools: toggle_rage.
    """

    @tool
    def toggle_rage() -> str:
        """Start or end Rage. While raging: resistance to physical damage and bonus STR damage."""
        if char.is_raging:
            char.end_rage()
            return "Rage ended."
        started = char.start_rage()
        if started:
            return (
                "Rage started! You have resistance to bludgeoning/piercing/slashing "
                "and bonus damage on STR attacks."
            )
        return "Rage not available (no uses remaining)."

    return [toggle_rage]


def _build_monk_tools(char: Monk) -> list:
    """
    Build Monk-specific tools.

    Parameters
    ----------
    char : Monk
        The Monk character to bind tools to.

    Returns
    -------
    list
        List of Monk tools: flurry_of_blows, patient_defense, step_of_the_wind,
        stunning_strike, and optionally wholeness_of_body for OpenHand monks.
    """

    @tool
    def flurry_of_blows(target: str) -> str:
        """
        Spend 1 Focus Point to make two unarmed strikes as a Bonus Action.

        Parameters
        ----------
        target : The target of the unarmed strikes.
        """
        if not char.use_focus_points(1):
            return "Flurry of Blows not available (insufficient Focus Points)."
        ability = char.get_attack_ability(None)
        total1, die_roll1 = char.make_attack_roll(ability, True)
        bonus1 = total1 - die_roll1
        damage1, formula1 = char.roll_unarmed_damage()
        total2, die_roll2 = char.make_attack_roll(ability, True)
        bonus2 = total2 - die_roll2
        damage2, formula2 = char.roll_unarmed_damage()
        return (
            f"Flurry of Blows vs {target}:\n"
            f"  Strike 1: {total1} to hit (rolled {die_roll1} + {bonus1:+d}) — "
            f"{damage1} damage ({formula1})\n"
            f"  Strike 2: {total2} to hit (rolled {die_roll2} + {bonus2:+d}) — "
            f"{damage2} damage ({formula2})"
        )

    @tool
    def patient_defense() -> str:
        """Spend 1 Focus Point to take both the Disengage and Dodge actions as a Bonus Action."""
        if not char.use_focus_points(1):
            return "Patient Defense not available (insufficient Focus Points)."
        return (
            "Patient Defense activated. You take the Disengage and Dodge actions as a Bonus Action."
        )

    @tool
    def step_of_the_wind(action: str) -> str:
        """
        Spend 1 Focus Point to Dash or Disengage as a Bonus Action with doubled jump distance.

        Parameters
        ----------
        action : The action to take — "dash" or "disengage".
        """
        if not char.use_focus_points(1):
            return "Step of the Wind not available (insufficient Focus Points)."
        action_lower = action.lower()
        if action_lower in ("dash", "disengage"):
            return (
                "Step of the Wind: You Dash and Disengage as a Bonus Action. "
                "Your jump distance is doubled for the turn."
            )
        return f"Unknown action '{action}' for Step of the Wind. Use: dash, disengage"

    @tool
    def stunning_strike(target: str) -> str:
        """
        Spend 1 Focus Point to attempt a Stunning Strike. Target must make a CON save or be Stunned.

        Parameters
        ----------
        target : The target of the stunning strike.
        """
        if not char.use_focus_points(1):
            return "Stunning Strike not available (insufficient Focus Points)."
        dc = char.get_stunning_strike_dc()
        if dc == 0:
            return "Stunning Strike requires level 5 (DC not yet available)."
        return (
            f"Stunning Strike used on {target}! DC {dc} CON save or Stunned until start of "
            "your next turn. (Condition tracking deferred to DM.)"
        )

    tools = [flurry_of_blows, patient_defense, step_of_the_wind, stunning_strike]

    if isinstance(char, OpenHand):

        @tool
        def wholeness_of_body() -> str:
            """Use Wholeness of Body to heal yourself with your Martial Arts die + WIS mod."""
            healed = char.use_wholeness_of_body()
            if healed == 0:
                return "Wholeness of Body not available."
            return (
                f"Wholeness of Body: healed {healed} HP. "
                f"HP now {char.current_hp}/{char.max_hp}."
            )

        tools.append(wholeness_of_body)

    return tools


def _build_rogue_tools(char: Rogue) -> list:
    """
    Build Rogue-specific tools.

    Parameters
    ----------
    char : Rogue
        The Rogue character to bind tools to.

    Returns
    -------
    list
        List of Rogue tools: cunning_action.
    """

    @tool
    def cunning_action(action: str) -> str:
        """
        Use Cunning Action to Dash, Disengage, or Hide as a Bonus Action.

        Parameters
        ----------
        action : The bonus action to take — "dash", "disengage", or "hide".
        """
        action_lower = action.lower()
        if action_lower == "hide":
            total, die_roll = char.make_skill_check(Skill.STEALTH)
            bonus = total - die_roll
            return (
                f"Cunning Action (Hide): Stealth check {total} "
                f"(rolled {die_roll} + {bonus:+d})."
            )
        if action_lower in ("dash", "disengage"):
            return f"Cunning Action ({action.title()}): {action.title()} taken as a Bonus Action."
        return f"Unknown cunning action '{action}'. Use: dash, disengage, hide"

    return [cunning_action]
