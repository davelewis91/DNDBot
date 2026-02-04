"""Tests for class-specific abilities on character classes."""

from dnd_bot.character import (
    Barbarian,
    Fighter,
    Monk,
    Rogue,
    SpeciesName,
    create_character,
)


class TestFighterMethods:
    """Tests for Fighter-specific methods."""

    def test_fighter_has_second_wind_method(self):
        """Fighter should have use_second_wind method."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        assert isinstance(fighter, Fighter)
        assert hasattr(fighter, "use_second_wind")
        assert hasattr(fighter, "can_use_second_wind")

    def test_fighter_has_action_surge_method(self):
        """Fighter should have action surge methods."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )
        assert hasattr(fighter, "use_action_surge")
        assert hasattr(fighter, "can_use_action_surge")

    def test_second_wind_heals_character(self):
        """use_second_wind should heal the character."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=3,
        )
        fighter.current_hp = 10

        healed = fighter.use_second_wind()

        # 1d10 + 3 = 4 to 13 HP healed
        assert 4 <= healed <= 13
        assert fighter.current_hp >= 14

    def test_action_surge_uses_resource(self):
        """use_action_surge should consume the Action Surge resource."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )

        assert fighter.can_use_action_surge()
        assert fighter.use_action_surge()
        assert not fighter.can_use_action_surge()

    def test_extra_attack_count(self):
        """Fighter should have correct extra attack count by level."""
        fighter_1 = create_character(
            name="Fighter L1",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=1,
        )
        assert fighter_1.get_extra_attack_count() == 1

        fighter_5 = create_character(
            name="Fighter L5",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
        )
        assert fighter_5.get_extra_attack_count() == 2

        fighter_11 = create_character(
            name="Fighter L11",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=11,
        )
        assert fighter_11.get_extra_attack_count() == 3

        fighter_20 = create_character(
            name="Fighter L20",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=20,
        )
        assert fighter_20.get_extra_attack_count() == 4


class TestBarbarianMethods:
    """Tests for Barbarian-specific methods."""

    def test_barbarian_has_rage_methods(self):
        """Barbarian should have rage methods."""
        barbarian = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
        )
        assert isinstance(barbarian, Barbarian)
        assert hasattr(barbarian, "start_rage")
        assert hasattr(barbarian, "can_rage")
        assert hasattr(barbarian, "get_rage_damage_bonus")

    def test_rage_uses_resource(self):
        """start_rage should consume a Rage use."""
        barbarian = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
        )

        assert barbarian.can_rage()
        assert barbarian.start_rage()

        resource = barbarian.resources.get_feature("Rage")
        assert resource.current == 1  # Used 1 of 2

    def test_rage_damage_bonus_scales_with_level(self):
        """get_rage_damage_bonus should return correct value for level."""
        # Level 1 = +2
        barb1 = create_character(
            name="Barbarian L1",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=1,
        )
        assert barb1.get_rage_damage_bonus() == 2

        # Level 9 = +3
        barb9 = create_character(
            name="Barbarian L9",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=9,
        )
        assert barb9.get_rage_damage_bonus() == 3

        # Level 16 = +4
        barb16 = create_character(
            name="Barbarian L16",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=16,
        )
        assert barb16.get_rage_damage_bonus() == 4


class TestMonkMethods:
    """Tests for Monk-specific methods."""

    def test_monk_has_focus_methods(self):
        """Monk should have focus point methods."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=2,
        )
        assert isinstance(monk, Monk)
        assert hasattr(monk, "use_focus_points")
        assert hasattr(monk, "get_focus_points")
        assert hasattr(monk, "get_martial_arts_die")

    def test_focus_points_equal_to_level(self):
        """get_focus_points should return level for a fresh Monk."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=5,
        )

        assert monk.get_focus_points() == 5

    def test_use_focus_points_decrements(self):
        """use_focus_points should decrement the resource."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=5,
        )

        assert monk.use_focus_points(2)
        assert monk.get_focus_points() == 3

    def test_use_focus_points_fails_when_insufficient(self):
        """use_focus_points should fail if not enough points."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=2,
        )

        # Try to spend more than available
        assert not monk.use_focus_points(10)
        assert monk.get_focus_points() == 2  # Unchanged

    def test_martial_arts_die_scales_with_level(self):
        """get_martial_arts_die should return correct die for level."""
        monk_1 = create_character(
            name="Monk L1",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=1,
        )
        assert monk_1.get_martial_arts_die() == "1d6"

        monk_5 = create_character(
            name="Monk L5",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=5,
        )
        assert monk_5.get_martial_arts_die() == "1d8"

        monk_11 = create_character(
            name="Monk L11",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=11,
        )
        assert monk_11.get_martial_arts_die() == "1d10"

        monk_17 = create_character(
            name="Monk L17",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=17,
        )
        assert monk_17.get_martial_arts_die() == "1d12"


class TestRogueMethods:
    """Tests for Rogue-specific methods."""

    def test_rogue_has_sneak_attack_method(self):
        """Rogue should have sneak attack methods."""
        rogue = create_character(
            name="Test Rogue",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
        )
        assert isinstance(rogue, Rogue)
        assert hasattr(rogue, "get_sneak_attack_dice")

    def test_sneak_attack_dice_scales_with_level(self):
        """get_sneak_attack_dice should return correct dice for level."""
        # Level 1 = 1d6
        rogue1 = create_character(
            name="Rogue L1",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=1,
        )
        assert rogue1.get_sneak_attack_dice() == 1

        # Level 5 = 3d6
        rogue5 = create_character(
            name="Rogue L5",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=5,
        )
        assert rogue5.get_sneak_attack_dice() == 3

        # Level 20 = 10d6
        rogue20 = create_character(
            name="Rogue L20",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=20,
        )
        assert rogue20.get_sneak_attack_dice() == 10

    def test_rogue_has_evasion_at_level_7(self):
        """Rogue should have evasion at level 7+."""
        rogue_5 = create_character(
            name="Rogue L5",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=5,
        )
        assert not rogue_5.has_evasion()

        rogue_7 = create_character(
            name="Rogue L7",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=7,
        )
        assert rogue_7.has_evasion()

    def test_rogue_has_uncanny_dodge_at_level_5(self):
        """Rogue should have uncanny dodge at level 5+."""
        rogue_4 = create_character(
            name="Rogue L4",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=4,
        )
        assert not rogue_4.has_uncanny_dodge()

        rogue_5 = create_character(
            name="Rogue L5",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=5,
        )
        assert rogue_5.has_uncanny_dodge()
