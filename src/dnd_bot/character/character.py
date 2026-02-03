"""Main Character class combining all character components."""

import random
from enum import Enum

from pydantic import BaseModel, Field, computed_field

from .abilities import Ability, AbilityBonus, AbilityScores
from .background import Background
from .classes import (
    CharacterClass,
    ClassFeature,
    ClassName,
    calculate_resource_uses,
    get_class,
    get_rage_damage_bonus,
    get_rage_uses,
    get_resource_features,
    get_sneak_attack_dice,
)
from .conditions import Condition, ConditionManager
from .exhaustion import Exhaustion
from .resources import HitDice, ResourcePool, RestType
from .skills import Skill, SkillSet, get_proficiency_bonus, get_skill_ability
from .species import Species, SpeciesName, get_species
from .subclasses import Subclass, get_subclass

# Import items module for AC calculation (lazy import to avoid circular deps)
_items_module = None


def _get_items_module():
    """Lazy import of items module to avoid circular dependencies."""
    global _items_module
    if _items_module is None:
        from dnd_bot import items as _items_module
    return _items_module


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


class Character(BaseModel):
    """A complete D&D character combining all components."""

    # Identity
    name: str
    level: int = Field(default=1, ge=1, le=20)

    # Core components
    ability_scores: AbilityScores = Field(default_factory=AbilityScores)
    skills: SkillSet = Field(default_factory=SkillSet)
    species: Species
    character_class: CharacterClass
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

    # Subclass (gained at level 3)
    subclass: Subclass | None = Field(
        default=None,
        description="Character's subclass (gained at level 3)",
    )

    def model_post_init(self, __context: object) -> None:
        """Initialize derived stats after model creation."""
        # Set up saving throw proficiencies from class
        if not self.saving_throw_proficiencies:
            self.saving_throw_proficiencies = list(
                self.character_class.saving_throw_proficiencies
            )

        # Initialize HP if not set
        if self.max_hp == 0:
            self.max_hp = self.calculate_max_hp()
        if self.current_hp == 0:
            self.current_hp = self.max_hp

        # Initialize hit dice if not set
        if self.resources.hit_dice is None:
            self.resources.hit_dice = HitDice(
                die_size=self.character_class.hit_die.value,
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
        and adds them to the character's resource pool. Handles special
        cases like Rage which scales with level.
        """
        resource_features = get_resource_features(self.character_class, self.level)

        for feature in resource_features:
            if feature.mechanic is None or feature.mechanic.resource_name is None:
                continue

            key = feature.mechanic.resource_name.lower().replace(" ", "_")

            # Skip if already registered
            if key in self.resources.feature_uses:
                continue

            # Calculate uses based on level (special case for scaling resources)
            if feature.mechanic.resource_name == "Rage":
                uses = get_rage_uses(self.level)
            else:
                uses = calculate_resource_uses(feature, self.level)

            # Register the resource
            self.resources.add_feature(
                name=feature.mechanic.resource_name,
                maximum=uses,
                recover_on=feature.mechanic.recover_on or RestType.LONG,
            )

    @computed_field
    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        return get_proficiency_bonus(self.level)

    def get_effective_ability_score(self, ability: Ability) -> int:
        """Get ability score including any bonuses."""
        base = self.ability_scores.get_score(ability)
        bonus = sum(
            ab.value for ab in self.ability_bonuses if ab.ability == ability
        )
        # Cap at 30 (D&D maximum)
        return min(30, base + bonus)

    def get_ability_modifier(self, ability: Ability) -> int:
        """Get the modifier for an ability including bonuses."""
        score = self.get_effective_ability_score(ability)
        return (score - 10) // 2

    def calculate_max_hp(self) -> int:
        """Calculate maximum HP based on class, level, and CON modifier."""
        hit_die = self.character_class.hit_die.value
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

        Considers:
        - Equipped armor (light/medium/heavy)
        - Shield bonus (+2 if equipped)
        - Unarmored Defense (Barbarian: 10 + DEX + CON, Monk: 10 + DEX + WIS)
        - Base unarmored AC (10 + DEX)

        Returns:
            The calculated armor class
        """
        dex_mod = self.get_ability_modifier(Ability.DEXTERITY)

        # Check for unarmored defense (only applies when not wearing armor)
        if self.equipment.armor_id is None:
            # Barbarian Unarmored Defense: 10 + DEX + CON
            if self.character_class.name == ClassName.BARBARIAN:
                con_mod = self.get_ability_modifier(Ability.CONSTITUTION)
                base_ac = 10 + dex_mod + con_mod
            # Monk Unarmored Defense: 10 + DEX + WIS
            elif self.character_class.name == ClassName.MONK:
                wis_mod = self.get_ability_modifier(Ability.WISDOM)
                base_ac = 10 + dex_mod + wis_mod
            else:
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

    def make_ability_check(self, ability: Ability, advantage: bool = False,
                           disadvantage: bool = False) -> tuple[int, int]:
        """Make an ability check.

        Returns (total, die_roll) where total = die_roll + modifier + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        modifier = self.get_ability_modifier(ability)
        die_roll = self._roll_d20(advantage, disadvantage)
        total = die_roll + modifier + self.exhaustion.penalty
        return (total, die_roll)

    def make_skill_check(self, skill: Skill, advantage: bool = False,
                         disadvantage: bool = False) -> tuple[int, int]:
        """Make a skill check.

        Returns (total, die_roll) where total = die_roll + bonus + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        bonus = self.get_skill_bonus(skill)
        die_roll = self._roll_d20(advantage, disadvantage)
        total = die_roll + bonus + self.exhaustion.penalty
        return (total, die_roll)

    def make_saving_throw(self, ability: Ability, advantage: bool = False,
                          disadvantage: bool = False) -> tuple[int, int]:
        """Make a saving throw.

        Returns (total, die_roll) where total = die_roll + bonus + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        bonus = self.get_saving_throw_bonus(ability)
        die_roll = self._roll_d20(advantage, disadvantage)
        total = die_roll + bonus + self.exhaustion.penalty
        return (total, die_roll)

    def make_attack_roll(self, ability: Ability, is_proficient: bool = True,
                         advantage: bool = False,
                         disadvantage: bool = False) -> tuple[int, int]:
        """Make an attack roll.

        Returns (total, die_roll) where total = die_roll + modifier + exhaustion.
        Exhaustion penalty is applied to all d20 tests.
        """
        modifier = self.get_ability_modifier(ability)
        if is_proficient:
            modifier += self.proficiency_bonus
        die_roll = self._roll_d20(advantage, disadvantage)
        total = die_roll + modifier + self.exhaustion.penalty
        return (total, die_roll)

    def _roll_d20(self, advantage: bool = False,
                  disadvantage: bool = False) -> int:
        """Roll a d20, handling advantage and disadvantage.

        Parameters
        ----------
        advantage : bool, optional
            Whether the roll has advantage. Default False.
        disadvantage : bool, optional
            Whether the roll has disadvantage. Default False.

        Returns
        -------
        int
            The die result. If both advantage and disadvantage apply,
            they cancel out and a single roll is made.
        """
        roll1 = random.randint(1, 20)

        # If both advantage and disadvantage, they cancel out
        if advantage and disadvantage:
            return roll1

        if advantage or disadvantage:
            roll2 = random.randint(1, 20)
            if advantage:
                return max(roll1, roll2)
            return min(roll1, roll2)

        return roll1

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

        Returns:
            DeathSaveResult with roll, outcome, and current totals
        """
        roll = random.randint(1, 20)

        # Natural 20: critical success - regain 1 HP
        if roll == 20:
            self.current_hp = 1
            self.death_saves.reset()
            return DeathSaveResult(
                roll=roll,
                outcome=DeathSaveOutcome.CRITICAL_SUCCESS,
                successes=0,
                failures=0,
                hp_recovered=1,
            )

        # Natural 1: critical failure - 2 failures
        if roll == 1:
            is_dead = self.death_saves.add_failure(2)
            outcome = DeathSaveOutcome.DEAD if is_dead else DeathSaveOutcome.CRITICAL_FAILURE
            return DeathSaveResult(
                roll=roll,
                outcome=outcome,
                successes=self.death_saves.successes,
                failures=self.death_saves.failures,
            )

        # 10+: success
        if roll >= 10:
            is_stable = self.death_saves.add_success()
            outcome = DeathSaveOutcome.STABILIZED if is_stable else DeathSaveOutcome.SUCCESS
            return DeathSaveResult(
                roll=roll,
                outcome=outcome,
                successes=self.death_saves.successes,
                failures=self.death_saves.failures,
            )

        # 9-: failure
        is_dead = self.death_saves.add_failure()
        outcome = DeathSaveOutcome.DEAD if is_dead else DeathSaveOutcome.FAILURE
        return DeathSaveResult(
            roll=roll,
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

        Rolls the hit die and adds CON modifier.
        Minimum healing is 1 HP.

        Returns:
            HP healed (0 if no hit dice available)
        """
        if self.resources.hit_dice is None or self.resources.hit_dice.current <= 0:
            return 0

        if not self.resources.hit_dice.spend():
            return 0

        # Roll hit die + CON modifier
        die_size = self.resources.hit_dice.die_size
        roll = random.randint(1, die_size)
        con_mod = self.get_ability_modifier(Ability.CONSTITUTION)
        healing = max(1, roll + con_mod)  # Minimum 1 HP

        return self.heal(healing)

    def short_rest(self, hit_dice_to_spend: int = 0) -> RestResult:
        """Take a short rest.

        During a short rest, you can spend hit dice to recover HP.
        Short-rest resources (like Second Wind, Action Surge) recover.
        Maximum 2 short rests between long rests.

        Args:
            hit_dice_to_spend: Number of hit dice to spend for healing

        Returns:
            RestResult with details of recovery
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

        Returns:
            RestResult with details of recovery
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

    # Class feature helper methods
    def use_second_wind(self) -> int:
        """Use Second Wind to heal (Fighter feature).

        Heals 1d10 + Fighter level HP. Requires the Second Wind resource.

        Returns:
            HP healed (0 if resource not available or not a Fighter)
        """
        if self.character_class.name != ClassName.FIGHTER:
            return 0

        if not self.resources.use_feature("Second Wind"):
            return 0

        # Roll 1d10 + level
        roll = random.randint(1, 10)
        healing = roll + self.level
        return self.heal(healing)

    def can_use_second_wind(self) -> bool:
        """Check if Second Wind is available."""
        return (
            self.character_class.name == ClassName.FIGHTER
            and self.resources.has_feature_available("Second Wind")
        )

    def use_action_surge(self) -> bool:
        """Use Action Surge (Fighter feature).

        Grants an additional action on your turn.

        Returns:
            True if successful, False if not available
        """
        if self.character_class.name != ClassName.FIGHTER:
            return False

        return self.resources.use_feature("Action Surge")

    def can_use_action_surge(self) -> bool:
        """Check if Action Surge is available."""
        return (
            self.character_class.name == ClassName.FIGHTER
            and self.level >= 2
            and self.resources.has_feature_available("Action Surge")
        )

    def start_rage(self) -> bool:
        """Enter a rage (Barbarian feature).

        While raging:
        - Bonus damage on Strength-based melee attacks
        - Resistance to bludgeoning, piercing, and slashing damage
        - Advantage on Strength checks and saving throws

        Returns:
            True if rage started, False if not available
        """
        if self.character_class.name != ClassName.BARBARIAN:
            return False

        if not self.resources.use_feature("Rage"):
            return False

        # Track rage state in conditions or a dedicated field
        # For now, we just track that a rage was used
        return True

    def can_rage(self) -> bool:
        """Check if Rage is available."""
        return (
            self.character_class.name == ClassName.BARBARIAN
            and self.resources.has_feature_available("Rage")
        )

    def get_rage_damage_bonus(self) -> int:
        """Get the current Rage damage bonus based on level."""
        if self.character_class.name != ClassName.BARBARIAN:
            return 0
        return get_rage_damage_bonus(self.level)

    def use_focus_points(self, amount: int = 1) -> bool:
        """Spend Focus Points (Monk feature).

        Used for various Monk abilities like Flurry of Blows,
        Patient Defense, Step of the Wind, etc.

        Args:
            amount: Number of Focus Points to spend

        Returns:
            True if successful, False if not available
        """
        if self.character_class.name != ClassName.MONK:
            return False

        return self.resources.use_feature("Focus Points", amount)

    def get_focus_points(self) -> int:
        """Get current Focus Points remaining."""
        if self.character_class.name != ClassName.MONK:
            return 0
        resource = self.resources.get_feature("Focus Points")
        return resource.current if resource else 0

    def get_sneak_attack_dice(self) -> int:
        """Get the number of Sneak Attack dice based on Rogue level.

        Returns:
            Number of d6s for Sneak Attack (0 if not a Rogue)
        """
        if self.character_class.name != ClassName.ROGUE:
            return 0
        return get_sneak_attack_dice(self.level)

    # Subclass methods
    def set_subclass(self, subclass_id: str) -> bool:
        """Set the character's subclass.

        Args:
            subclass_id: The subclass identifier (e.g., "champion", "thief")

        Returns:
            True if subclass was set successfully, False if invalid

        Raises:
            ValueError: If subclass doesn't match character's class or level < 3
        """
        if self.level < 3:
            raise ValueError("Characters must be level 3+ to choose a subclass")

        subclass = get_subclass(subclass_id)

        if subclass.parent_class != self.character_class.name:
            raise ValueError(
                f"Subclass '{subclass.name}' is for {subclass.parent_class.value}, "
                f"not {self.character_class.name.value}"
            )

        self.subclass = subclass
        self._register_subclass_resources()
        return True

    def _register_subclass_resources(self) -> None:
        """Register subclass feature resources in the ResourcePool.

        Iterates through subclass features at or below the character's level
        and adds any RESOURCE or TOGGLE mechanics to the resource pool.
        Skips resources that are already registered.
        """
        if self.subclass is None:
            return

        from .classes import FeatureMechanicType

        resource_types = {FeatureMechanicType.RESOURCE, FeatureMechanicType.TOGGLE}

        for feature in self.subclass.features:
            if feature.level > self.level:
                continue
            if feature.mechanic is None or feature.mechanic.resource_name is None:
                continue
            if feature.mechanic.mechanic_type not in resource_types:
                continue

            key = feature.mechanic.resource_name.lower().replace(" ", "_")
            if key in self.resources.feature_uses:
                continue

            uses = calculate_resource_uses(feature, self.level)
            self.resources.add_feature(
                name=feature.mechanic.resource_name,
                maximum=uses,
                recover_on=feature.mechanic.recover_on or RestType.LONG,
            )

    def get_all_features(self) -> list[ClassFeature]:
        """Get all class and subclass features at or below current level.

        Returns:
            List of ClassFeature objects from both class and subclass
        """
        features = self.character_class.get_features_at_level(self.level)
        if self.subclass is not None:
            features = features + self.subclass.get_features_at_level(self.level)
        return features

    def has_feature(self, feature_name: str) -> bool:
        """Check if character has a specific feature.

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if the character has this feature at their current level
        """
        for feature in self.get_all_features():
            if feature.name == feature_name:
                return True
        return False

    def get_critical_range(self) -> list[int]:
        """Get the range of d20 rolls that count as critical hits.

        Checks for features like Improved Critical (Champion).

        Returns:
            List of d20 values that are critical hits (default [20])
        """
        critical_range = [20]

        for feature in self.get_all_features():
            if feature.mechanic and "critical_range" in feature.mechanic.extra_data:
                critical_range = feature.mechanic.extra_data["critical_range"]

        return sorted(critical_range)


def create_character(
    name: str,
    species_name: SpeciesName,
    class_name: ClassName,
    ability_scores: AbilityScores | None = None,
    level: int = 1,
    skill_proficiencies: list[Skill] | None = None,
    background: Background | None = None,
    subclass_id: str | None = None,
) -> Character:
    """Factory function to create a new character with sensible defaults.

    Args:
        name: Character name
        species_name: Character species
        class_name: Character class
        ability_scores: Optional custom ability scores
        level: Starting level (default 1)
        skill_proficiencies: Optional list of skill proficiencies
        background: Optional background information
        subclass_id: Optional subclass ID (requires level 3+)

    Returns:
        A new Character instance
    """
    species = get_species(species_name)
    char_class = get_class(class_name)

    character = Character(
        name=name,
        level=level,
        ability_scores=ability_scores or AbilityScores(),
        species=species,
        character_class=char_class,
        background=background or Background(),
    )

    # Apply skill proficiencies
    if skill_proficiencies:
        for skill in skill_proficiencies:
            character.skills.set_proficiency(skill)

    # Set subclass if provided
    if subclass_id is not None:
        if level < 3:
            raise ValueError("Cannot set subclass before level 3")
        character.set_subclass(subclass_id)

    # Recalculate HP after all modifiers are set
    character.max_hp = character.calculate_max_hp()
    character.current_hp = character.max_hp

    return character
