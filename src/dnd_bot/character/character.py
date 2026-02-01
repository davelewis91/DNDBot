"""Main Character class combining all character components."""

import random

from pydantic import BaseModel, Field, computed_field

from .abilities import Ability, AbilityBonus, AbilityScores
from .background import Background
from .classes import CharacterClass, ClassName, get_class
from .conditions import Condition, ConditionManager
from .exhaustion import Exhaustion
from .resources import HitDice, ResourcePool
from .skills import Skill, SkillSet, get_proficiency_bonus, get_skill_ability
from .species import Species, SpeciesName, get_species


class Equipment(BaseModel):
    """Simple equipment tracking for MVP."""

    weapons: list[str] = Field(default_factory=list)
    armor: str = ""
    shield: bool = False
    items: list[str] = Field(default_factory=list)
    gold: int = Field(default=0, ge=0)


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

    # Proficiencies (additional beyond class/species)
    saving_throw_proficiencies: list[Ability] = Field(default_factory=list)

    # Experience and progression
    experience_points: int = Field(default=0, ge=0)

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
        """Roll a d20, handling advantage/disadvantage."""
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

    def take_damage(self, amount: int) -> int:
        """Apply damage to the character.

        Temp HP is consumed first. Returns actual HP lost.
        """
        if amount <= 0:
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

        Returns actual HP restored (capped at max_hp).
        """
        if amount <= 0:
            return 0

        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal

    def set_temp_hp(self, amount: int) -> None:
        """Set temporary HP. Only the higher value is kept."""
        self.temp_hp = max(self.temp_hp, amount)

    @property
    def is_conscious(self) -> bool:
        """Check if the character is conscious (HP > 0 and not unconscious)."""
        return self.current_hp > 0 and not self.conditions.has(Condition.UNCONSCIOUS)

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


def create_character(
    name: str,
    species_name: SpeciesName,
    class_name: ClassName,
    ability_scores: AbilityScores | None = None,
    level: int = 1,
    skill_proficiencies: list[Skill] | None = None,
    background: Background | None = None,
) -> Character:
    """Factory function to create a new character with sensible defaults."""
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

    # Recalculate HP after all modifiers are set
    character.max_hp = character.calculate_max_hp()
    character.current_hp = character.max_hp

    return character
