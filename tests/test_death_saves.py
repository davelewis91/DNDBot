"""Tests for the death saving throw system."""

from unittest.mock import patch

from dnd_bot.character import (
    ClassName,
    SpeciesName,
    create_character,
)
from dnd_bot.character.character import DeathSaveOutcome, DeathSaves


class TestDeathSavesModel:
    """Tests for the DeathSaves model."""

    def test_initial_state(self):
        """Death saves should start at 0/0 and not stable."""
        saves = DeathSaves()
        assert saves.successes == 0
        assert saves.failures == 0
        assert saves.is_stable is False
        assert saves.is_dead is False
        assert saves.is_making_saves is True

    def test_add_success(self):
        """Adding successes should accumulate."""
        saves = DeathSaves()
        saves.add_success()
        assert saves.successes == 1
        saves.add_success()
        assert saves.successes == 2
        assert saves.is_stable is False

    def test_stabilize_on_three_successes(self):
        """Should stabilize after 3 successes."""
        saves = DeathSaves()
        saves.add_success()
        saves.add_success()
        result = saves.add_success()
        assert result is True  # Returns True when stabilized
        assert saves.successes == 3
        assert saves.is_stable is True
        assert saves.is_making_saves is False

    def test_add_failure(self):
        """Adding failures should accumulate."""
        saves = DeathSaves()
        saves.add_failure()
        assert saves.failures == 1
        saves.add_failure()
        assert saves.failures == 2
        assert saves.is_dead is False

    def test_dead_on_three_failures(self):
        """Should be dead after 3 failures."""
        saves = DeathSaves()
        saves.add_failure()
        saves.add_failure()
        result = saves.add_failure()
        assert result is True  # Returns True when dead
        assert saves.failures == 3
        assert saves.is_dead is True
        assert saves.is_making_saves is False

    def test_add_multiple_failures(self):
        """Should be able to add multiple failures at once (nat 1)."""
        saves = DeathSaves()
        saves.add_failure(2)
        assert saves.failures == 2

    def test_failures_capped_at_three(self):
        """Failures should not exceed 3."""
        saves = DeathSaves()
        saves.add_failure(5)
        assert saves.failures == 3

    def test_reset(self):
        """Reset should clear all death save progress."""
        saves = DeathSaves(successes=2, failures=1, is_stable=True)
        saves.reset()
        assert saves.successes == 0
        assert saves.failures == 0
        assert saves.is_stable is False


class TestMakeDeathSave:
    """Tests for the Character.make_death_save() method."""

    def _create_dying_character(self):
        """Create a character at 0 HP for testing."""
        char = create_character(
            name="Dying Hero",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.take_damage(char.max_hp)
        assert char.current_hp == 0
        return char

    def test_roll_10_is_success(self):
        """Rolling 10+ should be a success."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=10):
            result = char.make_death_save()
        assert result.roll == 10
        assert result.outcome == DeathSaveOutcome.SUCCESS
        assert result.successes == 1
        assert result.failures == 0

    def test_roll_15_is_success(self):
        """Rolling 15 should be a success."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=15):
            result = char.make_death_save()
        assert result.outcome == DeathSaveOutcome.SUCCESS
        assert result.successes == 1

    def test_roll_9_is_failure(self):
        """Rolling 9 or less should be a failure."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=9):
            result = char.make_death_save()
        assert result.roll == 9
        assert result.outcome == DeathSaveOutcome.FAILURE
        assert result.failures == 1
        assert result.successes == 0

    def test_roll_2_is_failure(self):
        """Rolling 2 should be a failure."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=2):
            result = char.make_death_save()
        assert result.outcome == DeathSaveOutcome.FAILURE
        assert result.failures == 1

    def test_natural_20_critical_success(self):
        """Natural 20 should regain 1 HP and reset death saves."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=20):
            result = char.make_death_save()
        assert result.roll == 20
        assert result.outcome == DeathSaveOutcome.CRITICAL_SUCCESS
        assert result.hp_recovered == 1
        assert result.successes == 0  # Reset
        assert result.failures == 0  # Reset
        assert char.current_hp == 1
        assert char.death_saves.is_stable is False

    def test_natural_1_critical_failure(self):
        """Natural 1 should cause 2 failures."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=1):
            result = char.make_death_save()
        assert result.roll == 1
        assert result.outcome == DeathSaveOutcome.CRITICAL_FAILURE
        assert result.failures == 2

    def test_three_successes_stabilizes(self):
        """Three successes should stabilize the character."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=15):
            char.make_death_save()
            char.make_death_save()
            result = char.make_death_save()
        assert result.outcome == DeathSaveOutcome.STABILIZED
        assert result.successes == 3
        assert char.death_saves.is_stable is True

    def test_three_failures_kills(self):
        """Three failures should kill the character."""
        char = self._create_dying_character()
        with patch("random.randint", return_value=5):
            char.make_death_save()
            char.make_death_save()
            result = char.make_death_save()
        assert result.outcome == DeathSaveOutcome.DEAD
        assert result.failures == 3
        assert char.death_saves.is_dead is True

    def test_nat_1_can_kill_from_two_failures(self):
        """Nat 1 with 2 existing failures should kill."""
        char = self._create_dying_character()
        char.death_saves.failures = 2
        with patch("random.randint", return_value=1):
            result = char.make_death_save()
        assert result.outcome == DeathSaveOutcome.DEAD
        assert char.death_saves.is_dead is True


class TestDamageAtZeroHP:
    """Tests for taking damage while at 0 HP."""

    def _create_dying_character(self):
        """Create a character at 0 HP for testing."""
        char = create_character(
            name="Dying Hero",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.take_damage(char.max_hp)
        return char

    def test_damage_at_zero_hp_adds_failure(self):
        """Taking damage at 0 HP should add 1 death save failure."""
        char = self._create_dying_character()
        char.take_damage(5)
        assert char.death_saves.failures == 1
        assert char.current_hp == 0

    def test_critical_damage_at_zero_hp_adds_two_failures(self):
        """Taking critical damage at 0 HP should add 2 failures."""
        char = self._create_dying_character()
        char.take_damage(5, is_critical=True)
        assert char.death_saves.failures == 2

    def test_multiple_damage_at_zero_hp(self):
        """Multiple hits at 0 HP should accumulate failures."""
        char = self._create_dying_character()
        char.take_damage(3)
        char.take_damage(3)
        assert char.death_saves.failures == 2


class TestHealingResetsDeathSaves:
    """Tests for healing resetting death saves."""

    def test_healing_from_zero_resets_death_saves(self):
        """Healing from 0 HP should reset death saves."""
        char = create_character(
            name="Dying Hero",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.take_damage(char.max_hp)
        char.death_saves.successes = 2
        char.death_saves.failures = 2

        char.heal(5)

        assert char.current_hp == 5
        assert char.death_saves.successes == 0
        assert char.death_saves.failures == 0
        assert char.death_saves.is_stable is False

    def test_healing_when_not_at_zero_no_reset(self):
        """Healing when not at 0 HP should not affect death saves."""
        char = create_character(
            name="Injured Hero",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.take_damage(5)
        # Manually set death saves (shouldn't normally happen)
        char.death_saves.failures = 1

        char.heal(3)

        # Death saves should not be reset since we weren't at 0
        assert char.death_saves.failures == 1

    def test_reset_death_saves_method(self):
        """reset_death_saves() should clear death save progress."""
        char = create_character(
            name="Dying Hero",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.death_saves.successes = 2
        char.death_saves.failures = 1

        char.reset_death_saves()

        assert char.death_saves.successes == 0
        assert char.death_saves.failures == 0
