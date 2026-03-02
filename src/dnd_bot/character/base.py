"""Base Character class for inheritance-based class hierarchy.

All D&D character classes (Fighter, Rogue, etc.) inherit from this base class.
Class-specific behavior is implemented in subclasses.
"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field

from dnd_bot.dice import Dice, d20, roll

from .abilities import Ability, AbilityBonus, AbilityScores
from .background import Background
from .conditions import Condition, ConditionManager
from .exhaustion import Exhaustion
from .resources import HitDice, ResourcePool, RestType
from .skills import Skill, SkillSet, get_proficiency_bonus, get_skill_ability
from .species import Species, SpeciesName

# Import items module for AC calculation (lazy import to avoid circular deps)
_items_module = None


def _get_items_module():
    """Lazy import of items module to avoid circular dependencies."""
    global _items_module
    if _items_module is None:
        from dnd_bot import items as _items_module
    return _items_module


class FeatureMechanicType(str, Enum):
    """Types of class feature mechanics."""

    PASSIVE = "passive"
    RESOURCE = "resource"
    TOGGLE = "toggle"
    REACTION = "reaction"


class FeatureMechanic(BaseModel):
    """Mechanical data for a class feature."""

    mechanic_type: FeatureMechanicType
    resource_name: str | None = Field(
        default=None,
        description="Name of the resource to track (for RESOURCE/TOGGLE types)",
    )
    uses_per_rest: int | None = Field(
        default=None,
        description="Number of uses per rest (for RESOURCE types)",
    )
    uses_per_rest_formula: str | None = Field(
        default=None,
        description="Formula for uses (e.g., 'level' for Monk Focus Points)",
    )
    recover_on: RestType | None = Field(
        default=None,
        description="When the resource recovers (SHORT or LONG)",
    )
    dice: str | None = Field(
        default=None,
        description="Dice to roll (e.g., '1d10' for Second Wind)",
    )
    dice_per_level: str | None = Field(
        default=None,
        description="Dice that scale with level (e.g., '1d6' for Sneak Attack per 2 levels)",
    )
    bonus: int | None = Field(
        default=None,
        description="Static bonus value",
    )
    extra_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional mechanic-specific data",
    )


class ClassFeature(BaseModel):
    """A class feature gained at a specific level."""

    name: str
    level: int = Field(ge=1, le=20)
    description: str
    mechanic: FeatureMechanic | None = Field(
        default=None,
        description="Mechanical data for features with game effects",
    )


class RestResult(BaseModel):
    """Result of taking a short or long rest."""

    rest_type: RestType
    success: bool = True
    error: str | None = None
    hp_recovered: int = 0
    hit_dice_spent: int = 0
    hit_dice_recovered: int = 0
    exhaustion_removed: int = 0
    resources_recovered: dict[str, int] = Field(default_factory=dict)
    ends_session: bool = False  # True for long rests


class DeathSaveOutcome(str, Enum):
    """Possible outcomes of a death saving throw."""

    SUCCESS = "success"
    FAILURE = "failure"
    CRITICAL_SUCCESS = "critical_success"  # Nat 20: regain 1 HP
    CRITICAL_FAILURE = "critical_failure"  # Nat 1: 2 failures
    STABILIZED = "stabilized"  # 3 successes
    DEAD = "dead"  # 3 failures


class DeathSaveResult(BaseModel):
    """Result of making a death saving throw."""

    roll: int
    outcome: DeathSaveOutcome
    successes: int  # Total after this roll
    failures: int  # Total after this roll
    hp_recovered: int = 0  # Only on nat 20


class DeathSaves(BaseModel):
    """Tracks death saving throw progress."""

    successes: int = Field(default=0, ge=0, le=3)
    failures: int = Field(default=0, ge=0, le=3)
    is_stable: bool = False

    def add_success(self) -> bool:
        """Add a success. Returns True if now stabilized."""
        self.successes = min(3, self.successes + 1)
        if self.successes >= 3:
            self.is_stable = True
        return self.is_stable

    def add_failure(self, count: int = 1) -> bool:
        """Add failure(s). Returns True if now dead."""
        self.failures = min(3, self.failures + count)
        return self.failures >= 3

    def reset(self) -> None:
        """Reset death saves (when healed above 0 HP)."""
        self.successes = 0
        self.failures = 0
        self.is_stable = False

    @property
    def is_dead(self) -> bool:
        """Check if character has died (3 failures)."""
        return self.failures >= 3

    @property
    def is_making_saves(self) -> bool:
        """Check if character should be making death saves."""
        return not self.is_stable and not self.is_dead


class Equipment(BaseModel):
    """Equipment tracking with item IDs.

    Weapons and armor are stored as item IDs that can be looked up
    in the items module registries.
    """

    weapon_ids: list[str] = Field(
        default_factory=list,
        description="IDs of equipped weapons",
    )
    armor_id: str | None = Field(
        default=None,
        description="ID of equipped armor (None = unarmored)",
    )
    shield_equipped: bool = Field(
        default=False,
        description="Whether a shield is equipped",
    )
    other_items: list[str] = Field(
        default_factory=list,
        description="IDs of other equipped/carried items",
    )
    gold: int = Field(default=0, ge=0, description="Gold pieces carried")

    # Legacy field aliases for backwards compatibility
    @property
    def weapons(self) -> list[str]:
        """Alias for weapon_ids (backwards compatibility)."""
        return self.weapon_ids

    @property
    def armor(self) -> str:
        """Alias for armor_id (backwards compatibility)."""
        return self.armor_id or ""

    @property
    def shield(self) -> bool:
        """Alias for shield_equipped (backwards compatibility)."""
        return self.shield_equipped

    @property
    def items(self) -> list[str]:
        """Alias for other_items (backwards compatibility)."""
        return self.other_items

    def item_names(self) -> list[str]:
        """Return display names for all carried equipment.

        Resolves weapon and armor IDs to their registered names. Shield is
        listed as "Shield". Other items are included as their raw IDs.

        Returns
        -------
        list[str]
            Display names in order: weapons, armor, shield, other items.
        """
        items_mod = _get_items_module()
        names: list[str] = []
        for wid in self.weapon_ids:
            try:
                names.append(items_mod.get_weapon(wid).name)
            except KeyError:
                names.append(wid)
        if self.armor_id:
            try:
                names.append(items_mod.get_armor(self.armor_id).name)
            except KeyError:
                names.append(self.armor_id)
        if self.shield_equipped:
            names.append("Shield")
        names.extend(self.other_items)
        return names


class Character(BaseModel):
    """Base character class - subclass for each D&D class.

    This is an abstract base class. Use Fighter, Rogue, Barbarian, or Monk
    for concrete characters, or their subclasses (Champion, Thief, etc.).
    """

    # Discriminator for serialization - set by subclasses
    class_type: str

    # Identity
    name: str
    level: int = Field(default=1, ge=1, le=20)

    # Core components
    ability_scores: AbilityScores = Field(default_factory=AbilityScores)
    skills: SkillSet = Field(default_factory=SkillSet)
    species: Species
    background: Background = Field(default_factory=Background)

    # Combat stats
    current_hp: int = Field(default=0, ge=0)
    max_hp: int = Field(default=0, ge=0)
    temp_hp: int = Field(default=0, ge=0)
    armor_class: int = Field(default=10, ge=0)

    # Equipment
    equipment: Equipment = Field(default_factory=Equipment)

    # Bonuses and conditions
    ability_bonuses: list[AbilityBonus] = Field(default_factory=list)
    exhaustion: Exhaustion = Field(default_factory=Exhaustion)
    conditions: ConditionManager = Field(default_factory=ConditionManager)

    # Resources (hit dice, feature uses)
    resources: ResourcePool = Field(default_factory=ResourcePool)

    # Death saving throws
    death_saves: DeathSaves = Field(default_factory=DeathSaves)

    # Proficiencies (additional beyond class/species)
    saving_throw_proficiencies: list[Ability] = Field(default_factory=list)

    # Experience and progression
    experience_points: int = Field(default=0, ge=0)

    @property
    def character_class(self) -> str:
        """Return the character's class name (e.g. 'Fighter', 'Champion')."""
        return type(self).__name__

    # Abstract properties - must be implemented by subclasses
    @property
    @abstractmethod
    def hit_die(self) -> int:
        """Hit die size (d6=6, d8=8, d10=10, d12=12)."""
        ...

    @property
    @abstractmethod
    def class_saving_throws(self) -> list[Ability]:
        """Abilities this class is proficient in for saves."""
        ...

    @property
    @abstractmethod
    def class_features(self) -> list[ClassFeature]:
        """Features available at current level."""
        ...

    def model_post_init(self, __context: object) -> None:
        """Initialize derived stats after model creation."""
        # Set up saving throw proficiencies from class if not already set
        if not self.saving_throw_proficiencies:
            self.saving_throw_proficiencies = list(self.class_saving_throws)

        # Initialize HP if not set
        if self.max_hp == 0:
            self.max_hp = self.calculate_max_hp()
        if self.current_hp == 0:
            self.current_hp = self.max_hp

        # Initialize hit dice if not set
        if self.resources.hit_dice is None:
            self.resources.hit_dice = HitDice(
                die_size=self.hit_die,
                total=self.level,
                current=self.level,
            )

        # Register class feature resources if not already registered
        self._register_class_resources()

        # Initialize AC if at default value
        if self.armor_class == 10:
            self.armor_class = self.calculate_armor_class()

    def _register_class_resources(self) -> None:
        """Register class feature resources in the ResourcePool.

        Iterates through class features with RESOURCE or TOGGLE mechanics
        and adds them to the character's resource pool.
        """
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

            # Calculate uses based on level
            uses = self._calculate_resource_uses(feature)

            # Register the resource
            self.resources.add_feature(
                name=feature.mechanic.resource_name,
                maximum=uses,
                recover_on=feature.mechanic.recover_on or RestType.LONG,
            )

    def _calculate_resource_uses(self, feature: ClassFeature) -> int:
        """Calculate the number of uses for a resource feature at current level."""
        if feature.mechanic is None:
            return 1

        if feature.mechanic.uses_per_rest is not None:
            return feature.mechanic.uses_per_rest

        if feature.mechanic.uses_per_rest_formula is not None:
            formula = feature.mechanic.uses_per_rest_formula
            if formula == "level":
                return self.level
            if formula.startswith("level/"):
                divisor = int(formula.split("/")[1])
                return max(1, self.level // divisor)

        return 1

    @computed_field
    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        return get_proficiency_bonus(self.level)

    def get_effective_ability_score(self, ability: Ability) -> int:
        """Get ability score including any bonuses."""
        base = self.ability_scores.get_score(ability)
        bonus = sum(ab.value for ab in self.ability_bonuses if ab.ability == ability)
        # Cap at 30 (D&D maximum)
        return min(30, base + bonus)

    def get_ability_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability including bonuses."""
        score = self.get_effective_ability_score(ability)
        return (score - 10) // 2

    def calculate_max_hp(self) -> int:
        """Calculate maximum HP based on class, level, and CON modifier."""
        hit_die = self.hit_die
        con_mod = self.get_ability_modifier(Ability.CONSTITUTION)

        # First level: max hit die + CON mod
        hp = hit_die + con_mod

        # Additional levels: average of hit die + CON mod
        # Using average rounded up: (die/2 + 1)
        if self.level > 1:
            avg_roll = (hit_die // 2) + 1
            hp += (self.level - 1) * (avg_roll + con_mod)

        # Dwarf Toughness bonus (1 HP per level)
        if self.species.name == SpeciesName.DWARF:
            hp += self.level

        return max(1, hp)

    def calculate_armor_class(self) -> int:
        """Calculate AC based on equipped armor, shield, and class features.

        Subclasses can override this for special AC calculations
        (e.g., Barbarian/Monk unarmored defense).
        """
        dex_mod = self.get_ability_modifier(Ability.DEXTERITY)

        # Check for equipped armor
        if self.equipment.armor_id is None:
            # Standard unarmored: 10 + DEX
            base_ac = 10 + dex_mod
        else:
            # Calculate AC from equipped armor
            items = _get_items_module()
            try:
                armor = items.get_armor(self.equipment.armor_id)
                base_ac = armor.calculate_ac(dex_mod)
            except KeyError:
                # Unknown armor ID, fall back to base 10 + DEX
                base_ac = 10 + dex_mod

        # Add shield bonus
        if self.equipment.shield_equipped:
            base_ac += 2

        return base_ac

    def recalculate_armor_class(self) -> int:
        """Recalculate and update armor_class field. Returns the new AC."""
        self.armor_class = self.calculate_armor_class()
        return self.armor_class

    def get_skill_bonus(self, skill: Skill) -> int:
        """Calculate total bonus for a skill check."""
        ability = get_skill_ability(skill)
        ability_mod = self.get_ability_modifier(ability)
        prof_multiplier = self.skills.get_proficiency_multiplier(skill)
        return ability_mod + (prof_multiplier * self.proficiency_bonus)

    def get_saving_throw_bonus(self, ability: Ability) -> int:
        """Calculate total bonus for a saving throw."""
        ability_mod = self.get_ability_modifier(ability)
        if ability in self.saving_throw_proficiencies:
            return ability_mod + self.proficiency_bonus
        return ability_mod

    @computed_field
    @property
    def initiative(self) -> int:
        """Calculate initiative modifier (DEX modifier)."""
        return self.get_ability_modifier(Ability.DEXTERITY)

    @computed_field
    @property
    def passive_perception(self) -> int:
        """Calculate passive Perception."""
        return 10 + self.get_skill_bonus(Skill.PERCEPTION)

    def make_ability_check(
        self, ability: Ability, advantage: bool = False, disadvantage: bool = False
    ) -> tuple[int, int]:
        """Make an ability check.

        Returns (total, die_roll) where total = die_roll + modifier + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        modifier = self.get_ability_modifier(ability)
        result = d20(advantage=advantage, disadvantage=disadvantage)
        die_roll = result.total  # The chosen roll (max for adv, min for disadv)
        total = die_roll + modifier + self.exhaustion.penalty
        return (total, die_roll)

    def make_skill_check(
        self, skill: Skill, advantage: bool = False, disadvantage: bool = False
    ) -> tuple[int, int]:
        """Make a skill check.

        Returns (total, die_roll) where total = die_roll + bonus + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        bonus = self.get_skill_bonus(skill)
        result = d20(advantage=advantage, disadvantage=disadvantage)
        die_roll = result.total
        total = die_roll + bonus + self.exhaustion.penalty
        return (total, die_roll)

    def make_saving_throw(
        self, ability: Ability, advantage: bool = False, disadvantage: bool = False
    ) -> tuple[int, int]:
        """Make a saving throw.

        Returns (total, die_roll) where total = die_roll + bonus + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        bonus = self.get_saving_throw_bonus(ability)
        result = d20(advantage=advantage, disadvantage=disadvantage)
        die_roll = result.total
        total = die_roll + bonus + self.exhaustion.penalty
        return (total, die_roll)

    def make_attack_roll(
        self,
        ability: Ability,
        is_proficient: bool = True,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> tuple[int, int]:
        """Make an attack roll.

        Returns (total, die_roll) where total = die_roll + modifier + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        modifier = self.get_ability_modifier(ability)
        if is_proficient:
            modifier += self.proficiency_bonus
        result = d20(advantage=advantage, disadvantage=disadvantage)
        die_roll = result.total
        total = die_roll + modifier + self.exhaustion.penalty
        return (total, die_roll)

    def get_attack_ability(self, weapon_obj: Any = None) -> Ability:
        """Get the ability modifier to use for an attack roll.

        Parameters
        ----------
        weapon_obj : Weapon | None
            The weapon being used, or None for unarmed.

        Returns
        -------
        Ability
            DEXTERITY for finesse/ranged weapons, STRENGTH otherwise.
        """
        if weapon_obj is not None and weapon_obj.is_finesse:
            str_mod = self.get_ability_modifier(Ability.STRENGTH)
            dex_mod = self.get_ability_modifier(Ability.DEXTERITY)
            return Ability.DEXTERITY if dex_mod > str_mod else Ability.STRENGTH
        if weapon_obj is not None and weapon_obj.is_ranged:
            return Ability.DEXTERITY
        return Ability.STRENGTH

    def roll_unarmed_damage(self) -> tuple[int, str]:
        """Roll damage for an unarmed strike (1 + STR modifier).

        Returns
        -------
        tuple[int, str]
            (damage_total, formula) e.g. (4, "1 + +3")
        """
        mod = self.get_ability_modifier(Ability.STRENGTH)
        return 1 + mod, f"1 + {mod:+d}"

    def roll_weapon_damage(
        self, dice_notation: str, modifier: int, is_crit: bool = False, advantage: bool = False
    ) -> tuple[int, str]:
        """Roll damage for a weapon attack.

        Parameters
        ----------
        dice_notation : str
            Weapon damage dice (e.g. "1d8", "2d6").
        modifier : int
            Ability modifier added to the damage.
        is_crit : bool
            Whether the attack was a critical hit. Doubles weapon dice on a crit.
        advantage : bool
            Whether the attacker had effective advantage (advantage and not disadvantage).
            Forwarded to subclasses that use it (e.g. Rogue Sneak Attack).

        Returns
        -------
        tuple[int, str]
            (damage_total, notation_used) e.g. (11, "2d8")
        """
        parsed = Dice.parse(dice_notation)
        if is_crit:
            count = parsed.count * 2
            total = Dice(count=count, sides=parsed.sides).roll().total + modifier
            return total, f"{count}d{parsed.sides}"
        total = roll(dice_notation).total + modifier
        return total, dice_notation

    def take_damage(self, amount: int, is_critical: bool = False) -> int:
        """Apply damage to the character.

        Temp HP is consumed first. If already at 0 HP, adds death save failures.
        Returns actual HP lost (0 if damage only caused death save failures).
        """
        if amount <= 0:
            return 0

        # If already at 0 HP, add death save failure(s)
        if self.current_hp == 0:
            failures = 2 if is_critical else 1
            self.death_saves.add_failure(failures)
            return 0

        # Temp HP absorbs damage first
        if self.temp_hp > 0:
            if amount <= self.temp_hp:
                self.temp_hp -= amount
                return 0
            amount -= self.temp_hp
            self.temp_hp = 0

        # Apply remaining damage to current HP
        actual_damage = min(amount, self.current_hp)
        self.current_hp -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal the character.

        If healed from 0 HP, resets death saving throws.
        Returns actual HP restored (capped at max_hp).
        """
        if amount <= 0:
            return 0

        was_at_zero = self.current_hp == 0
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal

        # Reset death saves when healed above 0 HP
        if was_at_zero and self.current_hp > 0:
            self.death_saves.reset()

        return actual_heal

    def set_temp_hp(self, amount: int) -> None:
        """Set temporary HP. Only the higher value is kept."""
        self.temp_hp = max(self.temp_hp, amount)

    @property
    def is_conscious(self) -> bool:
        """Check if the character is conscious (HP > 0 and not unconscious)."""
        return self.current_hp > 0 and not self.conditions.has(Condition.UNCONSCIOUS)

    # Death saving throw methods
    def make_death_save(self) -> DeathSaveResult:
        """Make a death saving throw.

        Should only be called when at 0 HP and not stable/dead.
        - Roll 10+: success
        - Roll 9-: failure
        - Natural 20: regain 1 HP and reset death saves
        - Natural 1: 2 failures
        """
        die_roll = d20().total

        # Natural 20: critical success - regain 1 HP
        if die_roll == 20:
            self.current_hp = 1
            self.death_saves.reset()
            return DeathSaveResult(
                roll=die_roll,
                outcome=DeathSaveOutcome.CRITICAL_SUCCESS,
                successes=0,
                failures=0,
                hp_recovered=1,
            )

        # Natural 1: critical failure - 2 failures
        if die_roll == 1:
            is_dead = self.death_saves.add_failure(2)
            outcome = DeathSaveOutcome.DEAD if is_dead else DeathSaveOutcome.CRITICAL_FAILURE
            return DeathSaveResult(
                roll=die_roll,
                outcome=outcome,
                successes=self.death_saves.successes,
                failures=self.death_saves.failures,
            )

        # 10+: success
        if die_roll >= 10:
            is_stable = self.death_saves.add_success()
            outcome = DeathSaveOutcome.STABILIZED if is_stable else DeathSaveOutcome.SUCCESS
            return DeathSaveResult(
                roll=die_roll,
                outcome=outcome,
                successes=self.death_saves.successes,
                failures=self.death_saves.failures,
            )

        # 9-: failure
        is_dead = self.death_saves.add_failure()
        outcome = DeathSaveOutcome.DEAD if is_dead else DeathSaveOutcome.FAILURE
        return DeathSaveResult(
            roll=die_roll,
            outcome=outcome,
            successes=self.death_saves.successes,
            failures=self.death_saves.failures,
        )

    def reset_death_saves(self) -> None:
        """Reset death saving throws (called when healed above 0 HP)."""
        self.death_saves.reset()

    # Condition convenience methods
    def add_condition(
        self,
        condition: Condition,
        source: str = "",
        duration: int | None = None,
    ) -> None:
        """Add a condition to the character."""
        self.conditions.add(condition, source, duration)

    def remove_condition(self, condition: Condition, source: str | None = None) -> int:
        """Remove a condition. Returns number of conditions removed."""
        return self.conditions.remove(condition, source)

    def has_condition(self, condition: Condition) -> bool:
        """Check if the character has a specific condition."""
        return self.conditions.has(condition)

    # Rest methods
    def spend_hit_die(self) -> int:
        """Spend a hit die to heal during a short rest.

        Rolls the hit die and adds CON modifier. Minimum healing is 1 HP.
        """
        if self.resources.hit_dice is None or self.resources.hit_dice.current <= 0:
            return 0

        if not self.resources.hit_dice.spend():
            return 0

        # Roll hit die + CON modifier
        die_size = self.resources.hit_dice.die_size
        result = roll(f"1d{die_size}")
        con_mod = self.get_ability_modifier(Ability.CONSTITUTION)
        healing = max(1, result.total + con_mod)  # Minimum 1 HP

        return self.heal(healing)

    def short_rest(self, hit_dice_to_spend: int = 0) -> RestResult:
        """Take a short rest.

        During a short rest, you can spend hit dice to recover HP.
        Short-rest resources (like Second Wind, Action Surge) recover.
        Maximum 2 short rests between long rests.
        """
        result = RestResult(rest_type=RestType.SHORT)

        # Check if we can take a short rest
        if not self.resources.can_short_rest():
            result.success = False
            result.error = "Maximum 2 short rests between long rests"
            return result

        # Record the short rest
        self.resources.record_short_rest()

        # Spend hit dice for healing
        total_healed = 0
        dice_spent = 0
        for _ in range(hit_dice_to_spend):
            healed = self.spend_hit_die()
            if healed == 0:
                break  # No more hit dice
            total_healed += healed
            dice_spent += 1

        result.hp_recovered = total_healed
        result.hit_dice_spent = dice_spent

        # Recover short-rest resources
        result.resources_recovered = self.resources.recover_short_rest()

        return result

    def long_rest(self) -> RestResult:
        """Take a long rest.

        During a long rest:
        - Recover all HP
        - Recover half of total hit dice (minimum 1)
        - Reset all resource uses
        - Reset short rest counter
        - Remove 1 level of exhaustion
        - Note: Long rests typically end the D&D session
        """
        result = RestResult(rest_type=RestType.LONG, ends_session=True)

        # Recover all HP
        result.hp_recovered = self.heal(self.max_hp)

        # Recover resources (includes hit dice recovery)
        result.resources_recovered = self.resources.recover_long_rest()

        # Extract hit dice recovery from resources if present
        if "Hit Dice" in result.resources_recovered:
            result.hit_dice_recovered = result.resources_recovered.pop("Hit Dice")

        # Remove 1 exhaustion level
        if self.exhaustion.level > 0:
            self.exhaustion.remove(1)
            result.exhaustion_removed = 1

        return result

    def can_short_rest(self) -> bool:
        """Check if a short rest can be taken."""
        return self.resources.can_short_rest()

    # Feature methods
    def get_all_features(self) -> list[ClassFeature]:
        """Get all class features at or below current level."""
        return self.class_features

    def has_feature(self, feature_name: str) -> bool:
        """Check if character has a specific feature."""
        for feature in self.class_features:
            if feature.name == feature_name:
                return True
        return False

    def get_critical_range(self) -> list[int]:
        """Get the range of d20 rolls that count as critical hits.

        Subclasses can override this for features like Improved Critical.
        """
        return [20]

    def is_critical_hit(self, die_roll: int) -> bool:
        """Return True if the die roll is in this character's critical hit range."""
        return die_roll in self.get_critical_range()

    @classmethod
    def from_base(cls, other: Character) -> Character:
        """Create a new character of this class from an existing character.

        Copies all common state (name, level, ability scores, etc.) and
        reinitializes class-specific features.
        """
        data = other.model_dump(exclude={"class_type"})
        # Reset resources so they get reinitialized for the new class
        data["resources"] = ResourcePool().model_dump()
        return cls(**data)
