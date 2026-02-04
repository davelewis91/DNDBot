"""Fighter class and subclasses.

The Fighter is a martial weapons master with abilities like Second Wind,
Action Surge, and Extra Attack. The Champion subclass specializes in
critical hits.
"""

from __future__ import annotations

import random
from typing import Literal

from pydantic import Field

from .abilities import Ability
from .base import Character, ClassFeature, FeatureMechanic, FeatureMechanicType
from .resources import RestType


class Fighter(Character):
    """Fighter - martial weapons master.

    Fighters are versatile combatants with access to all weapons and armor.
    They gain Second Wind at level 1 and Action Surge at level 2.
    """

    class_type: Literal["fighter"] = Field(default="fighter")

    @property
    def hit_die(self) -> int:
        return 10

    @property
    def class_saving_throws(self) -> list[Ability]:
        return [Ability.STRENGTH, Ability.CONSTITUTION]

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Fighter features at current level."""
        all_features = [
            ClassFeature(
                name="Fighting Style",
                level=1,
                description="You adopt a particular style of fighting as your specialty.",
            ),
            ClassFeature(
                name="Second Wind",
                level=1,
                description=(
                    "You have a limited well of stamina. On your turn, you can use a "
                    "Bonus Action to regain Hit Points equal to 1d10 plus your Fighter level."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Second Wind",
                    uses_per_rest=1,
                    recover_on=RestType.SHORT,
                    dice="1d10",
                ),
            ),
            ClassFeature(
                name="Weapon Mastery",
                level=1,
                description="Use weapon mastery properties with proficient weapons.",
            ),
            ClassFeature(
                name="Action Surge",
                level=2,
                description=(
                    "You can push yourself beyond your normal limits. On your turn, you "
                    "can take one additional action."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Action Surge",
                    uses_per_rest=1,
                    recover_on=RestType.SHORT,
                ),
            ),
            ClassFeature(
                name="Tactical Mind",
                level=2,
                description=(
                    "When you fail an ability check, you can expend a use of Second Wind "
                    "to add 1d10 to the roll."
                ),
            ),
            ClassFeature(
                name="Extra Attack",
                level=5,
                description="You can attack twice when you take the Attack action on your turn.",
            ),
            ClassFeature(
                name="Tactical Shift",
                level=5,
                description=(
                    "When you use Second Wind, you can move up to half your Speed without "
                    "provoking Opportunity Attacks."
                ),
            ),
            ClassFeature(
                name="Indomitable",
                level=9,
                description=(
                    "You can reroll a saving throw that you fail. If you do so, you must "
                    "use the new roll."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Indomitable",
                    uses_per_rest=1,
                    recover_on=RestType.LONG,
                ),
            ),
            ClassFeature(
                name="Extra Attack (2)",
                level=11,
                description="You can attack three times when you take the Attack action.",
            ),
            ClassFeature(
                name="Studied Attacks",
                level=13,
                description=(
                    "If you miss a creature with an attack roll, you have advantage on "
                    "your next attack roll against that creature before the end of your "
                    "next turn."
                ),
            ),
            ClassFeature(
                name="Extra Attack (3)",
                level=20,
                description="You can attack four times when you take the Attack action.",
            ),
        ]
        return [f for f in all_features if f.level <= self.level]

    # Fighter-specific methods
    def use_second_wind(self) -> int:
        """Use Second Wind to heal 1d10 + level HP.

        Returns:
            HP healed (0 if resource not available).
        """
        if not self.resources.use_feature("Second Wind"):
            return 0

        roll = random.randint(1, 10)
        healing = roll + self.level
        return self.heal(healing)

    def can_use_second_wind(self) -> bool:
        """Check if Second Wind is available."""
        return self.resources.has_feature_available("Second Wind")

    def use_action_surge(self) -> bool:
        """Use Action Surge to gain an additional action.

        Returns:
            True if successful, False if not available.
        """
        if self.level < 2:
            return False
        return self.resources.use_feature("Action Surge")

    def can_use_action_surge(self) -> bool:
        """Check if Action Surge is available."""
        return self.level >= 2 and self.resources.has_feature_available("Action Surge")

    def use_indomitable(self) -> bool:
        """Use Indomitable to reroll a failed saving throw.

        Returns:
            True if successful, False if not available.
        """
        if self.level < 9:
            return False
        return self.resources.use_feature("Indomitable")

    def can_use_indomitable(self) -> bool:
        """Check if Indomitable is available."""
        return self.level >= 9 and self.resources.has_feature_available("Indomitable")

    def get_extra_attack_count(self) -> int:
        """Get the number of attacks when taking the Attack action.

        Returns:
            Number of attacks (1 at low levels, up to 4 at level 20).
        """
        if self.level >= 20:
            return 4
        if self.level >= 11:
            return 3
        if self.level >= 5:
            return 2
        return 1


class Champion(Fighter):
    """Champion - critical hit specialist.

    The Champion Fighter subclass focuses on raw physical power and
    improved critical hits.
    """

    class_type: Literal["champion"] = Field(default="champion")

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Champion features combined with Fighter features."""
        base_features = super().class_features

        subclass_features = [
            ClassFeature(
                name="Improved Critical",
                level=3,
                description=(
                    "Your weapon attacks score a critical hit on a roll of 19 or 20 "
                    "on the d20."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.PASSIVE,
                    extra_data={"critical_range": [19, 20]},
                ),
            ),
            ClassFeature(
                name="Remarkable Athlete",
                level=7,
                description=(
                    "You can add half your proficiency bonus (rounded up) to any "
                    "Strength, Dexterity, or Constitution check you make that doesn't "
                    "already use your proficiency bonus."
                ),
            ),
            ClassFeature(
                name="Additional Fighting Style",
                level=10,
                description="You can choose a second Fighting Style option.",
            ),
            ClassFeature(
                name="Superior Critical",
                level=15,
                description=(
                    "Your weapon attacks score a critical hit on a roll of 18-20 "
                    "on the d20."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.PASSIVE,
                    extra_data={"critical_range": [18, 19, 20]},
                ),
            ),
            ClassFeature(
                name="Survivor",
                level=18,
                description=(
                    "At the start of each of your turns, you regain hit points equal "
                    "to 5 + your Constitution modifier if you have no more than half "
                    "of your hit points left."
                ),
            ),
        ]

        combined = base_features + [f for f in subclass_features if f.level <= self.level]
        return combined

    def get_critical_range(self) -> list[int]:
        """Get the range of d20 rolls that count as critical hits.

        Returns:
            [20] at low levels, [19, 20] at level 3+, [18, 19, 20] at level 15+.
        """
        if self.level >= 15:
            return [18, 19, 20]
        if self.level >= 3:
            return [19, 20]
        return [20]

    def get_remarkable_athlete_bonus(self) -> int:
        """Get the Remarkable Athlete bonus (half proficiency rounded up).

        Returns:
            Bonus to add to STR/DEX/CON checks, or 0 if below level 7.
        """
        if self.level < 7:
            return 0
        return (self.proficiency_bonus + 1) // 2

    def survivor_heal_amount(self) -> int:
        """Calculate Survivor healing amount.

        Returns:
            Healing amount (5 + CON mod), or 0 if below level 18.
        """
        if self.level < 18:
            return 0
        con_mod = self.get_ability_modifier(Ability.CONSTITUTION)
        return 5 + con_mod

    def should_trigger_survivor(self) -> bool:
        """Check if Survivor should trigger (at or below half HP).

        Returns:
            True if level 18+ and at or below half HP.
        """
        if self.level < 18:
            return False
        return self.current_hp <= self.max_hp // 2
