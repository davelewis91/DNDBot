"""Tests for class feature mechanics."""

from dnd_bot.character import (
    ClassName,
    FeatureMechanic,
    FeatureMechanicType,
    RestType,
    SpeciesName,
    calculate_resource_uses,
    create_character,
    get_class,
    get_martial_arts_die,
    get_rage_damage_bonus,
    get_rage_uses,
    get_resource_features,
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


class TestClassFeatureMechanics:
    """Tests for class feature mechanics on classes."""

    def test_fighter_has_second_wind_mechanic(self):
        """Fighter's Second Wind should have resource mechanic."""
        fighter = get_class(ClassName.FIGHTER)
        second_wind = next(f for f in fighter.features if f.name == "Second Wind")

        assert second_wind.mechanic is not None
        assert second_wind.mechanic.mechanic_type == FeatureMechanicType.RESOURCE
        assert second_wind.mechanic.resource_name == "Second Wind"
        assert second_wind.mechanic.uses_per_rest == 1
        assert second_wind.mechanic.recover_on == RestType.SHORT
        assert second_wind.mechanic.dice == "1d10"

    def test_fighter_has_action_surge_mechanic(self):
        """Fighter's Action Surge should have resource mechanic."""
        fighter = get_class(ClassName.FIGHTER)
        action_surge = next(f for f in fighter.features if f.name == "Action Surge")

        assert action_surge.mechanic is not None
        assert action_surge.mechanic.mechanic_type == FeatureMechanicType.RESOURCE
        assert action_surge.mechanic.resource_name == "Action Surge"
        assert action_surge.mechanic.recover_on == RestType.SHORT

    def test_rogue_has_sneak_attack_mechanic(self):
        """Rogue's Sneak Attack should have passive mechanic with scaling."""
        rogue = get_class(ClassName.ROGUE)
        sneak_attack = next(f for f in rogue.features if f.name == "Sneak Attack")

        assert sneak_attack.mechanic is not None
        assert sneak_attack.mechanic.mechanic_type == FeatureMechanicType.PASSIVE
        assert sneak_attack.mechanic.dice_per_level == "1d6"

    def test_barbarian_has_rage_mechanic(self):
        """Barbarian's Rage should have toggle mechanic."""
        barbarian = get_class(ClassName.BARBARIAN)
        rage = next(f for f in barbarian.features if f.name == "Rage")

        assert rage.mechanic is not None
        assert rage.mechanic.mechanic_type == FeatureMechanicType.TOGGLE
        assert rage.mechanic.resource_name == "Rage"
        assert rage.mechanic.recover_on == RestType.LONG

    def test_monk_has_focus_points_mechanic(self):
        """Monk's Focus should have resource mechanic scaling with level."""
        monk = get_class(ClassName.MONK)
        focus = next(f for f in monk.features if f.name == "Focus")

        assert focus.mechanic is not None
        assert focus.mechanic.mechanic_type == FeatureMechanicType.RESOURCE
        assert focus.mechanic.resource_name == "Focus Points"
        assert focus.mechanic.uses_per_rest_formula == "level"
        assert focus.mechanic.recover_on == RestType.SHORT


class TestResourceFeatureHelpers:
    """Tests for helper functions."""

    def test_get_resource_features_fighter(self):
        """Should return Second Wind and Action Surge for level 2+ Fighter."""
        fighter = get_class(ClassName.FIGHTER)
        features = get_resource_features(fighter, level=2)

        names = [f.name for f in features]
        assert "Second Wind" in names
        assert "Action Surge" in names

    def test_get_resource_features_level_filter(self):
        """Should only return features at or below the given level."""
        fighter = get_class(ClassName.FIGHTER)

        level_1_features = get_resource_features(fighter, level=1)
        level_2_features = get_resource_features(fighter, level=2)

        assert len(level_1_features) == 1  # Just Second Wind
        assert len(level_2_features) == 2  # Second Wind + Action Surge

    def test_calculate_resource_uses_fixed(self):
        """Fixed uses should return the configured amount."""
        fighter = get_class(ClassName.FIGHTER)
        second_wind = next(f for f in fighter.features if f.name == "Second Wind")

        assert calculate_resource_uses(second_wind, level=5) == 1
        assert calculate_resource_uses(second_wind, level=10) == 1

    def test_calculate_resource_uses_formula(self):
        """Formula-based uses should scale with level."""
        monk = get_class(ClassName.MONK)
        focus = next(f for f in monk.features if f.name == "Focus")

        assert calculate_resource_uses(focus, level=2) == 2
        assert calculate_resource_uses(focus, level=5) == 5
        assert calculate_resource_uses(focus, level=10) == 10


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
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )

        assert char.resources.has_feature_available("Second Wind")
        resource = char.resources.get_feature("Second Wind")
        assert resource is not None
        assert resource.maximum == 1
        assert resource.recover_on == RestType.SHORT

    def test_fighter_level_2_registers_action_surge(self):
        """Level 2 Fighter should have Action Surge resource registered."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=2,
        )

        assert char.resources.has_feature_available("Action Surge")
        resource = char.resources.get_feature("Action Surge")
        assert resource is not None
        assert resource.maximum == 1

    def test_barbarian_registers_rage(self):
        """Barbarian should have Rage resource registered."""
        char = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
        )

        assert char.resources.has_feature_available("Rage")
        resource = char.resources.get_feature("Rage")
        assert resource is not None
        assert resource.maximum == 2  # Level 1

    def test_barbarian_level_3_has_more_rages(self):
        """Level 3 Barbarian should have 3 Rages."""
        char = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
            level=3,
        )

        resource = char.resources.get_feature("Rage")
        assert resource is not None
        assert resource.maximum == 3

    def test_monk_registers_focus_points(self):
        """Monk should have Focus Points resource registered."""
        char = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=2,
        )

        assert char.resources.has_feature_available("Focus Points")
        resource = char.resources.get_feature("Focus Points")
        assert resource is not None
        assert resource.maximum == 2  # Equal to level

    def test_monk_level_5_has_5_focus_points(self):
        """Level 5 Monk should have 5 Focus Points."""
        char = create_character(
            name="Test Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=5,
        )

        resource = char.resources.get_feature("Focus Points")
        assert resource is not None
        assert resource.maximum == 5

    def test_rogue_has_no_resource_features(self):
        """Rogue should not register resource features (Sneak Attack is passive)."""
        char = create_character(
            name="Test Rogue",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.ROGUE,
        )

        # Rogue's features are all passive, no resources to track
        assert len(char.resources.feature_uses) == 0


class TestFighterFeatureUsage:
    """Tests for Fighter class feature usage."""

    def test_use_second_wind(self):
        """Second Wind should heal 1d10 + level."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=5,
        )
        char.current_hp = 10  # Take some damage

        healed = char.use_second_wind()

        # Should heal between 6 (1+5) and 15 (10+5)
        assert 6 <= healed <= 15
        assert char.current_hp >= 16  # At least 10 + 6

    def test_second_wind_uses_resource(self):
        """Second Wind should consume the resource."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.current_hp = 5

        assert char.can_use_second_wind()
        char.use_second_wind()
        assert not char.can_use_second_wind()

    def test_second_wind_fails_when_exhausted(self):
        """Second Wind should fail when resource is exhausted."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.current_hp = 5
        char.use_second_wind()  # Use the one charge

        healed = char.use_second_wind()
        assert healed == 0

    def test_second_wind_recovers_on_short_rest(self):
        """Second Wind should recover on short rest."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.current_hp = 5
        char.use_second_wind()
        assert not char.can_use_second_wind()

        char.short_rest()
        assert char.can_use_second_wind()

    def test_use_action_surge(self):
        """Action Surge should consume the resource."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=2,
        )

        assert char.can_use_action_surge()
        assert char.use_action_surge()
        assert not char.can_use_action_surge()

    def test_action_surge_fails_at_level_1(self):
        """Action Surge should not be available at level 1."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=1,
        )

        assert not char.can_use_action_surge()
        assert not char.use_action_surge()

    def test_non_fighter_cannot_use_second_wind(self):
        """Non-Fighters should not be able to use Second Wind."""
        char = create_character(
            name="Rogue",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.ROGUE,
        )

        assert not char.can_use_second_wind()
        assert char.use_second_wind() == 0


class TestBarbarianFeatureUsage:
    """Tests for Barbarian class feature usage."""

    def test_start_rage(self):
        """Starting rage should consume a Rage use."""
        char = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
        )

        assert char.can_rage()
        assert char.start_rage()

        resource = char.resources.get_feature("Rage")
        assert resource.current == 1  # Used 1 of 2

    def test_rage_damage_bonus(self):
        """Should return correct rage damage bonus for level."""
        char = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
            level=9,
        )

        assert char.get_rage_damage_bonus() == 3

    def test_rage_recovers_on_long_rest(self):
        """Rage should recover on long rest."""
        char = create_character(
            name="Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
        )

        char.start_rage()
        char.start_rage()
        assert not char.can_rage()

        char.long_rest()
        assert char.can_rage()
        resource = char.resources.get_feature("Rage")
        assert resource.current == 2

    def test_non_barbarian_cannot_rage(self):
        """Non-Barbarians should not be able to rage."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )

        assert not char.can_rage()
        assert not char.start_rage()


