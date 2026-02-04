"""Tests for the D&D character system."""

import pytest

from dnd_bot.character import (
    Ability,
    AbilityScores,
    Background,
    Fighter,
    Motivation,
    PersonalityTraits,
    Skill,
    SpeciesName,
    calculate_modifier,
    create_character,
    get_proficiency_bonus,
    get_skill_ability,
    get_species,
)


class TestAbilityScores:
    """Tests for ability scores and modifiers."""

    def test_default_scores(self):
        """Default ability scores should be 10."""
        scores = AbilityScores()
        assert scores.strength == 10
        assert scores.dexterity == 10
        assert scores.constitution == 10
        assert scores.intelligence == 10
        assert scores.wisdom == 10
        assert scores.charisma == 10

    def test_custom_scores(self):
        """Custom ability scores should be stored correctly."""
        scores = AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=8,
            wisdom=12,
            charisma=10,
        )
        assert scores.strength == 16
        assert scores.dexterity == 14
        assert scores.constitution == 15
        assert scores.intelligence == 8
        assert scores.wisdom == 12
        assert scores.charisma == 10

    def test_modifier_calculation(self):
        """Modifiers should calculate correctly."""
        assert calculate_modifier(1) == -5
        assert calculate_modifier(8) == -1
        assert calculate_modifier(9) == -1
        assert calculate_modifier(10) == 0
        assert calculate_modifier(11) == 0
        assert calculate_modifier(12) == 1
        assert calculate_modifier(13) == 1
        assert calculate_modifier(14) == 2
        assert calculate_modifier(15) == 2
        assert calculate_modifier(16) == 3
        assert calculate_modifier(18) == 4
        assert calculate_modifier(20) == 5
        assert calculate_modifier(30) == 10

    def test_ability_score_modifiers(self):
        """AbilityScores should calculate modifiers correctly."""
        scores = AbilityScores(strength=16, dexterity=8)
        assert scores.strength_modifier == 3
        assert scores.dexterity_modifier == -1
        assert scores.constitution_modifier == 0  # Default 10

    def test_get_score_by_ability(self):
        """Should retrieve score by Ability enum."""
        scores = AbilityScores(strength=18)
        assert scores.get_score(Ability.STRENGTH) == 18
        assert scores.get_score(Ability.STR) == 18  # Alias should work

    def test_get_modifier_by_ability(self):
        """Should retrieve modifier by Ability enum."""
        scores = AbilityScores(wisdom=14)
        assert scores.get_modifier(Ability.WISDOM) == 2
        assert scores.get_modifier(Ability.WIS) == 2

    def test_score_validation(self):
        """Scores outside 1-30 should raise validation error."""
        with pytest.raises(ValueError):
            AbilityScores(strength=0)
        with pytest.raises(ValueError):
            AbilityScores(dexterity=31)


class TestSkills:
    """Tests for skill system."""

    def test_skill_ability_mapping(self):
        """Skills should map to correct abilities."""
        assert get_skill_ability(Skill.ATHLETICS) == Ability.STRENGTH
        assert get_skill_ability(Skill.STEALTH) == Ability.DEXTERITY
        assert get_skill_ability(Skill.ARCANA) == Ability.INTELLIGENCE
        assert get_skill_ability(Skill.PERCEPTION) == Ability.WISDOM
        assert get_skill_ability(Skill.PERSUASION) == Ability.CHARISMA

    def test_proficiency_bonus_by_level(self):
        """Proficiency bonus should increase correctly with level."""
        assert get_proficiency_bonus(1) == 2
        assert get_proficiency_bonus(4) == 2
        assert get_proficiency_bonus(5) == 3
        assert get_proficiency_bonus(8) == 3
        assert get_proficiency_bonus(9) == 4
        assert get_proficiency_bonus(12) == 4
        assert get_proficiency_bonus(13) == 5
        assert get_proficiency_bonus(16) == 5
        assert get_proficiency_bonus(17) == 6
        assert get_proficiency_bonus(20) == 6


