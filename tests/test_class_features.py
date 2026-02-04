"""Tests for class feature mechanics."""

from dnd_bot.character import (
    ClassFeature,
    FeatureMechanic,
    FeatureMechanicType,
    RestType,
    SpeciesName,
    create_character,
    get_martial_arts_die,
    get_rage_damage_bonus,
    get_rage_uses,
    get_sneak_attack_dice,
)


class TestFeatureMechanic:
    """Tests for the FeatureMechanic model."""

    def test_passive_mechanic(self):
        """Passive mechanics have no resources."""
        mechanic = FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE)
        assert mechanic.mechanic_type == FeatureMechanicType.PASSIVE
        assert mechanic.resource_name is None

    def test_resource_mechanic(self):
        """Resource mechanics track uses per rest."""
        mechanic = FeatureMechanic(
            mechanic_type=FeatureMechanicType.RESOURCE,
            resource_name="Second Wind",
            uses_per_rest=1,
            recover_on=RestType.SHORT,
            dice="1d10",
        )
        assert mechanic.resource_name == "Second Wind"
        assert mechanic.uses_per_rest == 1
        assert mechanic.recover_on == RestType.SHORT
        assert mechanic.dice == "1d10"

    def test_toggle_mechanic(self):
        """Toggle mechanics can be activated/deactivated."""
        mechanic = FeatureMechanic(
            mechanic_type=FeatureMechanicType.TOGGLE,
            resource_name="Rage",
            uses_per_rest=2,
            recover_on=RestType.LONG,
        )
        assert mechanic.mechanic_type == FeatureMechanicType.TOGGLE
        assert mechanic.recover_on == RestType.LONG


class TestClassFeatures:
    """Tests for class feature definitions."""

    def test_fighter_has_second_wind_feature(self):
        """Fighter should have Second Wind feature at level 1."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=1,
        )
        feature_names = [f.name for f in fighter.class_features]
        assert "Second Wind" in feature_names

    def test_fighter_has_action_surge_at_level_2(self):
        """Fighter should have Action Surge feature at level 2."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )
        feature_names = [f.name for f in fighter.class_features]
        assert "Action Surge" in feature_names

    def test_fighter_level_1_no_action_surge(self):
        """Level 1 Fighter should not have Action Surge."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=1,
        )
        feature_names = [f.name for f in fighter.class_features]
        assert "Action Surge" not in feature_names

    def test_barbarian_has_rage_feature(self):
        """Barbarian should have Rage feature at level 1."""
        barbarian = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=1,
        )
        feature_names = [f.name for f in barbarian.class_features]
        assert "Rage" in feature_names

    def test_rogue_has_sneak_attack_feature(self):
        """Rogue should have Sneak Attack feature at level 1."""
        rogue = create_character(
            name="Rogue",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=1,
        )
        feature_names = [f.name for f in rogue.class_features]
        assert "Sneak Attack" in feature_names

    def test_monk_has_martial_arts_feature(self):
        """Monk should have Martial Arts feature at level 1."""
        monk = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=1,
        )
        feature_names = [f.name for f in monk.class_features]
        assert "Martial Arts" in feature_names


class TestSneakAttackDice:
    """Tests for Sneak Attack dice calculation."""

    def test_sneak_attack_level_1(self):
        """Level 1 Rogue gets 1d6 Sneak Attack."""
        assert get_sneak_attack_dice(1) == 1

    def test_sneak_attack_level_3(self):
        """Level 3 Rogue gets 2d6 Sneak Attack."""
        assert get_sneak_attack_dice(3) == 2

    def test_sneak_attack_level_5(self):
        """Level 5 Rogue gets 3d6 Sneak Attack."""
        assert get_sneak_attack_dice(5) == 3

    def test_sneak_attack_level_20(self):
        """Level 20 Rogue gets 10d6 Sneak Attack."""
        assert get_sneak_attack_dice(20) == 10


class TestRageProgression:
    """Tests for Barbarian Rage progression."""

    def test_rage_uses_level_1(self):
        """Level 1 Barbarian has 2 Rages."""
        assert get_rage_uses(1) == 2

    def test_rage_uses_level_3(self):
        """Level 3 Barbarian has 3 Rages."""
        assert get_rage_uses(3) == 3

    def test_rage_uses_level_6(self):
        """Level 6 Barbarian has 4 Rages."""
        assert get_rage_uses(6) == 4

    def test_rage_uses_level_17(self):
        """Level 17 Barbarian has 6 Rages."""
        assert get_rage_uses(17) == 6

    def test_rage_damage_level_1(self):
        """Level 1 Barbarian has +2 Rage damage."""
        assert get_rage_damage_bonus(1) == 2

    def test_rage_damage_level_9(self):
        """Level 9 Barbarian has +3 Rage damage."""
        assert get_rage_damage_bonus(9) == 3

    def test_rage_damage_level_16(self):
        """Level 16 Barbarian has +4 Rage damage."""
        assert get_rage_damage_bonus(16) == 4


class TestMartialArtsDie:
    """Tests for Monk Martial Arts die progression."""

    def test_martial_arts_level_1(self):
        """Level 1 Monk uses 1d6."""
        assert get_martial_arts_die(1) == "1d6"

    def test_martial_arts_level_5(self):
        """Level 5 Monk uses 1d8."""
        assert get_martial_arts_die(5) == "1d8"

    def test_martial_arts_level_11(self):
        """Level 11 Monk uses 1d10."""
        assert get_martial_arts_die(11) == "1d10"

    def test_martial_arts_level_17(self):
        """Level 17 Monk uses 1d12."""
        assert get_martial_arts_die(17) == "1d12"


class TestCharacterResourceRegistration:
    """Tests for automatic resource registration on character creation."""

    def test_fighter_registers_second_wind(self):
        """Fighter should have Second Wind resource registered."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        assert fighter.resources.has_feature_available("Second Wind")
        resource = fighter.resources.get_feature("Second Wind")
        assert resource is not None
        assert resource.maximum == 1
        assert resource.recover_on == RestType.SHORT

    def test_fighter_level_2_registers_action_surge(self):
        """Level 2 Fighter should have Action Surge resource registered."""
        fighter = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )

        assert fighter.resources.has_feature_available("Action Surge")
        resource = fighter.resources.get_feature("Action Surge")
        assert resource is not None
        assert resource.maximum == 1

    def test_barbarian_registers_rage(self):
        """Barbarian should have Rage resource registered."""
        barbarian = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
        )

        assert barbarian.resources.has_feature_available("Rage")
        resource = barbarian.resources.get_feature("Rage")
        assert resource is not None
        assert resource.maximum == 2  # Level 1

    def test_barbarian_level_3_has_more_rages(self):
        """Level 3 Barbarian should have 3 Rages."""
        barbarian = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=3,
        )

        resource = barbarian.resources.get_feature("Rage")
        assert resource is not None
        assert resource.maximum == 3

    def test_monk_registers_focus_points(self):
        """Monk should have Focus Points resource registered."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=2,
        )

        assert monk.resources.has_feature_available("Focus Points")
        resource = monk.resources.get_feature("Focus Points")
        assert resource is not None
        assert resource.maximum == 2  # Equal to level

    def test_monk_level_5_has_5_focus_points(self):
        """Level 5 Monk should have 5 Focus Points."""
        monk = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=5,
        )

        resource = monk.resources.get_feature("Focus Points")
        assert resource is not None
        assert resource.maximum == 5

    def test_rogue_has_no_resource_features(self):
        """Rogue should not register resource features (Sneak Attack is passive)."""
        rogue = create_character(
            name="Test Rogue",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
        )

        # Rogue's features are all passive, no resources to track
        assert len(rogue.resources.feature_uses) == 0


class TestFighterFeatureUsage:
    """Tests for Fighter class feature usage."""

    def test_use_second_wind(self):
        """Second Wind should heal 1d10 + level."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
        )
        fighter.current_hp = 10  # Take some damage

        healed = fighter.use_second_wind()

        # Should heal between 6 (1+5) and 15 (10+5)
        assert 6 <= healed <= 15
        assert fighter.current_hp >= 16  # At least 10 + 6

    def test_second_wind_uses_resource(self):
        """Second Wind should consume the resource."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        fighter.current_hp = 5

        assert fighter.can_use_second_wind()
        fighter.use_second_wind()
        assert not fighter.can_use_second_wind()

    def test_second_wind_fails_when_exhausted(self):
        """Second Wind should fail when resource is exhausted."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        fighter.current_hp = 5
        fighter.use_second_wind()  # Use the one charge

        healed = fighter.use_second_wind()
        assert healed == 0

    def test_second_wind_recovers_on_short_rest(self):
        """Second Wind should recover on short rest."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        fighter.current_hp = 5
        fighter.use_second_wind()
        assert not fighter.can_use_second_wind()

        fighter.short_rest()
        assert fighter.can_use_second_wind()

    def test_use_action_surge(self):
        """Action Surge should consume the resource."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )

        assert fighter.can_use_action_surge()
        assert fighter.use_action_surge()
        assert not fighter.can_use_action_surge()

    def test_action_surge_fails_at_level_1(self):
        """Action Surge should not be available at level 1."""
        fighter = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=1,
        )

        assert not fighter.can_use_action_surge()
        assert not fighter.use_action_surge()


