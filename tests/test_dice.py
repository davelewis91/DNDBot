"""Tests for the dice module."""

import pytest

from dnd_bot.dice import Dice, DiceResult, d20, roll


class TestDice:
    """Tests for the Dice class."""

    def test_parse_simple(self):
        """Parse simple dice notation like 'd20'."""
        dice = Dice.parse("d20")
        assert dice.count == 1
        assert dice.sides == 20
        assert dice.modifier == 0

    def test_parse_with_count(self):
        """Parse dice with count like '2d6'."""
        dice = Dice.parse("2d6")
        assert dice.count == 2
        assert dice.sides == 6
        assert dice.modifier == 0

    def test_parse_with_positive_modifier(self):
        """Parse dice with positive modifier like '1d8+3'."""
        dice = Dice.parse("1d8+3")
        assert dice.count == 1
        assert dice.sides == 8
        assert dice.modifier == 3

    def test_parse_with_negative_modifier(self):
        """Parse dice with negative modifier like '2d4-1'."""
        dice = Dice.parse("2d4-1")
        assert dice.count == 2
        assert dice.sides == 4
        assert dice.modifier == -1

    def test_parse_uppercase(self):
        """Parse uppercase notation."""
        dice = Dice.parse("2D6+3")
        assert dice.count == 2
        assert dice.sides == 6
        assert dice.modifier == 3

    def test_parse_with_whitespace(self):
        """Parse notation with leading/trailing whitespace."""
        dice = Dice.parse("  1d10  ")
        assert dice.count == 1
        assert dice.sides == 10

    def test_parse_invalid_notation(self):
        """Reject invalid dice notation."""
        with pytest.raises(ValueError, match="Invalid dice notation"):
            Dice.parse("not dice")

    def test_parse_empty_string(self):
        """Reject empty string."""
        with pytest.raises(ValueError, match="Invalid dice notation"):
            Dice.parse("")

    def test_parse_just_number(self):
        """Reject just a number."""
        with pytest.raises(ValueError, match="Invalid dice notation"):
            Dice.parse("6")

    def test_roll_returns_result(self):
        """Roll returns a DiceResult."""
        dice = Dice.parse("1d6")
        result = dice.roll()
        assert isinstance(result, DiceResult)
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 6
        assert result.total == result.rolls[0]

    def test_roll_multiple_dice(self):
        """Roll multiple dice."""
        dice = Dice.parse("3d6")
        result = dice.roll()
        assert len(result.rolls) == 3
        assert all(1 <= r <= 6 for r in result.rolls)
        assert result.total == sum(result.rolls)

    def test_roll_with_modifier(self):
        """Roll with modifier applied to total."""
        dice = Dice.parse("1d6+5")
        result = dice.roll()
        assert result.modifier == 5
        assert result.total == result.rolls[0] + 5

    def test_str_representation(self):
        """String representation matches notation."""
        assert str(Dice.parse("2d6")) == "2d6"
        assert str(Dice.parse("1d20+5")) == "1d20+5"
        assert str(Dice.parse("d8-2")) == "1d8-2"


class TestDiceResult:
    """Tests for the DiceResult class."""

    def test_str_simple(self):
        """String format for simple roll."""
        result = DiceResult(rolls=[5], modifier=0, total=5, notation="1d6")
        assert str(result) == "5 [5]"

    def test_str_with_modifier(self):
        """String format with positive modifier."""
        result = DiceResult(rolls=[4], modifier=3, total=7, notation="1d6+3")
        assert str(result) == "7 [4]+3"

    def test_str_with_negative_modifier(self):
        """String format with negative modifier."""
        result = DiceResult(rolls=[6], modifier=-2, total=4, notation="1d6-2")
        assert str(result) == "4 [6]-2"

    def test_str_multiple_rolls(self):
        """String format with multiple rolls."""
        result = DiceResult(rolls=[3, 5, 2], modifier=0, total=10, notation="3d6")
        assert str(result) == "10 [3, 5, 2]"

    def test_str_empty_rolls(self):
        """String format with no rolls."""
        result = DiceResult(total=5)
        assert str(result) == "5"


class TestRollFunction:
    """Tests for the roll() convenience function."""

    def test_roll_basic(self):
        """Roll with basic notation."""
        result = roll("1d6")
        assert isinstance(result, DiceResult)
        assert 1 <= result.total <= 6

    def test_roll_with_modifier(self):
        """Roll with modifier."""
        result = roll("1d4+10")
        assert 11 <= result.total <= 14


class TestD20Function:
    """Tests for the d20() function."""

    def test_d20_normal(self):
        """Normal d20 roll."""
        result = d20()
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 20
        assert result.total == result.rolls[0]

    def test_d20_with_modifier(self):
        """D20 roll with modifier."""
        result = d20(modifier=5)
        assert result.modifier == 5
        assert result.total == result.rolls[0] + 5

    def test_d20_advantage_rolls_twice(self):
        """Advantage rolls two dice."""
        result = d20(advantage=True)
        assert len(result.rolls) == 2
        assert result.total == max(result.rolls)

    def test_d20_disadvantage_rolls_twice(self):
        """Disadvantage rolls two dice."""
        result = d20(disadvantage=True)
        assert len(result.rolls) == 2
        assert result.total == min(result.rolls)

    def test_d20_advantage_and_disadvantage_cancel(self):
        """Advantage and disadvantage cancel out."""
        result = d20(advantage=True, disadvantage=True)
        assert len(result.rolls) == 1
        assert result.total == result.rolls[0]

    def test_d20_advantage_notation(self):
        """Advantage includes notation."""
        result = d20(advantage=True)
        assert "advantage" in result.notation

    def test_d20_disadvantage_notation(self):
        """Disadvantage includes notation."""
        result = d20(disadvantage=True)
        assert "disadvantage" in result.notation

    def test_d20_advantage_with_modifier(self):
        """Advantage with modifier."""
        result = d20(advantage=True, modifier=3)
        assert result.modifier == 3
        assert result.total == max(result.rolls) + 3


class TestDiceValidation:
    """Tests for Dice validation."""

    def test_count_must_be_positive(self):
        """Count must be at least 1."""
        with pytest.raises(ValueError):
            Dice(count=0, sides=6)

    def test_sides_must_be_positive(self):
        """Sides must be at least 1."""
        with pytest.raises(ValueError):
            Dice(count=1, sides=0)

    def test_reasonable_limits(self):
        """Can create dice with reasonable limits."""
        dice = Dice(count=100, sides=100, modifier=100)
        assert dice.count == 100
        assert dice.sides == 100
        assert dice.modifier == 100
