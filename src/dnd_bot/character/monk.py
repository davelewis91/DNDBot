"""Monk class and subclasses.

The Monk is a martial artist who harnesses the power of Focus (ki) for
supernatural feats. The Way of the Open Hand focuses on unarmed combat.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .abilities import Ability
from .base import Character, ClassFeature, FeatureMechanic, FeatureMechanicType
from .resources import RestType


def get_martial_arts_die(level: int) -> str:
    """Calculate Martial Arts die for a given Monk level."""
    if level >= 17:
        return "1d12"
    if level >= 11:
        return "1d10"
    if level >= 5:
        return "1d8"
    return "1d6"


class Monk(Character):
    """Monk - martial artist harnessing inner Focus.

    Monks are masters of martial arts who channel their Focus (ki) energy
    to perform supernatural feats of speed and power.
    """

    class_type: Literal["monk"] = Field(default="monk")

    @property
    def hit_die(self) -> int:
        return 8

    @property
    def class_saving_throws(self) -> list[Ability]:
        return [Ability.STRENGTH, Ability.DEXTERITY]

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Monk features at current level."""
        all_features = [
            ClassFeature(
                name="Martial Arts",
                level=1,
                description=(
                    f"Your practice of martial arts gives you mastery of combat styles "
                    f"that use your Martial Arts die ({get_martial_arts_die(self.level)}). "
                    "You can use Dexterity instead of Strength for unarmed strikes and "
                    "Monk weapons."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.PASSIVE,
                    dice=get_martial_arts_die(self.level),
                ),
            ),
            ClassFeature(
                name="Unarmored Defense",
                level=1,
                description=(
                    "While not wearing armor and not wielding a Shield, your AC equals "
                    "10 + your Dexterity modifier + your Wisdom modifier."
                ),
            ),
            ClassFeature(
                name="Focus",
                level=2,
                description=(
                    "Your training allows you to harness the mystic energy of Focus. "
                    f"You have {self.level} Focus Points that fuel various Focus features."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Focus Points",
                    uses_per_rest_formula="level",
                    recover_on=RestType.SHORT,
                ),
            ),
            ClassFeature(
                name="Flurry of Blows",
                level=2,
                description=(
                    "Immediately after you take the Attack action, you can spend 1 "
                    "Focus Point to make two Unarmed Strikes as a Bonus Action."
                ),
            ),
            ClassFeature(
                name="Patient Defense",
                level=2,
                description=(
                    "You can take the Disengage action as a Bonus Action. Alternatively, "
                    "you can spend 1 Focus Point to take both the Disengage and Dodge "
                    "actions as a Bonus Action."
                ),
            ),
            ClassFeature(
                name="Step of the Wind",
                level=2,
                description=(
                    "You can take the Dash action as a Bonus Action. Alternatively, you "
                    "can spend 1 Focus Point to take both the Dash and Disengage actions "
                    "as a Bonus Action, and your jump distance is doubled for the turn."
                ),
            ),
            ClassFeature(
                name="Uncanny Metabolism",
                level=2,
                description=(
                    "When you roll Initiative, you can regain all expended Focus Points. "
                    "You can use this feature only if you have 0 Focus Points."
                ),
            ),
            ClassFeature(
                name="Deflect Missiles",
                level=3,
                description=(
                    "You can use your Reaction to deflect or catch the missile when you "
                    "are hit by a ranged weapon attack. The damage is reduced by 1d10 + "
                    "your Dexterity modifier + your Monk level."
                ),
            ),
            ClassFeature(
                name="Slow Fall",
                level=4,
                description=(
                    "You can use your Reaction when you fall to reduce any Falling "
                    "damage you take by an amount equal to five times your Monk level."
                ),
            ),
            ClassFeature(
                name="Extra Attack",
                level=5,
                description="You can attack twice when you take the Attack action on your turn.",
            ),
            ClassFeature(
                name="Stunning Strike",
                level=5,
                description=(
                    "Once per turn when you hit a creature with a Monk weapon or an "
                    "Unarmed Strike, you can spend 1 Focus Point to attempt a stunning "
                    "strike. The target must succeed on a Constitution saving throw or "
                    "be Stunned until the start of your next turn."
                ),
            ),
            ClassFeature(
                name="Empowered Strikes",
                level=6,
                description=(
                    "Your Unarmed Strikes count as magical for the purpose of overcoming "
                    "resistance and immunity to nonmagical attacks and damage."
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
                name="Stillness of Mind",
                level=7,
                description=(
                    "You can use an action to end one effect on yourself that is causing "
                    "you to be Charmed or Frightened."
                ),
            ),
            ClassFeature(
                name="Purity of Body",
                level=10,
                description="You are immune to disease and poison.",
            ),
            ClassFeature(
                name="Tongue of the Sun and Moon",
                level=13,
                description=(
                    "You learn to touch the Focus of other minds so that you understand "
                    "all spoken languages. Moreover, any creature that can understand a "
                    "language can understand what you say."
                ),
            ),
            ClassFeature(
                name="Diamond Soul",
                level=14,
                description=(
                    "You gain proficiency in all saving throws. Additionally, when you "
                    "fail a saving throw, you can spend 1 Focus Point to reroll it."
                ),
            ),
            ClassFeature(
                name="Timeless Body",
                level=15,
                description=(
                    "Your Focus sustains you so that you suffer none of the frailty of "
                    "old age. You also no longer need food or water."
                ),
            ),
            ClassFeature(
                name="Superior Defense",
                level=18,
                description=(
                    "If you have 3 or more Focus Points remaining, you have resistance "
                    "to all damage except Force damage."
                ),
            ),
            ClassFeature(
                name="Perfect Self",
                level=20,
                description=(
                    "When you roll Initiative and have fewer than 4 Focus Points, you "
                    "regain Focus Points until you have 4."
                ),
            ),
        ]
        return [f for f in all_features if f.level <= self.level]

    def calculate_armor_class(self) -> int:
        """Calculate AC with Monk Unarmored Defense.

        When not wearing armor and not using a shield: AC = 10 + DEX mod + WIS mod.
        """
        dex_mod = self.get_ability_modifier(Ability.DEXTERITY)

        if self.equipment.armor_id is None and not self.equipment.shield_equipped:
            # Unarmored Defense: 10 + DEX + WIS
            wis_mod = self.get_ability_modifier(Ability.WISDOM)
            return 10 + dex_mod + wis_mod
        else:
            # Use standard armor calculation from base class
            return super().calculate_armor_class()

    # Monk-specific methods
    def use_focus_points(self, amount: int = 1) -> bool:
        """Spend Focus Points.

        Used for Flurry of Blows, Patient Defense, Step of the Wind, etc.

        Parameters:
            amount: Number of Focus Points to spend.

        Returns:
            True if successful, False if not available.
        """
        if self.level < 2:
            return False
        return self.resources.use_feature("Focus Points", amount)

    def get_focus_points(self) -> int:
        """Get current Focus Points remaining."""
        resource = self.resources.get_feature("Focus Points")
        return resource.current if resource else 0

    def get_max_focus_points(self) -> int:
        """Get maximum Focus Points (equals Monk level)."""
        if self.level < 2:
            return 0
        return self.level

    def get_martial_arts_die(self) -> str:
        """Get the current Martial Arts die based on level."""
        return get_martial_arts_die(self.level)

    def get_stunning_strike_dc(self) -> int:
        """Get the DC for Stunning Strike.

        Returns:
            DC (8 + proficiency + WIS mod), or 0 if below level 5.
        """
        if self.level < 5:
            return 0
        wis_mod = self.get_ability_modifier(Ability.WISDOM)
        return 8 + self.proficiency_bonus + wis_mod

    def get_deflect_missiles_reduction(self) -> str:
        """Get the damage reduction formula for Deflect Missiles.

        Returns:
            Damage reduction string, or empty if below level 3.
        """
        if self.level < 3:
            return ""
        dex_mod = self.get_ability_modifier(Ability.DEXTERITY)
        return f"1d10 + {dex_mod} + {self.level}"

    def get_slow_fall_reduction(self) -> int:
        """Get the falling damage reduction amount.

        Returns:
            Damage reduction (5 × Monk level), or 0 if below level 4.
        """
        if self.level < 4:
            return 0
        return 5 * self.level

    def has_evasion(self) -> bool:
        """Check if the Monk has Evasion (level 7+)."""
        return self.level >= 7

    def get_extra_attack_count(self) -> int:
        """Get the number of attacks when taking the Attack action."""
        if self.level >= 5:
            return 2
        return 1


class OpenHand(Monk):
    """Way of the Open Hand - master of unarmed combat.

    The Way of the Open Hand monks are the ultimate masters of martial
    arts combat, whether armed or unarmed.
    """

    class_type: Literal["openhand"] = Field(default="openhand")

    @property
    def class_features(self) -> list[ClassFeature]:
        """Get Open Hand features combined with Monk features."""
        base_features = super().class_features

        subclass_features = [
            ClassFeature(
                name="Open Hand Technique",
                level=3,
                description=(
                    "Whenever you hit a creature with an attack granted by Flurry of "
                    "Blows, you can impose one of the following effects: knock the "
                    "target Prone (DEX save), push the target 15 feet (STR save), or "
                    "prevent the target from taking Reactions until the end of your "
                    "next turn (no save)."
                ),
            ),
            ClassFeature(
                name="Wholeness of Body",
                level=6,
                description=(
                    "You can heal yourself. As a Bonus Action, you can roll your "
                    "Martial Arts die. You regain a number of Hit Points equal to "
                    "the number rolled plus your Wisdom modifier."
                ),
                mechanic=FeatureMechanic(
                    mechanic_type=FeatureMechanicType.RESOURCE,
                    resource_name="Wholeness of Body",
                    uses_per_rest=1,
                    recover_on=RestType.LONG,
                ),
            ),
            ClassFeature(
                name="Fleet Step",
                level=11,
                description=(
                    "You can take the Disengage action as part of your Flurry of Blows "
                    "without spending a Focus Point."
                ),
            ),
            ClassFeature(
                name="Quivering Palm",
                level=17,
                description=(
                    "You gain the ability to set up lethal vibrations in someone's body. "
                    "When you hit a creature with an Unarmed Strike, you can spend 4 "
                    "Focus Points to start these imperceptible vibrations. Within a "
                    "number of days equal to your Monk level, you can use an Action to "
                    "end the vibrations, which requires the creature to make a "
                    "Constitution save or drop to 0 HP."
                ),
            ),
        ]

        combined = base_features + [f for f in subclass_features if f.level <= self.level]
        return combined

    def get_open_hand_technique_dc(self) -> int:
        """Get the DC for Open Hand Technique effects.

        Returns:
            DC (8 + proficiency + WIS mod), or 0 if below level 3.
        """
        if self.level < 3:
            return 0
        wis_mod = self.get_ability_modifier(Ability.WISDOM)
        return 8 + self.proficiency_bonus + wis_mod

    def use_wholeness_of_body(self) -> int:
        """Use Wholeness of Body to heal.

        Returns:
            HP healed (0 if not available or below level 6).
        """
        if self.level < 6:
            return 0
        if not self.resources.use_feature("Wholeness of Body"):
            return 0

        import random

        # Roll Martial Arts die + WIS mod
        die_size = int(self.get_martial_arts_die()[2:])  # Extract number from "1d6"
        roll = random.randint(1, die_size)
        wis_mod = self.get_ability_modifier(Ability.WISDOM)
        healing = roll + wis_mod
        return self.heal(max(1, healing))

    def can_use_wholeness_of_body(self) -> bool:
        """Check if Wholeness of Body is available."""
        return self.level >= 6 and self.resources.has_feature_available("Wholeness of Body")

    def get_quivering_palm_dc(self) -> int:
        """Get the DC for Quivering Palm.

        Returns:
            DC (8 + proficiency + WIS mod), or 0 if below level 17.
        """
        if self.level < 17:
            return 0
        wis_mod = self.get_ability_modifier(Ability.WISDOM)
        return 8 + self.proficiency_bonus + wis_mod
