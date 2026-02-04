"""Tests for character YAML storage."""

from pathlib import Path

import pytest

from dnd_bot.character import (
    AbilityScores,
    Background,
    Champion,
    Fighter,
    Motivation,
    PersonalityTraits,
    Skill,
    SpeciesName,
    create_character,
    delete_character,
    list_characters,
    load_character,
    save_character,
)


class TestCharacterStorage:
    """Tests for saving and loading characters."""

    def test_save_and_load_basic_character(self, tmp_path: Path):
        """Should save and load a basic character correctly."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        # Save
        filepath = save_character(char, tmp_path)
        assert filepath.exists()
        assert filepath.suffix == ".yaml"

        # Load
        loaded = load_character(filepath)
        assert loaded.name == char.name
        assert loaded.level == char.level
        assert loaded.species.name == char.species.name
        assert loaded.class_type == char.class_type
        assert isinstance(loaded, Fighter)

    def test_save_and_load_with_custom_abilities(self, tmp_path: Path):
        """Should preserve ability scores."""
        scores = AbilityScores(
            strength=18,
            dexterity=14,
            constitution=16,
            intelligence=10,
            wisdom=12,
            charisma=8,
        )
        char = create_character(
            name="Strong Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=scores,
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.ability_scores.strength == 18
        assert loaded.ability_scores.dexterity == 14
        assert loaded.ability_scores.constitution == 16
        assert loaded.ability_scores.intelligence == 10
        assert loaded.ability_scores.wisdom == 12
        assert loaded.ability_scores.charisma == 8

    def test_save_and_load_with_skills(self, tmp_path: Path):
        """Should preserve skill proficiencies."""
        char = create_character(
            name="Skilled Rogue",
            species_name=SpeciesName.ELF,
            class_type="rogue",
            skill_proficiencies=[Skill.STEALTH, Skill.PERCEPTION, Skill.DECEPTION],
        )
        char.skills.set_expertise(Skill.STEALTH)

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.skills.is_proficient(Skill.STEALTH)
        assert loaded.skills.is_proficient(Skill.PERCEPTION)
        assert loaded.skills.is_proficient(Skill.DECEPTION)
        assert loaded.skills.has_expertise(Skill.STEALTH)
        assert not loaded.skills.has_expertise(Skill.PERCEPTION)

    def test_save_and_load_with_background(self, tmp_path: Path):
        """Should preserve background and motivations."""
        bg = Background(
            name="Soldier",
            backstory="Served in the king's army for ten years.",
            personality=PersonalityTraits(
                traits=["I am always calm under pressure."],
                ideals=["Greater Good: My duty is to protect the innocent."],
                bonds=["I fight for those who cannot fight for themselves."],
                flaws=["I have a weakness for fine wine."],
            ),
            motivations=[
                Motivation(
                    description="Find the traitor who betrayed my unit",
                    priority=1,
                    is_secret=True,
                ),
                Motivation(
                    description="Earn enough gold to retire",
                    priority=3,
                    is_secret=False,
                ),
            ],
            fears=["Drowning", "Betrayal"],
            allies=["The Silver Guard"],
            enemies=["The Shadow Syndicate"],
            notes="Prefers direct confrontation over subtlety.",
        )

        char = create_character(
            name="Veteran Soldier",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            background=bg,
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.background.name == "Soldier"
        assert "king's army" in loaded.background.backstory
        assert len(loaded.background.personality.traits) == 1
        assert len(loaded.background.motivations) == 2
        assert loaded.background.motivations[0].is_secret
        assert "Drowning" in loaded.background.fears
        assert "The Silver Guard" in loaded.background.allies

    def test_save_and_load_combat_stats(self, tmp_path: Path):
        """Should preserve HP and combat stats."""
        char = create_character(
            name="Wounded Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.take_damage(5)
        char.set_temp_hp(3)
        char.armor_class = 18

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.current_hp == char.current_hp
        assert loaded.max_hp == char.max_hp
        assert loaded.temp_hp == 3
        assert loaded.armor_class == 18

    def test_save_and_load_equipment(self, tmp_path: Path):
        """Should preserve equipment."""
        char = create_character(
            name="Equipped Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.equipment.weapon_ids = ["longsword", "handaxe"]
        char.equipment.armor_id = "chain_mail"
        char.equipment.shield_equipped = True
        char.equipment.other_items = ["torch", "rope"]
        char.equipment.gold = 50

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.equipment.weapon_ids == ["longsword", "handaxe"]
        assert loaded.equipment.armor_id == "chain_mail"
        assert loaded.equipment.shield_equipped is True
        assert loaded.equipment.other_items == ["torch", "rope"]
        assert loaded.equipment.gold == 50

    def test_save_and_load_different_species(self, tmp_path: Path):
        """Should work with all species types."""
        species_list = [
            SpeciesName.HUMAN,
            SpeciesName.ELF,
            SpeciesName.DWARF,
            SpeciesName.HALFLING,
        ]

        for species_name in species_list:
            char = create_character(
                name=f"Test {species_name.value.title()}",
                species_name=species_name,
                class_type="fighter",
            )

            filepath = save_character(char, tmp_path)
            loaded = load_character(filepath)

            assert loaded.species.name == species_name

    def test_save_and_load_different_classes(self, tmp_path: Path):
        """Should work with all class types."""
        class_list = ["fighter", "rogue", "barbarian", "monk"]

        for class_type in class_list:
            char = create_character(
                name=f"Test {class_type.title()}",
                species_name=SpeciesName.HUMAN,
                class_type=class_type,
            )

            filepath = save_character(char, tmp_path)
            loaded = load_character(filepath)

            assert loaded.class_type == class_type

    def test_save_and_load_subclasses(self, tmp_path: Path):
        """Should work with subclass types."""
        char = create_character(
            name="Test Champion",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.class_type == "champion"
        assert isinstance(loaded, Champion)

    def test_filename_sanitization(self, tmp_path: Path):
        """Should create safe filenames from character names."""
        char = create_character(
            name="Test Character With Spaces!@#$%",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        filepath = save_character(char, tmp_path)
        assert " " not in filepath.name
        assert "@" not in filepath.name
        assert filepath.exists()

    def test_list_characters(self, tmp_path: Path):
        """Should list all character files in a directory."""
        # Create multiple characters
        for i in range(3):
            char = create_character(
                name=f"Character {i}",
                species_name=SpeciesName.HUMAN,
                class_type="fighter",
            )
            save_character(char, tmp_path)

        files = list_characters(tmp_path)
        assert len(files) == 3
        assert all(f.suffix == ".yaml" for f in files)

    def test_list_characters_empty_directory(self, tmp_path: Path):
        """Should return empty list for empty directory."""
        files = list_characters(tmp_path)
        assert files == []

    def test_list_characters_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        files = list_characters(Path("/nonexistent/path"))
        assert files == []

    def test_delete_character(self, tmp_path: Path):
        """Should delete a character file."""
        char = create_character(
            name="To Delete",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        filepath = save_character(char, tmp_path)
        assert filepath.exists()

        result = delete_character(filepath)
        assert result is True
        assert not filepath.exists()

    def test_delete_nonexistent_character(self, tmp_path: Path):
        """Should return False for nonexistent file."""
        result = delete_character(tmp_path / "nonexistent.yaml")
        assert result is False

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_character(tmp_path / "missing.yaml")

    def test_yaml_is_human_readable(self, tmp_path: Path):
        """The YAML file should be human-readable and editable."""
        char = create_character(
            name="Readable Character",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=AbilityScores(strength=16),
        )

        filepath = save_character(char, tmp_path)

        # Read the raw YAML
        content = filepath.read_text()

        # Should contain readable keys (not Python class names)
        assert "name: Readable Character" in content
        assert "strength: 16" in content
        assert "class_type: fighter" in content

    def test_higher_level_character(self, tmp_path: Path):
        """Should handle higher level characters correctly."""
        char = create_character(
            name="High Level Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=10,
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.level == 10
        assert loaded.proficiency_bonus == 4  # Level 9-12

    def test_round_trip_preserves_calculated_values(self, tmp_path: Path):
        """Loading a character should recalculate derived values correctly."""
        scores = AbilityScores(dexterity=16, wisdom=14)
        char = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            ability_scores=scores,
            skill_proficiencies=[Skill.PERCEPTION],
        )

        original_passive = char.passive_perception
        original_initiative = char.initiative

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.passive_perception == original_passive
        assert loaded.initiative == original_initiative
