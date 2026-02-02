"""Subclass definitions for D&D 5e (2024 edition).

Each class gains a subclass at level 3. Subclasses provide additional
features at specific levels that enhance or specialize the base class.
"""

from pydantic import BaseModel, Field

from .classes import (
    ClassFeature,
    ClassName,
    FeatureMechanic,
    FeatureMechanicType,
    RestType,
)


class Subclass(BaseModel):
    """A character subclass that provides specialized features."""

    id: str = Field(description="Unique identifier for the subclass")
    name: str = Field(description="Display name of the subclass")
    parent_class: ClassName = Field(description="The class this subclass belongs to")
    description: str = Field(description="Flavor text describing the subclass")
    features: list[ClassFeature] = Field(
        default_factory=list,
        description="Features granted by this subclass",
    )

    def get_features_at_level(self, level: int) -> list[ClassFeature]:
        """Get all subclass features at or below the given level."""
        return [f for f in self.features if f.level <= level]

    def get_feature_by_name(self, name: str) -> ClassFeature | None:
        """Get a specific feature by name."""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None


# =============================================================================
# Fighter Subclasses
# =============================================================================

CHAMPION = Subclass(
    id="champion",
    name="Champion",
    parent_class=ClassName.FIGHTER,
    description=(
        "A Champion focuses on the development of raw physical power honed to deadly "
        "perfection. Those who model themselves on this archetype combine rigorous "
        "training with physical excellence to deal devastating blows."
    ),
    features=[
        ClassFeature(
            name="Improved Critical",
            level=3,
            description=(
                "Your weapon attacks score a critical hit on a roll of 19 or 20."
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
                "You can add half your proficiency bonus (round up) to any Strength, "
                "Dexterity, or Constitution check you make that doesn't already use "
                "your proficiency bonus. In addition, when you make a running long jump, "
                "the distance you can cover increases by a number of feet equal to your "
                "Strength modifier."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"half_proficiency_to": ["strength", "dexterity", "constitution"]},
            ),
        ),
        ClassFeature(
            name="Additional Fighting Style",
            level=10,
            description=(
                "You can choose a second option from the Fighting Style feature."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Superior Critical",
            level=15,
            description=(
                "Your weapon attacks score a critical hit on a roll of 18-20."
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
                "You attain the pinnacle of resilience in battle. At the start of each "
                "of your turns, you regain hit points equal to 5 + your Constitution "
                "modifier if you have no more than half of your hit points left. You "
                "don't gain this benefit if you have 0 hit points."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"heal_per_turn": True, "base_heal": 5, "add_con_mod": True},
            ),
        ),
    ],
)


# =============================================================================
# Rogue Subclasses
# =============================================================================

THIEF = Subclass(
    id="thief",
    name="Thief",
    parent_class=ClassName.ROGUE,
    description=(
        "You hone your skills in the larcenous arts. Burglars, bandits, cutpurses, "
        "and other criminals typically follow this archetype, but so do rogues who "
        "prefer to think of themselves as professional treasure seekers."
    ),
    features=[
        ClassFeature(
            name="Fast Hands",
            level=3,
            description=(
                "You can use the Bonus Action granted by Cunning Action to make a "
                "Dexterity (Sleight of Hand) check, use your thieves' tools to disarm "
                "a trap or open a lock, or take the Use an Object action."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"bonus_actions": ["Sleight of Hand", "Thieves' Tools", "Use Object"]},
            ),
        ),
        ClassFeature(
            name="Second-Story Work",
            level=3,
            description=(
                "You gain the ability to climb faster than normal; climbing no longer "
                "costs you extra movement. In addition, when you make a running jump, "
                "the distance you cover increases by a number of feet equal to your "
                "Dexterity modifier."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"climb_speed": "normal", "jump_bonus": "dexterity"},
            ),
        ),
        ClassFeature(
            name="Supreme Sneak",
            level=9,
            description=(
                "You have advantage on a Dexterity (Stealth) check if you move no more "
                "than half your speed on the same turn."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"advantage_on_stealth": True, "requires_half_speed": True},
            ),
        ),
        ClassFeature(
            name="Use Magic Device",
            level=13,
            description=(
                "You have learned enough about the workings of magic that you can "
                "improvise the use of items even when they are not intended for you. "
                "You ignore all class, race, and level requirements on the use of "
                "magic items."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"ignore_item_requirements": True},
            ),
        ),
        ClassFeature(
            name="Thief's Reflexes",
            level=17,
            description=(
                "You have become adept at laying ambushes and quickly escaping danger. "
                "You can take two turns during the first round of any combat. You take "
                "your first turn at your normal initiative and your second turn at your "
                "initiative minus 10."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"extra_first_round_turn": True, "second_turn_initiative": -10},
            ),
        ),
    ],
)


# =============================================================================
# Barbarian Subclasses
# =============================================================================

