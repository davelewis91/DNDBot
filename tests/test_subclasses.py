"""Tests for subclass system."""

from pathlib import Path

import pytest

from dnd_bot.character import (
    ClassName,
    SpeciesName,
    Subclass,
    create_character,
    get_all_subclasses,
    get_subclass,
    get_subclasses_for_class,
    list_subclasses,
    load_character,
    save_character,
)


class TestSubclassModel:
    """Tests for the Subclass model."""

    def test_get_subclass_champion(self):
        """Should retrieve Champion subclass."""
        champion = get_subclass("champion")
        assert champion.name == "Champion"
        assert champion.parent_class == ClassName.FIGHTER
        assert len(champion.features) > 0

    def test_get_subclass_thief(self):
        """Should retrieve Thief subclass."""
        thief = get_subclass("thief")
        assert thief.name == "Thief"
        assert thief.parent_class == ClassName.ROGUE

    def test_get_subclass_berserker(self):
        """Should retrieve Berserker subclass."""
        berserker = get_subclass("berserker")
        assert berserker.name == "Path of the Berserker"
        assert berserker.parent_class == ClassName.BARBARIAN

    def test_get_subclass_open_hand(self):
        """Should retrieve Way of the Open Hand subclass."""
        open_hand = get_subclass("way_of_the_open_hand")
        assert open_hand.name == "Way of the Open Hand"
        assert open_hand.parent_class == ClassName.MONK

    def test_get_subclass_not_found(self):
        """Should raise KeyError for unknown subclass."""
        with pytest.raises(KeyError):
            get_subclass("unknown_subclass")

    def test_get_subclass_returns_copy(self):
        """get_subclass should return a copy, not the original."""
        sub1 = get_subclass("champion")
        sub2 = get_subclass("champion")
        assert sub1 is not sub2


class TestSubclassListing:
    """Tests for listing subclasses."""

    def test_list_all_subclass_ids(self):
        """Should list all available subclass IDs."""
        subclass_ids = list_subclasses()
        assert len(subclass_ids) >= 4  # At least our 4 martial subclasses
        assert all(isinstance(s, str) for s in subclass_ids)
        assert "champion" in subclass_ids
        assert "thief" in subclass_ids

    def test_list_subclasses_by_class(self):
        """Should filter subclass IDs by parent class."""
        fighter_ids = list_subclasses(ClassName.FIGHTER)
        assert len(fighter_ids) >= 1
        assert "champion" in fighter_ids
        # Verify they're all fighter subclasses
        for subclass_id in fighter_ids:
            sub = get_subclass(subclass_id)
            assert sub.parent_class == ClassName.FIGHTER

    def test_get_all_subclasses(self):
        """Should get all subclasses as objects."""
        subclasses = get_all_subclasses()
        assert len(subclasses) >= 4
        assert all(isinstance(s, Subclass) for s in subclasses)

    def test_get_all_subclasses_by_class(self):
        """Should filter subclasses by parent class."""
        fighter_subs = get_all_subclasses(ClassName.FIGHTER)
        assert len(fighter_subs) >= 1
        assert all(s.parent_class == ClassName.FIGHTER for s in fighter_subs)

    def test_get_subclasses_for_class(self):
        """Should get all subclasses for a specific class."""
        rogue_subs = get_subclasses_for_class(ClassName.ROGUE)
        assert len(rogue_subs) >= 1
        assert all(s.parent_class == ClassName.ROGUE for s in rogue_subs)


class TestSubclassFeatures:
    """Tests for subclass feature mechanics."""

    def test_champion_improved_critical(self):
        """Champion should have Improved Critical at level 3."""
        champion = get_subclass("champion")
        features = champion.get_features_at_level(3)
        names = [f.name for f in features]
        assert "Improved Critical" in names

        improved_crit = champion.get_feature_by_name("Improved Critical")
        assert improved_crit is not None
        assert improved_crit.level == 3
        assert improved_crit.mechanic is not None
        assert improved_crit.mechanic.extra_data["critical_range"] == [19, 20]

    def test_champion_superior_critical(self):
        """Champion should have Superior Critical at level 15."""
        champion = get_subclass("champion")
        features = champion.get_features_at_level(15)
        names = [f.name for f in features]
        assert "Superior Critical" in names

        superior_crit = champion.get_feature_by_name("Superior Critical")
        assert superior_crit.mechanic.extra_data["critical_range"] == [18, 19, 20]

    def test_thief_fast_hands(self):
        """Thief should have Fast Hands at level 3."""
        thief = get_subclass("thief")
        fast_hands = thief.get_feature_by_name("Fast Hands")
        assert fast_hands is not None
        assert fast_hands.level == 3

    def test_berserker_frenzy(self):
        """Berserker should have Frenzy at level 3."""
        berserker = get_subclass("berserker")
        frenzy = berserker.get_feature_by_name("Frenzy")
        assert frenzy is not None
        assert frenzy.mechanic.extra_data["bonus_action_attack"] is True

    def test_open_hand_technique(self):
        """Way of the Open Hand should have Open Hand Technique at level 3."""
        open_hand = get_subclass("way_of_the_open_hand")
        technique = open_hand.get_feature_by_name("Open Hand Technique")
        assert technique is not None
        assert "options" in technique.mechanic.extra_data

    def test_open_hand_wholeness_of_body(self):
        """Way of the Open Hand should have Wholeness of Body at level 6."""
        open_hand = get_subclass("way_of_the_open_hand")
        wholeness = open_hand.get_feature_by_name("Wholeness of Body")
        assert wholeness is not None
        assert wholeness.level == 6
        assert wholeness.mechanic.resource_name == "Wholeness of Body"