class TestMonkFeatureUsage:
    """Tests for Monk class feature usage."""

    def test_use_focus_points(self):
        """Using Focus Points should consume the resource."""
        char = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=5,
        )

        assert char.get_focus_points() == 5
        assert char.use_focus_points(2)
        assert char.get_focus_points() == 3

    def test_focus_points_recover_on_short_rest(self):
        """Focus Points should recover on short rest."""
        char = create_character(
            name="Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            level=3,
        )

        char.use_focus_points(3)
        assert char.get_focus_points() == 0

        char.short_rest()
        assert char.get_focus_points() == 3

    def test_non_monk_has_no_focus_points(self):
        """Non-Monks should have 0 Focus Points."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )

        assert char.get_focus_points() == 0
        assert not char.use_focus_points()


class TestRogueFeatureUsage:
    """Tests for Rogue class feature usage."""

    def test_sneak_attack_dice(self):
        """Should return correct Sneak Attack dice for Rogue level."""
        char = create_character(
            name="Rogue",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.ROGUE,
            level=5,
        )

        assert char.get_sneak_attack_dice() == 3  # 3d6 at level 5

    def test_non_rogue_has_no_sneak_attack(self):
        """Non-Rogues should have 0 Sneak Attack dice."""
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )

        assert char.get_sneak_attack_dice() == 0
