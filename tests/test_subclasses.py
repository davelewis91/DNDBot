"""Tests for subclass inheritance system."""

from pathlib import Path

from dnd_bot.character import (
    Barbarian,
    Berserker,
    Champion,
    Fighter,
    Monk,
    OpenHand,
    Rogue,
    SpeciesName,
    Thief,
    create_character,
    load_character,
    save_character,
)


class TestChampionSubclass:
    """Tests for Champion subclass (Fighter)."""

    def test_champion_is_fighter(self):
        """Champion should be a subclass of Fighter."""
        champion = create_character(
            name="Test Champion",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )
        assert isinstance(champion, Champion)
        assert isinstance(champion, Fighter)

    def test_champion_has_fighter_features(self):
        """Champion should have all Fighter methods."""
        champion = create_character(
            name="Test Champion",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )
        assert hasattr(champion, "use_second_wind")
        assert hasattr(champion, "use_action_surge")

    def test_champion_critical_range_level_3(self):
        """Champion at level 3+ should have critical range [19, 20]."""
        champion = create_character(
            name="Champion L3",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )
        assert champion.get_critical_range() == [19, 20]

    def test_champion_critical_range_level_15(self):
        """Champion at level 15+ should have critical range [18, 19, 20]."""
        champion = create_character(
            name="Champion L15",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=15,
        )
        assert champion.get_critical_range() == [18, 19, 20]

    def test_champion_level_1_normal_critical(self):
        """Champion below level 3 should have normal critical range."""
        champion = create_character(
            name="Champion L1",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=1,
        )
        assert champion.get_critical_range() == [20]

    def test_fighter_has_default_critical_range(self):
        """Base Fighter should have default critical range [20]."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
        )
        assert fighter.get_critical_range() == [20]


class TestBerserkerSubclass:
    """Tests for Berserker subclass (Barbarian)."""

    def test_berserker_is_barbarian(self):
        """Berserker should be a subclass of Barbarian."""
        berserker = create_character(
            name="Test Berserker",
            species_name=SpeciesName.HUMAN,
            class_type="berserker",
            level=3,
        )
        assert isinstance(berserker, Berserker)
        assert isinstance(berserker, Barbarian)

    def test_berserker_has_barbarian_features(self):
        """Berserker should have all Barbarian methods."""
        berserker = create_character(
            name="Test Berserker",
            species_name=SpeciesName.HUMAN,
            class_type="berserker",
            level=3,
        )
        assert hasattr(berserker, "start_rage")
        assert hasattr(berserker, "can_rage")
        assert hasattr(berserker, "get_rage_damage_bonus")

    def test_berserker_intimidating_presence_dc(self):
        """Berserker should calculate intimidating presence DC."""
        berserker = create_character(
            name="Berserker",
            species_name=SpeciesName.HUMAN,
            class_type="berserker",
            level=10,
        )
        # DC = 8 + proficiency + CHA mod
        # Level 10 proficiency = 4, default CHA = 10 (mod 0)
        assert berserker.get_intimidating_presence_dc() == 12


class TestThiefSubclass:
    """Tests for Thief subclass (Rogue)."""

    def test_thief_is_rogue(self):
        """Thief should be a subclass of Rogue."""
        thief = create_character(
            name="Test Thief",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=3,
        )
        assert isinstance(thief, Thief)
        assert isinstance(thief, Rogue)

    def test_thief_has_rogue_features(self):
        """Thief should have all Rogue methods."""
        thief = create_character(
            name="Test Thief",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=3,
        )
        assert hasattr(thief, "get_sneak_attack_dice")
        assert hasattr(thief, "has_evasion")

    def test_thief_jump_bonus(self):
        """Thief should have jump bonus based on DEX mod."""
        thief = create_character(
            name="Thief",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=3,
        )
        # Default DEX = 10 (mod 0)
        assert thief.get_jump_bonus() == 0

    def test_thief_supreme_sneak_at_level_9(self):
        """Thief should have Supreme Sneak at level 9+."""
        thief_8 = create_character(
            name="Thief L8",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=8,
        )
        assert not thief_8.has_supreme_sneak()

        thief_9 = create_character(
            name="Thief L9",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=9,
        )
        assert thief_9.has_supreme_sneak()


class TestOpenHandSubclass:
    """Tests for Way of the Open Hand subclass (Monk)."""

    def test_open_hand_is_monk(self):
        """OpenHand should be a subclass of Monk."""
        open_hand = create_character(
            name="Test OpenHand",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=3,
        )
        assert isinstance(open_hand, OpenHand)
        assert isinstance(open_hand, Monk)

    def test_open_hand_has_monk_features(self):
        """OpenHand should have all Monk methods."""
        open_hand = create_character(
            name="Test OpenHand",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=3,
        )
        assert hasattr(open_hand, "use_focus_points")
        assert hasattr(open_hand, "get_focus_points")
        assert hasattr(open_hand, "get_martial_arts_die")

    def test_open_hand_wholeness_of_body(self):
        """OpenHand should be able to use Wholeness of Body at level 6+."""
        open_hand_6 = create_character(
            name="OpenHand L6",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=6,
        )
        initial_hp = 1
        open_hand_6.current_hp = initial_hp

        healed = open_hand_6.use_wholeness_of_body()

        # Should heal Martial Arts die (1d8 at level 6) + WIS mod (0 with default 10)
        # So 1-8 HP healed
        assert 1 <= healed <= 8
        assert open_hand_6.current_hp == initial_hp + healed

    def test_open_hand_quivering_palm_dc(self):
        """OpenHand should calculate Quivering Palm DC at level 17+."""
        open_hand = create_character(
            name="OpenHand L17",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=17,
        )
        # DC = 8 + proficiency + WIS mod
        # Level 17 proficiency = 6, default WIS = 10 (mod 0)
        assert open_hand.get_quivering_palm_dc() == 14


class TestSubclassStorage:
    """Tests for subclass YAML storage."""

    def test_save_and_load_champion(self, tmp_path: Path):
        """Should preserve Champion subclass on save/load."""
        champion = create_character(
            name="Champion Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=5,
        )

        filepath = save_character(champion, tmp_path)
        loaded = load_character(filepath)

        assert isinstance(loaded, Champion)
        assert loaded.class_type == "champion"
        assert loaded.get_critical_range() == [19, 20]

    def test_save_and_load_berserker(self, tmp_path: Path):
        """Should preserve Berserker subclass on save/load."""
        berserker = create_character(
            name="Berserker",
            species_name=SpeciesName.HUMAN,
            class_type="berserker",
            level=5,
        )

        filepath = save_character(berserker, tmp_path)
        loaded = load_character(filepath)

        assert isinstance(loaded, Berserker)
        assert loaded.class_type == "berserker"

    def test_save_and_load_thief(self, tmp_path: Path):
        """Should preserve Thief subclass on save/load."""
        thief = create_character(
            name="Thief",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=5,
        )

        filepath = save_character(thief, tmp_path)
        loaded = load_character(filepath)

        assert isinstance(loaded, Thief)
        assert loaded.class_type == "thief"

    def test_save_and_load_open_hand(self, tmp_path: Path):
        """Should preserve OpenHand subclass on save/load."""
        open_hand = create_character(
            name="Open Hand Monk",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=5,
        )

        filepath = save_character(open_hand, tmp_path)
        loaded = load_character(filepath)

        assert isinstance(loaded, OpenHand)
        assert loaded.class_type == "openhand"

    def test_yaml_contains_class_type(self, tmp_path: Path):
        """YAML file should contain class_type field."""
        champion = create_character(
            name="Champion",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )

        filepath = save_character(champion, tmp_path)
        content = filepath.read_text()

        assert "class_type: champion" in content


class TestSubclassClassFeatures:
    """Tests for subclass class_features property."""

    def test_champion_includes_improved_critical_feature(self):
        """Champion should have Improved Critical in class_features at level 3+."""
        champion = create_character(
            name="Champion",
            species_name=SpeciesName.HUMAN,
            class_type="champion",
            level=3,
        )
        feature_names = [f.name for f in champion.class_features]

        # Should have Fighter features
        assert "Second Wind" in feature_names
        assert "Action Surge" in feature_names
        # Should have Champion feature
        assert "Improved Critical" in feature_names

    def test_berserker_includes_frenzy_feature(self):
        """Berserker should have Frenzy in class_features at level 3+."""
        berserker = create_character(
            name="Berserker",
            species_name=SpeciesName.HUMAN,
            class_type="berserker",
            level=3,
        )
        feature_names = [f.name for f in berserker.class_features]

        # Should have Barbarian features
        assert "Rage" in feature_names
        # Should have Berserker feature
        assert "Frenzy" in feature_names

    def test_thief_includes_fast_hands_feature(self):
        """Thief should have Fast Hands in class_features at level 3+."""
        thief = create_character(
            name="Thief",
            species_name=SpeciesName.HUMAN,
            class_type="thief",
            level=3,
        )
        feature_names = [f.name for f in thief.class_features]

        # Should have Rogue features
        assert "Sneak Attack" in feature_names
        assert "Cunning Action" in feature_names
        # Should have Thief feature
        assert "Fast Hands" in feature_names

    def test_open_hand_includes_technique_feature(self):
        """OpenHand should have Open Hand Technique in class_features at level 3+."""
        open_hand = create_character(
            name="OpenHand",
            species_name=SpeciesName.HUMAN,
            class_type="openhand",
            level=3,
        )
        feature_names = [f.name for f in open_hand.class_features]

        # Should have Monk features
        assert "Martial Arts" in feature_names
        assert "Focus" in feature_names
        # Should have OpenHand feature
        assert "Open Hand Technique" in feature_names
