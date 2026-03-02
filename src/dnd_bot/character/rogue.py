"""Rogue class and subclasses.

The Rogue is a skilled combatant who relies on stealth, precision,
and cunning. The Thief subclass focuses on agility and quick hands.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from dnd_bot.dice import Dice

from .abilities import Ability
from .base import Character, ClassFeature, FeatureMechanic, FeatureMechanicType
from .resources import RestType


def get_sneak_attack_dice(level: int) -> int:
    """Calculate number of Sneak Attack dice for a given Rogue level.

    Sneak Attack starts at 1d6 at level 1 and gains an additional d6
    at every odd level (3, 5, 7, 9, 11, 13, 15, 17, 19).
    """
    return (level + 1) // 2


class Rogue(Character):
    """Rogue - skilled combatant relying on stealth and precision.

    Rogues excel at finding weaknesses and striking where it hurts.
    Their Sneak Attack deals massive damage to distracted foes.
    """

    class_type: Literal["rogue"] = Field(default="rogue")

    @property
    def hit_die(self) -> int:
        return 8

    @property
    def class_saving_throws(self) -> list[Ability]:
        return [Ability.DEXTERITY, Ability.INTELLIGENCE]

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Rogue features at current level."""
        all_features = [
            ClassFeature(
                name="Expertise",
                level=1,
                description=(
                    "Choose two of your skill proficiencies or one skill proficiency "
                    "and Thieves' Tools. Your proficiency bonus is doubled for any "
                    "ability check that uses either of the chosen proficiencies."
                ),
            ),
            ClassFeature(
                name="Sneak Attack",
                level=1,
                description=(
                    f"Once per turn, you can deal an extra {get_sneak_attack_dice(self.level)}d6 "
                    "damage to one creature you hit with an attack if you have advantage "
                    "on the attack roll, or if another enemy of the target is within "
                    "5 feet of it."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.PASSIVE,
                    dice_per_level="1d6",
                ),
            ),
            ClassFeature(
                name="Thieves' Cant",
                level=1,
                description=(
                    "You know Thieves' Cant, a secret mix of dialect, jargon, and code "
                    "that allows you to hide messages in seemingly normal conversation."
                ),
            ),
            ClassFeature(
                name="Weapon Mastery",
                level=1,
                description="You can use weapon mastery properties with Finesse and Light weapons.",
            ),
            ClassFeature(
                name="Cunning Action",
                level=2,
                description=(
                    "Your quick thinking and agility allow you to move and act quickly. "
                    "On your turn, you can take Dash, Disengage, or Hide as a Bonus Action."
                ),
            ),
            ClassFeature(
                name="Steady Aim",
                level=3,
                description=(
                    "As a Bonus Action, you give yourself advantage on your next attack "
                    "roll on the current turn. You can use this only if you haven't moved "
                    "during this turn, and after you use it, your speed is 0 until the "
                    "end of the current turn."
                ),
            ),
            ClassFeature(
                name="Uncanny Dodge",
                level=5,
                description=(
                    "When an attacker that you can see hits you with an attack, you can "
                    "use your Reaction to halve the attack's damage against you."
                ),
            ),
            ClassFeature(
                name="Evasion",
                level=7,
                description=(
                    "When you are subjected to an effect that allows you to make a "
                    "Dexterity saving throw to take only half damage, you instead take "
                    "no damage on a success and half damage on a failure."
                ),
            ),
            ClassFeature(
                name="Reliable Talent",
                level=11,
                description=(
                    "Whenever you make an ability check that uses a skill or tool you "
                    "have proficiency in, you can treat a d20 roll of 9 or lower as a 10."
                ),
            ),
            ClassFeature(
                name="Blindsense",
                level=14,
                description=(
                    "If you are able to hear, you are aware of the location of any "
                    "Hidden or Invisible creature within 10 feet of you."
                ),
            ),
            ClassFeature(
                name="Slippery Mind",
                level=15,
                description="You gain proficiency in Wisdom saving throws.",
            ),
            ClassFeature(
                name="Elusive",
                level=18,
                description=(
                    "No attack roll has advantage against you while you aren't "
                    "Incapacitated."
                ),
            ),
            ClassFeature(
                name="Stroke of Luck",
                level=20,
                description=(
                    "You have an uncanny knack for succeeding when you need to. If "
                    "your attack misses a target within range, you can turn the miss "
                    "into a hit. Alternatively, if you fail an ability check, you can "
                    "treat the d20 roll as a 20."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Stroke of Luck",
                    uses_per_rest=1,
                    recover_on=RestType.SHORT,
                ),
            ),
        ]
        return [f for f in all_features if f.level <= self.level]

    # Rogue-specific methods
    def get_sneak_attack_dice(self) -> int:
        """Get the number of Sneak Attack dice based on level.

        Returns:
            Number of d6s for Sneak Attack.
        """
        return get_sneak_attack_dice(self.level)

    def get_sneak_attack_damage_string(self) -> str:
        """Get the Sneak Attack damage as a dice string."""
        dice = self.get_sneak_attack_dice()
        return f"{dice}d6"

    def roll_weapon_damage(
        self, dice_notation: str, modifier: int, is_crit: bool = False, advantage: bool = False
    ) -> tuple[int, str]:
        """Roll weapon damage, adding Sneak Attack bonus dice when advantage is effective.

        Sneak Attack applies when the attacker has effective advantage (advantage=True).
        On a critical hit, Sneak Attack dice are also doubled per 5e rules.

        Parameters
        ----------
        dice_notation : str
            Weapon damage dice (e.g. "1d6").
        modifier : int
            Ability modifier added to the damage.
        is_crit : bool
            Whether the attack was a critical hit.
        advantage : bool
            Whether the attacker had effective advantage (advantage and not disadvantage).

        Returns
        -------
        tuple[int, str]
            (damage_total, notation_used) e.g. (12, "1d4 + 3d6")
        """
        weapon_total, weapon_notation = super().roll_weapon_damage(
            dice_notation, modifier, is_crit, advantage
        )
        if not advantage:
            return weapon_total, weapon_notation
        sa_count = self.get_sneak_attack_dice() * (2 if is_crit else 1)
        sa_total = Dice(count=sa_count, sides=6).roll().total
        return weapon_total + sa_total, f"{weapon_notation} + {sa_count}d6"

    def has_evasion(self) -> bool:
        """Check if the Rogue has Evasion (level 7+)."""
        return self.level >= 7

    def has_uncanny_dodge(self) -> bool:
        """Check if the Rogue has Uncanny Dodge (level 5+)."""
        return self.level >= 5

    def has_reliable_talent(self) -> bool:
        """Check if the Rogue has Reliable Talent (level 11+)."""
        return self.level >= 11

    def use_stroke_of_luck(self) -> bool:
        """Use Stroke of Luck to turn a miss into a hit or treat a roll as 20.

        Returns:
            True if successful, False if not available.
        """
        if self.level < 20:
            return False
        return self.resources.use_feature("Stroke of Luck")

    def can_use_stroke_of_luck(self) -> bool:
        """Check if Stroke of Luck is available."""
        return self.level >= 20 and self.resources.has_feature_available("Stroke of Luck")