class TestSpecies:
    """Tests for species definitions."""

    def test_get_human(self):
        """Human species should have correct properties."""
        human = get_species(SpeciesName.HUMAN)
        assert human.name == SpeciesName.HUMAN
        assert human.speed == 30
        assert human.darkvision == 0
        assert len(human.traits) == 3  # Resourceful, Skillful, Versatile

    def test_get_elf(self):
        """Elf species should have correct properties."""
        elf = get_species(SpeciesName.ELF)
        assert elf.name == SpeciesName.ELF
        assert elf.darkvision == 60
        assert "Elvish" in elf.languages

    def test_get_dwarf(self):
        """Dwarf species should have correct properties."""
        dwarf = get_species(SpeciesName.DWARF)
        assert dwarf.name == SpeciesName.DWARF
        assert dwarf.darkvision == 120
        assert "Poison" in dwarf.resistances

    def test_get_halfling(self):
        """Halfling species should have correct properties."""
        halfling = get_species(SpeciesName.HALFLING)
        assert halfling.name == SpeciesName.HALFLING
        assert halfling.size.value == "small"


class TestClasses:
    """Tests for character class definitions."""

    def test_fighter_class(self):
        """Fighter class should have correct properties."""
        fighter = create_character(
            name="Test",
            class_type="fighter",
            species_name=SpeciesName.HUMAN,
        )
        assert fighter.class_type == "fighter"
        assert fighter.hit_die == 10
        assert Ability.STRENGTH in fighter.class_saving_throws
        assert Ability.CONSTITUTION in fighter.class_saving_throws

    def test_rogue_class(self):
        """Rogue class should have correct properties."""
        rogue = create_character(
            name="Test",
            class_type="rogue",
            species_name=SpeciesName.HUMAN,
        )
        assert rogue.class_type == "rogue"
        assert rogue.hit_die == 8

    def test_barbarian_class(self):
        """Barbarian class should have correct properties."""
        barbarian = create_character(
            name="Test",
            class_type="barbarian",
            species_name=SpeciesName.HUMAN,
        )
        assert barbarian.class_type == "barbarian"
        assert barbarian.hit_die == 12  # Largest hit die

    def test_monk_class(self):
        """Monk class should have correct properties."""
        monk = create_character(
            name="Test",
            class_type="monk",
            species_name=SpeciesName.HUMAN,
        )
        assert monk.class_type == "monk"
        assert monk.hit_die == 8

    def test_class_features_at_level(self):
        """Should filter features by level."""
        fighter = create_character(
            name="Test",
            class_type="fighter",
            species_name=SpeciesName.HUMAN,
            level=5,
        )
        features = fighter.class_features
        names = [f.name for f in features]

        # Level 1 should have Fighting Style, Second Wind
        assert "Second Wind" in names
        # Level 5 should have Extra Attack
        assert "Extra Attack" in names