BERSERKER = Subclass(
    id="berserker",
    name="Path of the Berserker",
    parent_class=ClassName.BARBARIAN,
    description=(
        "For some barbarians, rage is a means to an end—that end being violence. "
        "The Path of the Berserker is a path of untrammeled fury, slick with blood. "
        "As you enter the berserker's rage, you thrill in the chaos of battle."
    ),
    features=[
        ClassFeature(
            name="Frenzy",
            level=3,
            description=(
                "You can go into a frenzy when you rage. If you do so, for the duration "
                "of your rage you can make a single melee weapon attack as a bonus action "
                "on each of your turns after this one."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"bonus_action_attack": True, "requires_rage": True},
            ),
        ),
        ClassFeature(
            name="Mindless Rage",
            level=6,
            description=(
                "You can't be charmed or frightened while raging. If you are charmed or "
                "frightened when you enter your rage, the effect is suspended for the "
                "duration of the rage."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"immunity_while_raging": ["charmed", "frightened"]},
            ),
        ),
        ClassFeature(
            name="Intimidating Presence",
            level=10,
            description=(
                "You can use your action to frighten someone with your menacing presence. "
                "When you do so, choose one creature that you can see within 30 feet. "
                "If the creature can see or hear you, it must succeed on a Wisdom saving "
                "throw (DC equal to 8 + your proficiency bonus + your Charisma modifier) "
                "or be frightened of you until the end of your next turn."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={
                    "action_cost": True,
                    "range": 30,
                    "save_dc": "8 + proficiency + charisma",
                    "condition": "frightened",
                },
            ),
        ),
        ClassFeature(
            name="Retaliation",
            level=14,
            description=(
                "When you take damage from a creature that is within 5 feet of you, "
                "you can use your reaction to make a melee weapon attack against "
                "that creature."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.REACTION,
                extra_data={"trigger": "take_damage", "range": 5},
            ),
        ),
    ],
)


# =============================================================================
# Monk Subclasses
# =============================================================================

WAY_OF_THE_OPEN_HAND = Subclass(
    id="way_of_the_open_hand",
    name="Way of the Open Hand",
    parent_class=ClassName.MONK,
    description=(
        "Monks of the Way of the Open Hand are the ultimate masters of martial arts "
        "combat, whether armed or unarmed. They learn techniques to push and trip "
        "their opponents, manipulate ki to heal damage to their bodies, and practice "
        "advanced meditation that can protect them from harm."
    ),
    features=[
        ClassFeature(
            name="Open Hand Technique",
            level=3,
            description=(
                "Whenever you hit a creature with one of the attacks granted by your "
                "Flurry of Blows, you can impose one of the following effects on that "
                "target: It must succeed on a Dexterity saving throw or be knocked prone. "
                "It must make a Strength saving throw. If it fails, you can push it up "
                "to 15 feet away from you. It can't take reactions until the end of "
                "your next turn."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={
                    "requires_flurry": True,
                    "options": [
                        {"save": "dexterity", "effect": "prone"},
                        {"save": "strength", "effect": "push", "distance": 15},
                        {"effect": "no_reactions"},
                    ],
                },
            ),
        ),
        ClassFeature(
            name="Wholeness of Body",
            level=6,
            description=(
                "You gain the ability to heal yourself. As an action, you can regain "
                "hit points equal to three times your monk level. You must finish a "
                "long rest before you can use this feature again."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.RESOURCE,
                resource_name="Wholeness of Body",
                uses_per_rest=1,
                recover_on=RestType.LONG,
                extra_data={"heal_formula": "level * 3"},
            ),
        ),
        ClassFeature(
            name="Tranquility",
            level=11,
            description=(
                "You can enter a special meditation that surrounds you with an aura of "
                "peace. At the end of a long rest, you gain the effect of a sanctuary "
                "spell that lasts until the start of your next long rest (the spell can "
                "end early as normal)."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"grants_sanctuary": True, "duration": "until_long_rest"},
            ),
        ),
        ClassFeature(
            name="Quivering Palm",
            level=17,
            description=(
                "You gain the ability to set up lethal vibrations in someone's body. "
                "When you hit a creature with an unarmed strike, you can spend 3 focus "
                "points to start these imperceptible vibrations, which last for a number "
                "of days equal to your monk level. You can use your action to end the "
                "vibrations, forcing the target to make a Constitution save or be reduced "
                "to 0 HP. On a success, it takes 10d10 necrotic damage."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={
                    "focus_cost": 3,
                    "save": "constitution",
                    "damage_on_success": "10d10",
                    "damage_type": "necrotic",
                },
            ),
        ),
    ],
)


# =============================================================================
# Registry
# =============================================================================

SUBCLASS_REGISTRY: dict[str, Subclass] = {
    # Fighter
    "champion": CHAMPION,
    # Rogue
    "thief": THIEF,
    # Barbarian
    "berserker": BERSERKER,
    # Monk
    "way_of_the_open_hand": WAY_OF_THE_OPEN_HAND,
}


def get_subclass(subclass_id: str) -> Subclass:
    """Get a subclass by ID.

    Args:
        subclass_id: The subclass identifier (e.g., "champion", "thief")

    Returns:
        A copy of the Subclass

    Raises:
        KeyError: If the subclass ID is not found
    """
    if subclass_id not in SUBCLASS_REGISTRY:
        raise KeyError(f"Unknown subclass: {subclass_id}")
    return SUBCLASS_REGISTRY[subclass_id].model_copy(deep=True)


def list_subclasses(parent_class: ClassName | None = None) -> list[Subclass]:
    """List all available subclasses.

    Args:
        parent_class: Optional filter by parent class

    Returns:
        List of Subclass objects (copies)
    """
    subclasses = [s.model_copy(deep=True) for s in SUBCLASS_REGISTRY.values()]
    if parent_class is not None:
        subclasses = [s for s in subclasses if s.parent_class == parent_class]
    return subclasses


def get_subclasses_for_class(class_name: ClassName) -> list[Subclass]:
    """Get all subclasses available for a specific class.

    Args:
        class_name: The class to get subclasses for

    Returns:
        List of Subclass objects (copies)
    """
    return list_subclasses(class_name)