class Thief(Rogue):
    """Thief - master of stealth and agility.

    The Thief archetype focuses on agility and stealth, with abilities
    that make them expert burglars and second-story workers.
    """

    class_type: Literal["thief"] = Field(default="thief")

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Thief features combined with Rogue features."""
        base_features = super().class_features

        subclass_features = [
            ClassFeature(
                name="Fast Hands",
                level=3,
                description=(
                    "You can use the Bonus Action granted by Cunning Action to make "
                    "a Dexterity (Sleight of Hand) check, use thieves' tools to disarm "
                    "a trap or pick a lock, or take the Use an Object action."
                ),
            ),
            ClassFeature(
                name="Second-Story Work",
                level=3,
                description=(
                    "You gain the ability to climb faster than normal; climbing no "
                    "longer costs you extra movement. In addition, when you make a "
                    "running jump, the distance you cover increases by a number of "
                    "feet equal to your Dexterity modifier."
                ),
            ),
            ClassFeature(
                name="Supreme Sneak",
                level=9,
                description=(
                    "You have advantage on a Dexterity (Stealth) check if you move "
                    "no more than half your speed on the same turn."
                ),
            ),
            ClassFeature(
                name="Use Magic Device",
                level=13,
                description=(
                    "You have learned enough about the workings of magic that you "
                    "can improvise the use of items even when they are not intended "
                    "for you. You ignore all class, species, and level requirements "
                    "on the use of magic items."
                ),
            ),
            ClassFeature(
                name="Thief's Reflexes",
                level=17,
                description=(
                    "You have become adept at laying ambushes and quickly escaping "
                    "danger. You can take two turns during the first round of any "
                    "combat. You take your first turn at your normal initiative and "
                    "your second turn at your initiative minus 10."
                ),
            ),
        ]

        combined = base_features + [f for f in subclass_features if f.level <= self.level]
        return combined

    def get_jump_bonus(self) -> int:
        """Get the bonus distance for running jumps (DEX modifier).

        Returns:
            Bonus feet for running jumps, or 0 if below level 3.
        """
        if self.level < 3:
            return 0
        return self.get_ability_modifier(Ability.DEXTERITY)

    def has_supreme_sneak(self) -> bool:
        """Check if the Thief has Supreme Sneak (level 9+)."""
        return self.level >= 9

    def has_use_magic_device(self) -> bool:
        """Check if the Thief can use any magic item (level 13+)."""
        return self.level >= 13

    def has_thiefs_reflexes(self) -> bool:
        """Check if the Thief has Thief's Reflexes (level 17+)."""
        return self.level >= 17
