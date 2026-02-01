"""Tests for the conditions system."""

from pathlib import Path

from dnd_bot.character import (
    ActiveCondition,
    ClassName,
    Condition,
    ConditionManager,
    SpeciesName,
    create_character,
    load_character,
    save_character,
)


class TestCondition:
    """Tests for the Condition enum."""

    def test_all_conditions_exist(self):
        """All standard D&D conditions should exist."""
        conditions = [
            Condition.BLINDED,
            Condition.CHARMED,
            Condition.DEAFENED,
            Condition.FRIGHTENED,
            Condition.GRAPPLED,
            Condition.INCAPACITATED,
            Condition.INVISIBLE,
            Condition.PARALYZED,
            Condition.PETRIFIED,
            Condition.POISONED,
            Condition.PRONE,
            Condition.RESTRAINED,
            Condition.STUNNED,
            Condition.UNCONSCIOUS,
        ]
        assert len(conditions) == 14


class TestActiveCondition:
    """Tests for the ActiveCondition model."""

    def test_create_basic_condition(self):
        """Should create a condition with default values."""
        ac = ActiveCondition(condition=Condition.POISONED)
        assert ac.condition == Condition.POISONED
        assert ac.source == ""
        assert ac.duration is None

    def test_create_condition_with_source(self):
        """Should create a condition with source."""
        ac = ActiveCondition(
            condition=Condition.FRIGHTENED,
            source="Dragon's Frightful Presence",
        )
        assert ac.source == "Dragon's Frightful Presence"

    def test_create_condition_with_duration(self):
        """Should create a condition with duration."""
        ac = ActiveCondition(
            condition=Condition.PARALYZED,
            source="Hold Person spell",
            duration=10,
        )
        assert ac.duration == 10

    def test_tick_decreases_duration(self):
        """Tick should decrease duration by 1."""
        ac = ActiveCondition(condition=Condition.STUNNED, duration=3)

        result = ac.tick()
        assert result is True
        assert ac.duration == 2

        result = ac.tick()
        assert result is True
        assert ac.duration == 1

        result = ac.tick()
        assert result is False  # Expired
        assert ac.duration == 0

    def test_tick_permanent_condition(self):
        """Permanent conditions (None duration) should not expire."""
        ac = ActiveCondition(condition=Condition.PETRIFIED, duration=None)

        result = ac.tick()
        assert result is True
        assert ac.duration is None


