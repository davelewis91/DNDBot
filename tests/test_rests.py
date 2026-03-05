"""Tests for the rest system."""

from dnd_bot.character import (
    AbilityScores,
    RestResult,
    RestType,
    SpeciesName,
    create_character,
)


class TestRestResult:
    """Tests for the RestResult class."""

    def test_create_short_rest_result(self):
        """Should create a short rest result."""
        result = RestResult(rest_type=RestType.SHORT)
        assert result.rest_type == RestType.SHORT
        assert result.success is True
        assert result.ends_session is False

    def test_create_long_rest_result(self):
        """Should create a long rest result with ends_session."""
        result = RestResult(rest_type=RestType.LONG, ends_session=True)
        assert result.rest_type == RestType.LONG
        assert result.ends_session is True


class TestSpendHitDie:
    """Tests for spending hit dice."""

    def test_spend_hit_die_heals(self):
        """Spending a hit die should heal the character."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=AbilityScores(constitution=14),  # +2 CON mod
        )
        char.take_damage(10)
        initial_hp = char.current_hp

        healed = char.spend_hit_die()

        assert healed > 0
        assert char.current_hp == initial_hp + healed
        assert char.resources.hit_dice.current == 0  # Level 1, started with 1

    def test_spend_hit_die_minimum_one(self):
        """Spending hit die should heal at least 1 HP even with negative CON."""
        char = create_character(
            name="Sickly Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=AbilityScores(constitution=3),  # -4 CON mod
        )
        char.take_damage(5)

        healed = char.spend_hit_die()

        assert healed >= 1  # Minimum 1 HP

    def test_spend_hit_die_no_dice_available(self):
        """Should return 0 when no hit dice available."""
        char = create_character(
            name="Exhausted Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        # Spend all hit dice
        char.resources.hit_dice.current = 0

        healed = char.spend_hit_die()

        assert healed == 0

    def test_spend_multiple_hit_dice(self):
        """Should be able to spend multiple hit dice."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=3,
            ability_scores=AbilityScores(constitution=14),  # +2 CON mod
        )
        char.take_damage(20)

        # Spend 2 hit dice
        healed1 = char.spend_hit_die()
        healed2 = char.spend_hit_die()

        assert healed1 > 0
        assert healed2 > 0
        assert char.resources.hit_dice.current == 1  # Started with 3


class TestShortRest:
    """Tests for short rests."""

    def test_short_rest_basic(self):
        """Should complete a short rest successfully."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        result = char.short_rest()

        assert result.success is True
        assert result.rest_type == RestType.SHORT
        assert result.ends_session is False
        assert char.resources.short_rests_since_long == 1

    def test_short_rest_with_hit_dice(self):
        """Should spend hit dice and heal during short rest."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=3,
            ability_scores=AbilityScores(constitution=14),
        )
        char.take_damage(15)

        result = char.short_rest(hit_dice_to_spend=2)

        assert result.success is True
        assert result.hit_dice_spent == 2
        assert result.hp_recovered > 0
        assert char.resources.hit_dice.current == 1

    def test_short_rest_limited_by_available_dice(self):
        """Should only spend available hit dice."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=2,
        )
        # Deficit (11) exceeds max single d10 heal (10), so both dice are spent
        char.take_damage(11)

        result = char.short_rest(hit_dice_to_spend=5)  # Request more than available

        assert result.success is True
        assert result.hit_dice_spent == 2  # Only 2 available at level 2
        assert char.resources.hit_dice.current == 0

    def test_short_rest_recovers_resources(self):
        """Should recover short-rest resources."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.resources.add_feature("Test Short", maximum=1, recover_on=RestType.SHORT)
        char.resources.add_feature("Test Long", maximum=3, recover_on=RestType.LONG)
        char.resources.use_feature("Test Short")
        char.resources.use_feature("Test Long")

        result = char.short_rest()

        assert "Test Short" in result.resources_recovered
        assert "Test Long" not in result.resources_recovered  # Long rest only
        assert char.resources.get_feature("Test Short").current == 1
        assert char.resources.get_feature("Test Long").current == 2

    def test_short_rest_limit(self):
        """Should limit short rests to 2 between long rests."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        result1 = char.short_rest()
        assert result1.success is True

        result2 = char.short_rest()
        assert result2.success is True

        result3 = char.short_rest()
        assert result3.success is False
        assert result3.error is not None
        assert "Maximum 2" in result3.error

    def test_can_short_rest(self):
        """Should check if short rest is available."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        assert char.can_short_rest() is True
        char.short_rest()
        assert char.can_short_rest() is True
        char.short_rest()
        assert char.can_short_rest() is False