class TestCharacterSubclass:
    """Tests for character subclass integration."""

    def test_create_character_with_subclass(self):
        """Should create a character with a subclass."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
            subclass_id="champion",
        )
        assert char.subclass is not None
        assert char.subclass.name == "Champion"

    def test_create_character_subclass_requires_level_3(self):
        """Should raise error if subclass set before level 3."""
        with pytest.raises(ValueError, match="level 3"):
            create_character(
                name="Fighter",
                species_name=SpeciesName.HUMAN,
                class_name=ClassName.FIGHTER,
                level=2,
                subclass_id="champion",
            )

    def test_set_subclass_wrong_class(self):
        """Should raise error if subclass doesn't match class."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
        )
        with pytest.raises(ValueError, match="not fighter"):
            char.set_subclass("thief")  # Thief is for Rogue

    def test_set_subclass_success(self):
        """Should successfully set a matching subclass."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
        )
        assert char.set_subclass("champion")
        assert char.subclass.name == "Champion"

    def test_get_all_features_includes_subclass(self):
        """get_all_features should include both class and subclass features."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
            subclass_id="champion",
        )
        features = char.get_all_features()
        names = [f.name for f in features]

        # Class features
        assert "Second Wind" in names
        assert "Action Surge" in names
        # Subclass feature
        assert "Improved Critical" in names

    def test_has_feature(self):
        """has_feature should find both class and subclass features."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
            subclass_id="champion",
        )
        assert char.has_feature("Second Wind")
        assert char.has_feature("Improved Critical")
        assert not char.has_feature("Superior Critical")  # Level 15 feature

    def test_get_critical_range_default(self):
        """Default critical range should be [20]."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
        )
        assert char.get_critical_range() == [20]

    def test_get_critical_range_champion(self):
        """Champion should have critical range [19, 20]."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
            subclass_id="champion",
        )
        assert char.get_critical_range() == [19, 20]

    def test_get_critical_range_champion_level_15(self):
        """Champion at level 15 should have critical range [18, 19, 20]."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=15,
            subclass_id="champion",
        )
        assert char.get_critical_range() == [18, 19, 20]


class TestSubclassResourceRegistration:
    """Tests for subclass resource registration."""

    def test_open_hand_registers_wholeness_of_body(self):
        """Way of the Open Hand should register Wholeness of Body at level 6."""
        char = create_character(
            name="Open Hand Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=6,
            subclass_id="way_of_the_open_hand",
        )

        resource = char.resources.get_feature("Wholeness of Body")
        assert resource is not None
        assert resource.maximum == 1

    def test_subclass_resource_not_registered_below_level(self):
        """Wholeness of Body should not be registered at level 3."""
        char = create_character(
            name="Open Hand Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=3,
            subclass_id="way_of_the_open_hand",
        )

        resource = char.resources.get_feature("Wholeness of Body")
        assert resource is None  # Level 6 feature, not registered at level 3


class TestSubclassStorage:
    """Tests for subclass YAML storage."""

    def test_save_and_load_character_with_subclass(self, tmp_path: Path):
        """Should preserve subclass on save/load."""
        char = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=5,
            subclass_id="champion",
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.subclass is not None
        assert loaded.subclass.id == "champion"
        assert loaded.subclass.name == "Champion"

    def test_save_and_load_character_without_subclass(self, tmp_path: Path):
        """Should handle characters without subclass."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=2,
        )

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.subclass is None

    def test_yaml_contains_subclass(self, tmp_path: Path):
        """YAML file should contain subclass ID."""
        char = create_character(
            name="Thief",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.ROGUE,
            level=3,
            subclass_id="thief",
        )

        filepath = save_character(char, tmp_path)
        content = filepath.read_text()

        assert "subclass: thief" in content

    def test_load_unknown_subclass_graceful(self, tmp_path: Path):
        """Should gracefully handle unknown subclass IDs on load."""
        # Create a character and save it
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
            subclass_id="champion",
        )
        filepath = save_character(char, tmp_path)

        # Manually edit the file to use an unknown subclass
        content = filepath.read_text()
        content = content.replace("subclass: champion", "subclass: unknown_subclass")
        filepath.write_text(content)

        # Should load without error, but subclass should be None
        loaded = load_character(filepath)
        assert loaded.subclass is None