class TestCharacter:
    """Tests for the main Character class."""

    def test_create_basic_character(self):
        """Should create a character with factory function."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        assert char.name == "Test Fighter"
        assert char.level == 1
        assert char.species.name == SpeciesName.HUMAN
        assert char.class_type == "fighter"
        assert isinstance(char, Fighter)

    def test_character_proficiency_bonus(self):
        """Character should calculate proficiency bonus correctly."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=1,
        )
        assert char.proficiency_bonus == 2

        char_lvl5 = create_character(
            name="Fighter5",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
        )
        assert char_lvl5.proficiency_bonus == 3

    def test_character_hp_calculation(self):
        """HP should calculate correctly based on class and CON."""
        scores = AbilityScores(constitution=14)  # +2 modifier
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
            level=1,
        )
        # Fighter: d10 + CON mod = 10 + 2 = 12
        assert char.max_hp == 12

    def test_dwarf_hp_bonus(self):
        """Dwarves should get +1 HP per level."""
        scores = AbilityScores(constitution=10)  # +0 modifier
        char = create_character(
            name="Dwarf Fighter",
            species_name=SpeciesName.DWARF,
            class_type="fighter",
            ability_scores=scores,
            level=1,
        )
        # Fighter: d10 + CON mod + dwarf bonus = 10 + 0 + 1 = 11
        assert char.max_hp == 11

    def test_skill_bonus_without_proficiency(self):
        """Skill bonus without proficiency should be just ability mod."""
        scores = AbilityScores(dexterity=14)  # +2 modifier
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
        )
        # Stealth (DEX) without proficiency = just DEX mod
        assert char.get_skill_bonus(Skill.STEALTH) == 2

    def test_skill_bonus_with_proficiency(self):
        """Skill bonus with proficiency should include proficiency bonus."""
        scores = AbilityScores(dexterity=14)  # +2 modifier
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
            skill_proficiencies=[Skill.STEALTH],
        )
        # Stealth (DEX) with proficiency = DEX mod + prof bonus = 2 + 2 = 4
        assert char.get_skill_bonus(Skill.STEALTH) == 4

    def test_skill_bonus_with_expertise(self):
        """Skill bonus with expertise should double proficiency."""
        scores = AbilityScores(dexterity=14)  # +2 modifier
        char = create_character(
            name="Rogue",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            ability_scores=scores,
            skill_proficiencies=[Skill.STEALTH],
        )
        char.skills.set_expertise(Skill.STEALTH)
        # Stealth with expertise = DEX mod + 2*prof = 2 + 4 = 6
        assert char.get_skill_bonus(Skill.STEALTH) == 6

    def test_saving_throw_proficiency(self):
        """Characters should be proficient in class saving throws."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        assert Ability.STRENGTH in char.saving_throw_proficiencies
        assert Ability.CONSTITUTION in char.saving_throw_proficiencies
        assert Ability.DEXTERITY not in char.saving_throw_proficiencies

    def test_saving_throw_bonus(self):
        """Saving throw bonus should include proficiency when proficient."""
        scores = AbilityScores(strength=14, dexterity=14)  # Both +2
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
        )
        # STR save (proficient): mod + prof = 2 + 2 = 4
        assert char.get_saving_throw_bonus(Ability.STRENGTH) == 4
        # DEX save (not proficient): just mod = 2
        assert char.get_saving_throw_bonus(Ability.DEXTERITY) == 2

    def test_initiative(self):
        """Initiative should equal DEX modifier."""
        scores = AbilityScores(dexterity=16)  # +3 modifier
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
        )
        assert char.initiative == 3

    def test_passive_perception(self):
        """Passive perception should be 10 + perception bonus."""
        scores = AbilityScores(wisdom=14)  # +2 modifier
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
        )
        # Without proficiency: 10 + 2 = 12
        assert char.passive_perception == 12

    def test_damage_and_healing(self):
        """Character should track damage and healing correctly."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        initial_hp = char.current_hp

        # Take damage
        damage = char.take_damage(5)
        assert damage == 5
        assert char.current_hp == initial_hp - 5
        assert char.is_conscious

        # Heal
        healed = char.heal(3)
        assert healed == 3
        assert char.current_hp == initial_hp - 2

        # Can't overheal
        healed = char.heal(100)
        assert char.current_hp == char.max_hp

    def test_temp_hp(self):
        """Temporary HP should absorb damage first."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        initial_hp = char.current_hp

        char.set_temp_hp(5)
        assert char.temp_hp == 5

        # Damage absorbed by temp HP
        damage = char.take_damage(3)
        assert damage == 0
        assert char.temp_hp == 2
        assert char.current_hp == initial_hp

        # Overflow damage goes to real HP
        damage = char.take_damage(5)
        assert damage == 3
        assert char.temp_hp == 0
        assert char.current_hp == initial_hp - 3

    def test_unconscious_at_zero_hp(self):
        """Character should be unconscious at 0 HP."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.take_damage(char.max_hp)
        assert char.current_hp == 0
        assert not char.is_conscious


class TestBackground:
    """Tests for background and personality."""

    def test_background_creation(self):
        """Should create a background with all fields."""
        bg = Background(
            name="Soldier",
            backstory="Fought in the war.",
            personality=PersonalityTraits(
                traits=["Brave", "Loyal"],
                ideals=["Honor"],
                bonds=["My regiment"],
                flaws=["Reckless"],
            ),
            motivations=[
                Motivation(description="Find my lost commander", priority=1),
                Motivation(description="Earn gold", priority=3),
            ],
        )
        assert bg.name == "Soldier"
        assert len(bg.personality.traits) == 2

    def test_primary_motivation(self):
        """Should return highest priority motivation."""
        bg = Background(
            motivations=[
                Motivation(description="Low priority", priority=5),
                Motivation(description="High priority", priority=1),
                Motivation(description="Medium priority", priority=3),
            ]
        )
        primary = bg.get_primary_motivation()
        assert primary.description == "High priority"

    def test_prompt_context(self):
        """Should generate text suitable for AI prompts."""
        bg = Background(
            backstory="A former soldier.",
            personality=PersonalityTraits(traits=["Brave"]),
            motivations=[Motivation(description="Find glory")],
        )
        context = bg.to_prompt_context()
        assert "A former soldier" in context
        assert "Brave" in context
        assert "Find glory" in context