class TestLongRest:
    """Tests for long rests."""

    def test_long_rest_recovers_all_hp(self):
        """Should recover all HP on long rest."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.take_damage(char.max_hp - 1)  # Leave at 1 HP

        result = char.long_rest()

        assert result.success is True
        assert result.rest_type == RestType.LONG
        assert result.hp_recovered == char.max_hp - 1
        assert char.current_hp == char.max_hp

    def test_long_rest_recovers_hit_dice(self):
        """Should recover half of hit dice (minimum 1) on long rest."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
        )
        char.resources.hit_dice.current = 0  # Spend all hit dice

        result = char.long_rest()

        assert result.hit_dice_recovered == 2  # 5 // 2 = 2
        assert char.resources.hit_dice.current == 2

    def test_long_rest_recovers_all_resources(self):
        """Should recover all resources on long rest."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.resources.add_feature("Test Short", maximum=1, recover_on=RestType.SHORT)
        char.resources.add_feature("Test Long", maximum=3, recover_on=RestType.LONG)
        char.resources.use_feature("Test Short")
        char.resources.use_feature("Test Long", 2)

        result = char.long_rest()

        assert "Test Short" in result.resources_recovered
        assert "Test Long" in result.resources_recovered
        assert char.resources.get_feature("Test Short").current == 1
        assert char.resources.get_feature("Test Long").current == 3

    def test_long_rest_resets_short_rest_counter(self):
        """Should reset short rest counter on long rest."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.short_rest()
        char.short_rest()
        assert char.resources.short_rests_since_long == 2

        char.long_rest()

        assert char.resources.short_rests_since_long == 0
        assert char.can_short_rest() is True

    def test_long_rest_removes_exhaustion(self):
        """Should remove 1 level of exhaustion on long rest."""
        char = create_character(
            name="Exhausted Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.exhaustion.level = 3

        result = char.long_rest()

        assert result.exhaustion_removed == 1
        assert char.exhaustion.level == 2

    def test_long_rest_no_exhaustion_to_remove(self):
        """Should not remove exhaustion if already at 0."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        result = char.long_rest()

        assert result.exhaustion_removed == 0
        assert char.exhaustion.level == 0

    def test_long_rest_ends_session(self):
        """Long rest should indicate it ends the session."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        result = char.long_rest()

        assert result.ends_session is True


class TestRestIntegration:
    """Integration tests for the rest system."""

    def test_full_adventuring_day(self):
        """Simulate a full adventuring day with rests."""
        char = create_character(
            name="Adventurer",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            level=5,
            ability_scores=AbilityScores(constitution=14),
        )
        char.resources.add_feature("Test Short 1", maximum=1, recover_on=RestType.SHORT)
        char.resources.add_feature("Test Short 2", maximum=1, recover_on=RestType.SHORT)

        # Morning: Use resources in combat
        char.take_damage(15)
        char.resources.use_feature("Test Short 1")
        char.resources.use_feature("Test Short 2")

        # First short rest
        result1 = char.short_rest(hit_dice_to_spend=2)
        assert result1.success
        assert char.resources.get_feature("Test Short 1").current == 1
        assert char.resources.get_feature("Test Short 2").current == 1

        # Afternoon: More combat
        char.take_damage(20)
        char.resources.use_feature("Test Short 1")

        # Second short rest
        result2 = char.short_rest(hit_dice_to_spend=2)
        assert result2.success
        assert char.resources.short_rests_since_long == 2

        # Can't take another short rest
        result3 = char.short_rest()
        assert not result3.success

        # Evening: Long rest
        char.exhaustion.add(1)  # Gained exhaustion during the day
        char.take_damage(10)

        result4 = char.long_rest()
        assert result4.success
        assert char.current_hp == char.max_hp
        assert char.exhaustion.level == 0
        assert char.can_short_rest()  # Reset