class TestConditionManager:
    """Tests for the ConditionManager."""

    def test_empty_manager(self):
        """New manager should have no conditions."""
        manager = ConditionManager()
        assert len(manager.active) == 0
        assert not manager.has(Condition.POISONED)

    def test_add_condition(self):
        """Should add a condition."""
        manager = ConditionManager()
        manager.add(Condition.POISONED, source="Poison trap")

        assert manager.has(Condition.POISONED)
        assert len(manager.active) == 1

    def test_add_multiple_conditions(self):
        """Should add multiple different conditions."""
        manager = ConditionManager()
        manager.add(Condition.POISONED)
        manager.add(Condition.FRIGHTENED)
        manager.add(Condition.PRONE)

        assert manager.has(Condition.POISONED)
        assert manager.has(Condition.FRIGHTENED)
        assert manager.has(Condition.PRONE)
        assert len(manager.active) == 3

    def test_add_same_condition_multiple_times(self):
        """Should allow multiple instances of the same condition."""
        manager = ConditionManager()
        manager.add(Condition.FRIGHTENED, source="Dragon")
        manager.add(Condition.FRIGHTENED, source="Lich")

        assert len(manager.active) == 2
        assert len(manager.get(Condition.FRIGHTENED)) == 2

    def test_remove_condition(self):
        """Should remove a condition."""
        manager = ConditionManager()
        manager.add(Condition.POISONED)
        manager.add(Condition.PRONE)

        count = manager.remove(Condition.POISONED)
        assert count == 1
        assert not manager.has(Condition.POISONED)
        assert manager.has(Condition.PRONE)

    def test_remove_condition_by_source(self):
        """Should remove only condition from specific source."""
        manager = ConditionManager()
        manager.add(Condition.FRIGHTENED, source="Dragon")
        manager.add(Condition.FRIGHTENED, source="Lich")

        count = manager.remove(Condition.FRIGHTENED, source="Dragon")
        assert count == 1
        assert manager.has(Condition.FRIGHTENED)  # Lich's fear remains
        assert len(manager.get(Condition.FRIGHTENED)) == 1

    def test_remove_all_conditions(self):
        """Should remove all conditions."""
        manager = ConditionManager()
        manager.add(Condition.POISONED)
        manager.add(Condition.PRONE)
        manager.add(Condition.FRIGHTENED)

        count = manager.remove_all()
        assert count == 3
        assert len(manager.active) == 0

    def test_tick_all(self):
        """Should tick all conditions and return expired ones."""
        manager = ConditionManager()
        manager.add(Condition.STUNNED, duration=1)  # Will expire
        manager.add(Condition.PARALYZED, duration=2)  # Will remain
        manager.add(Condition.PETRIFIED)  # Permanent

        expired = manager.tick_all()

        assert Condition.STUNNED in expired
        assert not manager.has(Condition.STUNNED)
        assert manager.has(Condition.PARALYZED)
        assert manager.has(Condition.PETRIFIED)

    def test_list_conditions(self):
        """Should list unique conditions."""
        manager = ConditionManager()
        manager.add(Condition.FRIGHTENED, source="Dragon")
        manager.add(Condition.FRIGHTENED, source="Lich")
        manager.add(Condition.POISONED)

        conditions = manager.list_conditions()
        assert len(conditions) == 2
        assert Condition.FRIGHTENED in conditions
        assert Condition.POISONED in conditions

    def test_has_disadvantage_on_attacks(self):
        """Should detect disadvantage on attacks."""
        manager = ConditionManager()
        assert not manager.has_disadvantage_on_attacks

        manager.add(Condition.POISONED)
        assert manager.has_disadvantage_on_attacks

    def test_has_disadvantage_on_checks(self):
        """Should detect disadvantage on ability checks."""
        manager = ConditionManager()
        assert not manager.has_disadvantage_on_checks

        manager.add(Condition.FRIGHTENED)
        assert manager.has_disadvantage_on_checks

    def test_grants_advantage_to_attackers(self):
        """Should detect when attackers have advantage."""
        manager = ConditionManager()
        assert not manager.grants_advantage_to_attackers

        manager.add(Condition.PARALYZED)
        assert manager.grants_advantage_to_attackers

    def test_is_incapacitated(self):
        """Should detect incapacitated state."""
        manager = ConditionManager()
        assert not manager.is_incapacitated

        manager.add(Condition.STUNNED)
        assert manager.is_incapacitated

    def test_cannot_move(self):
        """Should detect when movement is prevented."""
        manager = ConditionManager()
        assert not manager.cannot_move

        manager.add(Condition.GRAPPLED)
        assert manager.cannot_move

    def test_auto_crit_on_melee(self):
        """Should detect when melee attacks auto-crit."""
        manager = ConditionManager()
        assert not manager.auto_crit_on_melee

        manager.add(Condition.UNCONSCIOUS)
        assert manager.auto_crit_on_melee


class TestCharacterConditions:
    """Tests for condition integration with Character."""

    def test_character_default_no_conditions(self):
        """Character should start with no conditions."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        assert len(char.conditions.active) == 0

    def test_character_add_condition(self):
        """Should add condition via character method."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.add_condition(Condition.POISONED, source="Bad food")

        assert char.has_condition(Condition.POISONED)

    def test_character_remove_condition(self):
        """Should remove condition via character method."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.add_condition(Condition.POISONED)

        count = char.remove_condition(Condition.POISONED)
        assert count == 1
        assert not char.has_condition(Condition.POISONED)

    def test_unconscious_affects_is_conscious(self):
        """Unconscious condition should make is_conscious return False."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        assert char.is_conscious  # HP > 0

        char.add_condition(Condition.UNCONSCIOUS)
        assert not char.is_conscious  # Has unconscious condition

        char.remove_condition(Condition.UNCONSCIOUS)
        assert char.is_conscious  # Condition removed


class TestConditionsStorage:
    """Tests for conditions YAML persistence."""

    def test_save_and_load_conditions(self, tmp_path: Path):
        """Should preserve conditions across save/load."""
        char = create_character(
            name="Afflicted Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )
        char.add_condition(Condition.POISONED, source="Poison trap", duration=5)
        char.add_condition(Condition.FRIGHTENED, source="Dragon")

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        assert len(loaded.conditions.active) == 2
        assert loaded.has_condition(Condition.POISONED)
        assert loaded.has_condition(Condition.FRIGHTENED)

        # Check details preserved
        poisoned = loaded.conditions.get(Condition.POISONED)[0]
        assert poisoned.source == "Poison trap"
        assert poisoned.duration == 5

    def test_load_character_without_conditions(self, tmp_path: Path):
        """Loading character without conditions field should work."""
        char = create_character(
            name="Old Character",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
        )

        filepath = save_character(char, tmp_path)

        # Manually remove conditions from the YAML
        import yaml
        with open(filepath) as f:
            data = yaml.safe_load(f)
        del data["conditions"]
        with open(filepath, "w") as f:
            yaml.dump(data, f)

        loaded = load_character(filepath)
        assert len(loaded.conditions.active) == 0
