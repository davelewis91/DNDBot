"""Barbarian class and subclasses.

The Barbarian is a primal warrior who channels rage for devastating
attacks and incredible resilience. The Berserker subclass emphasizes
relentless fury.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from dnd_bot.dice import Dice

from .abilities import Ability
from .base import Character, ClassFeature, FeatureMechanic, FeatureMechanicType
from .resources import RestType


def get_rage_uses(level: int) -> int:
    """Calculate number of Rage uses for a given Barbarian level."""
    if level >= 17:
        return 6
    if level >= 12:
        return 5
    if level >= 6:
        return 4
    if level >= 3:
        return 3
    return 2


def get_rage_damage_bonus(level: int) -> int:
    """Calculate Rage damage bonus for a given Barbarian level."""
    if level >= 16:
        return 4
    if level >= 9:
        return 3
    return 2


class Barbarian(Character):
    """Barbarian - primal warrior fueled by rage.

    Barbarians are fierce warriors who can enter a battle rage, granting
    them bonus damage and resistance to physical damage.
    """

    class_type: Literal["barbarian"] = Field(default="barbarian")
    is_raging: bool = False

    @property
    def hit_die(self) -> int:
        return 12

    @property
    def class_saving_throws(self) -> list[Ability]:
        return [Ability.STRENGTH, Ability.CONSTITUTION]

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Barbarian features at current level."""
        all_features = [
            ClassFeature(
                name="Rage",
                level=1,
                description=(
                    "In battle, you fight with primal ferocity. On your turn, you can "
                    "enter a Rage as a Bonus Action. While Raging, you gain resistance "
                    "to Bludgeoning, Piercing, and Slashing damage, and bonus damage "
                    "on Strength-based melee attacks."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.TOGGLE,
                    resource_name="Rage",
                    uses_per_rest=get_rage_uses(self.level),
                    recover_on=RestType.LONG,
                ),
            ),
            ClassFeature(
                name="Unarmored Defense",
                level=1,
                description=(
                    "While not wearing armor, your AC equals 10 + your Dexterity "
                    "modifier + your Constitution modifier."
                ),
            ),
            ClassFeature(
                name="Weapon Mastery",
                level=1,
                description="Use weapon mastery properties with proficient weapons.",
            ),
            ClassFeature(
                name="Danger Sense",
                level=2,
                description=(
                    "You gain an uncanny sense of when things nearby aren't as they "
                    "should be. You have advantage on Dexterity saving throws against "
                    "effects that you can see."
                ),
            ),
            ClassFeature(
                name="Reckless Attack",
                level=2,
                description=(
                    "When you make your first attack on your turn, you can decide to "
                    "attack recklessly. Doing so gives you advantage on melee attack "
                    "rolls using Strength during this turn, but attack rolls against "
                    "you have advantage until your next turn."
                ),
            ),
            ClassFeature(
                name="Primal Knowledge",
                level=2,
                description=(
                    "You gain proficiency in another skill from the Barbarian skill list."
                ),
            ),
            ClassFeature(
                name="Extra Attack",
                level=5,
                description="You can attack twice when you take the Attack action on your turn.",
            ),
            ClassFeature(
                name="Fast Movement",
                level=5,
                description=(
                    "Your speed increases by 10 feet while you aren't wearing Heavy Armor."
                ),
            ),
            ClassFeature(
                name="Feral Instinct",
                level=7,
                description=(
                    "Your instincts are so honed that you have advantage on Initiative "
                    "rolls. Additionally, if you are surprised at the beginning of "
                    "combat and aren't Incapacitated, you can act normally on your "
                    "first turn if you enter your Rage."
                ),
            ),
            ClassFeature(
                name="Instinctive Pounce",
                level=7,
                description=(
                    "When you enter your Rage, you can move up to half your Speed."
                ),
            ),
            ClassFeature(
                name="Brutal Critical",
                level=9,
                description=(
                    "When you score a critical hit with a melee attack, you roll one "
                    "additional weapon damage die."
                ),
            ),
            ClassFeature(
                name="Relentless Rage",
                level=11,
                description=(
                    "Your Rage can keep you fighting despite grievous wounds. If you "
                    "drop to 0 HP while Raging and don't die outright, you can make a "
                    "DC 10 Constitution save to drop to 1 HP instead."
                ),
            ),
            ClassFeature(
                name="Persistent Rage",
                level=15,
                description=(
                    "Your Rage ends early only if you fall Unconscious or choose to "
                    "end it."
                ),
            ),
            ClassFeature(
                name="Indomitable Might",
                level=18,
                description=(
                    "If your total for a Strength check or save is less than your "
                    "Strength score, you can use that score in place of the total."
                ),
            ),
            ClassFeature(
                name="Primal Champion",
                level=20,
                description=(
                    "Your Strength and Constitution scores increase by 4. Your maximum "
                    "for those scores is now 24."
                ),
            ),
        ]
        return [f for f in all_features if f.level <= self.level]

    def _register_class_resources(self) -> None:
        """Override to handle Rage's level-scaling uses."""
        # First, let the base class handle standard resources
        # But we need to handle Rage specially since it scales with level
        from .base import FeatureMechanicType

        resource_types = {FeatureMechanicType.RESOURCE, FeatureMechanicType.TOGGLE}

        for feature in self.class_features:
            if feature.mechanic is None or feature.mechanic.resource_name is None:
                continue
            if feature.mechanic.mechanic_type not in resource_types:
                continue

            key = feature.mechanic.resource_name.lower().replace(" ", "_")

            # Skip if already registered
            if key in self.resources.feature_uses:
                continue

            # Special handling for Rage
            if feature.mechanic.resource_name == "Rage":
                uses = get_rage_uses(self.level)
            else:
                uses = self._calculate_resource_uses(feature)

            self.resources.add_feature(
                name=feature.mechanic.resource_name,
                maximum=uses,
                recover_on=feature.mechanic.recover_on or RestType.LONG,
            )

    def calculate_armor_class(self) -> int:
        """Calculate AC with Barbarian Unarmored Defense.

        When not wearing armor: AC = 10 + DEX mod + CON mod.
        """
        dex_mod = self.get_ability_modifier(Ability.DEXTERITY)

        if self.equipment.armor_id is None:
            # Unarmored Defense: 10 + DEX + CON
            con_mod = self.get_ability_modifier(Ability.CONSTITUTION)
            base_ac = 10 + dex_mod + con_mod
        else:
            # Use standard armor calculation from base class
            base_ac = super().calculate_armor_class()
            # Remove shield bonus since we add it below
            if self.equipment.shield_equipped:
                base_ac -= 2

        # Add shield bonus
        if self.equipment.shield_equipped:
            base_ac += 2

        return base_ac

    # Barbarian-specific methods
    def start_rage(self) -> bool:
        """Enter a rage.

        While raging:
        - Bonus damage on Strength-based melee attacks
        - Resistance to bludgeoning, piercing, and slashing damage
        - Advantage on Strength checks and saving throws

        Returns:
            True if rage started, False if not available.
        """
        if not self.resources.use_feature("Rage"):
            return False
        self.is_raging = True
        return True

    def end_rage(self) -> None:
        """End the current rage."""
        self.is_raging = False

    def can_rage(self) -> bool:
        """Check if Rage is available."""
        return self.resources.has_feature_available("Rage")

    def get_rage_damage_bonus(self) -> int:
        """Get the current Rage damage bonus based on level."""
        return get_rage_damage_bonus(self.level)

    def get_rage_uses(self) -> int:
        """Get the total number of Rage uses per long rest."""
        return get_rage_uses(self.level)

    def get_extra_attack_count(self) -> int:
        """Get the number of attacks when taking the Attack action."""
        if self.level >= 5:
            return 2
        return 1

    def get_brutal_critical_dice(self) -> int:
        """Get number of extra dice on critical hits.

        Returns:
            1 at level 9+, 0 otherwise.
        """
        if self.level >= 9:
            return 1
        return 0

    def roll_weapon_damage(
        self, dice_notation: str, modifier: int, is_crit: bool = False, advantage: bool = False
    ) -> tuple[int, str]:
        """Roll weapon damage, adding Brutal Critical bonus dice on a critical hit.

        At level 9+, Brutal Critical adds one extra weapon damage die on a critical hit,
        on top of the standard critical hit doubling.

        Parameters
        ----------
        dice_notation : str
            Weapon damage dice (e.g. "1d12").
        modifier : int
            Ability modifier added to the damage.
        is_crit : bool
            Whether the attack was a critical hit.
        advantage : bool
            Forwarded to super(); unused by Barbarian directly.

        Returns
        -------
        tuple[int, str]
            (damage_total, notation_used) e.g. (15, "3d12")
        """
        if not is_crit:
            return super().roll_weapon_damage(dice_notation, modifier, is_crit, advantage)
        bonus = self.get_brutal_critical_dice()
        if bonus == 0:
            return super().roll_weapon_damage(dice_notation, modifier, is_crit, advantage)
        parsed = Dice.parse(dice_notation)
        count = parsed.count * 2 + bonus
        total = Dice(count=count, sides=parsed.sides).roll().total + modifier
        return total, f"{count}d{parsed.sides}"


