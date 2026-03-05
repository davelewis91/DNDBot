"""Tests for the exhaustion system."""

from pathlib import Path

import pytest

from dnd_bot.character import (
    AbilityScores,
    Exhaustion,
    SpeciesName,
    create_character,
    load_character,
    save_character,
)


class TestExhaustion:
    """Tests for the Exhaustion class."""

    def test_default_exhaustion(self):
        """Default exhaustion should be level 0."""
        exhaustion = Exhaustion()
        assert exhaustion.level == 0
        assert exhaustion.penalty == 0
        assert not exhaustion.is_dead

    def test_exhaustion_penalty(self):
        """Penalty should equal negative of level."""
        exhaustion = Exhaustion(level=3)
        assert exhaustion.penalty == -3

        exhaustion = Exhaustion(level=7)
        assert exhaustion.penalty == -7

    def test_exhaustion_add(self):
        """Adding exhaustion should increase level."""
        exhaustion = Exhaustion()
        exhaustion.add(2)
        assert exhaustion.level == 2

        exhaustion.add()  # Default is 1
        assert exhaustion.level == 3

    def test_exhaustion_add_caps_at_10(self):
        """Exhaustion should cap at level 10."""
        exhaustion = Exhaustion(level=8)
        exhaustion.add(5)
        assert exhaustion.level == 10

    def test_exhaustion_remove(self):
        """Removing exhaustion should decrease level."""
        exhaustion = Exhaustion(level=5)
        exhaustion.remove(2)
        assert exhaustion.level == 3

        exhaustion.remove()  # Default is 1
        assert exhaustion.level == 2

    def test_exhaustion_remove_floors_at_0(self):
        """Exhaustion should not go below 0."""
        exhaustion = Exhaustion(level=2)
        exhaustion.remove(5)
        assert exhaustion.level == 0

    def test_exhaustion_reset(self):
        """Reset should set exhaustion to 0."""
        exhaustion = Exhaustion(level=7)
        exhaustion.reset()
        assert exhaustion.level == 0

    def test_exhaustion_death(self):
        """Character dies at exhaustion level 10."""
        exhaustion = Exhaustion(level=9)
        assert not exhaustion.is_dead

        exhaustion.add()
        assert exhaustion.level == 10
        assert exhaustion.is_dead

    def test_exhaustion_validation(self):
        """Exhaustion level should be validated."""
        with pytest.raises(ValueError):
            Exhaustion(level=-1)

        with pytest.raises(ValueError):
            Exhaustion(level=11)


class TestCharacterExhaustion:
    """Tests for exhaustion integration with Character."""

    def test_character_default_exhaustion(self):
        """Character should have 0 exhaustion by default."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        assert char.exhaustion.level == 0
        assert char.exhaustion.penalty == 0

    def test_exhaustion_penalty_applied_to_ability_check(self):
        """Exhaustion penalty should be included in ability check totals."""
        from dnd_bot.character.abilities import Ability

        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=AbilityScores(strength=14),  # +2 modifier
        )
        char.exhaustion.level = 3  # penalty = -3

        total, die_roll = char.make_ability_check(Ability.STRENGTH)
        modifier = char.get_ability_modifier(Ability.STRENGTH)

        assert total - die_roll == modifier + char.exhaustion.penalty

    def test_exhaustion_penalty_applied_to_saving_throw(self):
        """Exhaustion penalty should be included in saving throw totals."""
        from dnd_bot.character.abilities import Ability

        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
            ability_scores=AbilityScores(constitution=16),  # +3 modifier
        )
        char.exhaustion.level = 4  # penalty = -4

        total, die_roll = char.make_saving_throw(Ability.CONSTITUTION)

        expected = char.get_saving_throw_bonus(Ability.CONSTITUTION) + char.exhaustion.penalty
        assert total - die_roll == expected


class TestExhaustionStorage:
    """Tests for exhaustion YAML persistence."""

    def test_save_and_load_exhaustion(self, tmp_path: Path):
        """Should preserve exhaustion level across save/load."""
        char = create_character(
            name="Exhausted Fighter",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )
        char.exhaustion.level = 4

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert loaded.exhaustion.level == 4
        assert loaded.exhaustion.penalty == -4

    def test_load_character_without_exhaustion(self, tmp_path: Path):
        """Loading character without exhaustion field should default to 0."""
        char = create_character(
            name="Old Character",
            species_name=SpeciesName.HUMAN,
            class_type="fighter",
        )

        filepath = save_character(char, tmp_path)

        # Manually remove exhaustion from the YAML
        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)
        del data["exhaustion"]
        with open(filepath, "w") as f:
            yaml.dump(data, f)

        loaded = load_character(filepath)
        assert loaded.exhaustion.level == 0