class TestBarbarianFeatureUsage:
    """Tests for Barbarian class feature usage."""

    def test_start_rage(self):
        """Starting rage should consume a Rage use."""
        barbarian = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
        )

        assert barbarian.can_rage()
        assert barbarian.start_rage()

        resource = barbarian.resources.get_feature("Rage")
        assert resource.current == 1  # Used 1 of 2

    def test_rage_damage_bonus(self):
        """Should return correct rage damage bonus for level."""
        barbarian = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
            level=9,
        )

        assert barbarian.get_rage_damage_bonus() == 3

    def test_rage_recovers_on_long_rest(self):
        """Rage should recover on long rest."""
        barbarian = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_type="barbarian",
        )

        barbarian.start_rage()
        barbarian.start_rage()
        assert not barbarian.can_rage()

        barbarian.long_rest()
        assert barbarian.can_rage()
        resource = barbarian.resources.get_feature("Rage")
        assert resource.current == 2


class TestMonkFeatureUsage:
    """Tests for Monk class feature usage."""

    def test_use_focus_points(self):
        """Using Focus Points should consume the resource."""
        monk = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=5,
        )

        assert monk.get_focus_points() == 5
        assert monk.use_focus_points(2)
        assert monk.get_focus_points() == 3

    def test_focus_points_recover_on_short_rest(self):
        """Focus Points should recover on short rest."""
        monk = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_type="monk",
            level=3,
        )

        monk.use_focus_points(3)
        assert monk.get_focus_points() == 0

        monk.short_rest()
        assert monk.get_focus_points() == 3


class TestRogueFeatureUsage:
    """Tests for Rogue class feature usage."""

    def test_sneak_attack_dice(self):
        """Should return correct Sneak Attack dice for Rogue level."""
        rogue = create_character(
            name="Rogue",
            species_name=SpeciesName.HUMAN,
            class_type="rogue",
            level=5,
        )

        assert rogue.get_sneak_attack_dice() == 3  # 3d6 at level 5