class Berserker(Barbarian):
    """Berserker - path of unrelenting fury.

    The Path of the Berserker represents pure, unfettered rage and
    relentless assault.
    """

    class_type: Literal["berserker"] = Field(default="berserker")

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Berserker features combined with Barbarian features."""
        base_features = super().class_features

        subclass_features = [
            ClassFeature(
                name="Frenzy",
                level=3,
                description=(
                    "While Raging, you can choose to Frenzy. If you do, for the "
                    "duration of your Rage you can make a single melee weapon attack "
                    "as a Bonus Action on each of your turns after this one."
                ),
            ),
            ClassFeature(
                name="Mindless Rage",
                level=6,
                description=(
                    "You can't be Charmed or Frightened while Raging. If you are "
                    "Charmed or Frightened when you enter your Rage, the effect is "
                    "suspended for the duration of the Rage."
                ),
            ),
            ClassFeature(
                name="Intimidating Presence",
                level=10,
                description=(
                    "As an action, you can frighten someone with your menacing "
                    "presence. The target must make a Wisdom saving throw against "
                    "a DC of 8 + your proficiency bonus + your Charisma modifier."
                ),
            ),
            ClassFeature(
                name="Retaliation",
                level=14,
                description=(
                    "When you take damage from a creature within 5 feet of you, you "
                    "can use your Reaction to make a melee weapon attack against "
                    "that creature."
                ),
            ),
        ]

        combined = base_features + [f for f in subclass_features if f.level <= self.level]
        return combined

    def get_intimidating_presence_dc(self) -> int:
        """Get the DC for Intimidating Presence.

        Returns:
            DC (8 + proficiency + CHA mod), or 0 if below level 10.
        """
        if self.level < 10:
            return 0
        cha_mod = self.get_ability_modifier(Ability.CHARISMA)
        return 8 + self.proficiency_bonus + cha_mod
