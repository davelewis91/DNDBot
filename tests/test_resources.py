"""Tests for the resource tracking system."""

from pathlib import Path

from dnd_bot.character import (
    ClassName,
    HitDice,
    Resource,
    ResourcePool,
    RestType,
    SpeciesName,
    create_character,
    load_character,
    save_character,
)


class TestResource:
    """Tests for the Resource class."""

    def test_create_resource(self):
        """Should create a resource with correct values."""
        resource = Resource(
            name="Second Wind",
            current=1,
            maximum=1,
            recover_on=RestType.SHORT,
        )
        assert resource.name == "Second Wind"
        assert resource.current == 1
        assert resource.maximum == 1
        assert resource.recover_on == RestType.SHORT

    def test_spend_resource(self):
        """Should spend resource uses."""
        resource = Resource(
            name="Rage",
            current=3,
            maximum=3,
            recover_on=RestType.LONG,
        )

        result = resource.spend()
        assert result is True
        assert resource.current == 2

        result = resource.spend(2)
        assert result is True
        assert resource.current == 0

    def test_spend_resource_insufficient(self):
        """Should fail when spending more than available."""
        resource = Resource(
            name="Action Surge",
            current=1,
            maximum=1,
            recover_on=RestType.SHORT,
        )

        result = resource.spend(2)
        assert result is False
        assert resource.current == 1  # Unchanged

    def test_recover_on_matching_rest(self):
        """Should recover on matching rest type."""
        resource = Resource(
            name="Second Wind",
            current=0,
            maximum=1,
            recover_on=RestType.SHORT,
        )

        amount = resource.recover(RestType.SHORT)
        assert amount == 1
        assert resource.current == 1

    def test_recover_on_long_rest(self):
        """Long rest should recover all resources."""
        resource = Resource(
            name="Action Surge",
            current=0,
            maximum=2,
            recover_on=RestType.SHORT,
        )

        amount = resource.recover(RestType.LONG)
        assert amount == 2
        assert resource.current == 2

    def test_no_recover_on_wrong_rest(self):
        """Should not recover on wrong rest type."""
        resource = Resource(
            name="Rage",
            current=0,
            maximum=3,
            recover_on=RestType.LONG,
        )

        amount = resource.recover(RestType.SHORT)
        assert amount == 0
        assert resource.current == 0

    def test_partial_recovery(self):
        """Should handle partial recovery amounts."""
        resource = Resource(
            name="Ki Points",
            current=0,
            maximum=5,
            recover_on=RestType.SHORT,
            recover_amount=2,  # Only recover 2 per rest
        )

        amount = resource.recover(RestType.SHORT)
        assert amount == 2
        assert resource.current == 2

        amount = resource.recover(RestType.SHORT)
        assert amount == 2
        assert resource.current == 4

        # Cap at maximum
        amount = resource.recover(RestType.SHORT)
        assert amount == 1  # Only 1 remaining to max
        assert resource.current == 5

    def test_is_available(self):
        """Should check if resource is available."""
        resource = Resource(
            name="Second Wind",
            current=1,
            maximum=1,
            recover_on=RestType.SHORT,
        )
        assert resource.is_available

        resource.spend()
        assert not resource.is_available

    def test_reset(self):
        """Should reset to maximum."""
        resource = Resource(
            name="Rage",
            current=0,
            maximum=3,
            recover_on=RestType.LONG,
        )

        resource.reset()
        assert resource.current == 3


class TestHitDice:
    """Tests for the HitDice class."""

    def test_create_hit_dice(self):
        """Should create hit dice pool."""
        hd = HitDice(die_size=10, total=5, current=5)
        assert hd.die_size == 10
        assert hd.total == 5
        assert hd.current == 5

    def test_spend_hit_die(self):
        """Should spend hit dice."""
        hd = HitDice(die_size=8, total=3, current=3)

        result = hd.spend()
        assert result is True
        assert hd.current == 2

        result = hd.spend(2)
        assert result is True
        assert hd.current == 0

    def test_spend_hit_die_insufficient(self):
        """Should fail when spending more than available."""
        hd = HitDice(die_size=10, total=5, current=1)

        result = hd.spend(2)
        assert result is False
        assert hd.current == 1  # Unchanged

    def test_recover_hit_dice(self):
        """Should recover hit dice."""
        hd = HitDice(die_size=12, total=5, current=2)

        amount = hd.recover(2)
        assert amount == 2
        assert hd.current == 4

    def test_recover_hit_dice_capped(self):
        """Should cap recovery at total."""
        hd = HitDice(die_size=10, total=5, current=4)

        amount = hd.recover(3)
        assert amount == 1  # Only 1 to reach max
        assert hd.current == 5

    def test_recover_half(self):
        """Should recover half hit dice rounded down (minimum 1)."""
        hd = HitDice(die_size=10, total=5, current=0)

        amount = hd.recover_half()
        assert amount == 2  # 5 // 2 = 2
        assert hd.current == 2

    def test_recover_half_minimum_one(self):
        """Should recover at least 1 hit die."""
        hd = HitDice(die_size=6, total=1, current=0)

        amount = hd.recover_half()
        assert amount == 1  # max(1, 1//2) = 1
        assert hd.current == 1

    def test_available_property(self):
        """Should return available hit dice."""
        hd = HitDice(die_size=8, total=4, current=2)
        assert hd.available == 2


class TestResourcePool:
    """Tests for the ResourcePool class."""

    def test_empty_pool(self):
        """New pool should be empty."""
        pool = ResourcePool()
        assert pool.hit_dice is None
        assert len(pool.feature_uses) == 0
        assert pool.short_rests_since_long == 0

    def test_add_feature(self):
        """Should add a feature resource."""
        pool = ResourcePool()
        resource = pool.add_feature(
            name="Second Wind",
            maximum=1,
            recover_on=RestType.SHORT,
        )

        assert resource.name == "Second Wind"
        assert pool.get_feature("Second Wind") is not None
        assert pool.get_feature("second_wind") is not None  # Case insensitive

    def test_use_feature(self):
        """Should use a feature resource."""
        pool = ResourcePool()
        pool.add_feature("Rage", maximum=3, recover_on=RestType.LONG)

        result = pool.use_feature("Rage")
        assert result is True
        assert pool.get_feature("Rage").current == 2

    def test_use_feature_not_found(self):
        """Should return False for unknown feature."""
        pool = ResourcePool()
        result = pool.use_feature("Unknown Feature")
        assert result is False

    def test_has_feature_available(self):
        """Should check if feature has uses."""
        pool = ResourcePool()
        pool.add_feature("Action Surge", maximum=1, recover_on=RestType.SHORT)

        assert pool.has_feature_available("Action Surge")

        pool.use_feature("Action Surge")
        assert not pool.has_feature_available("Action Surge")

    def test_recover_short_rest(self):
        """Should recover short rest resources."""
        pool = ResourcePool()
        pool.add_feature("Second Wind", maximum=1, recover_on=RestType.SHORT)
        pool.add_feature("Rage", maximum=3, recover_on=RestType.LONG)

        pool.use_feature("Second Wind")
        pool.use_feature("Rage")

        recovered = pool.recover_short_rest()

        assert "Second Wind" in recovered
        assert recovered["Second Wind"] == 1
        assert "Rage" not in recovered  # Long rest only
        assert pool.get_feature("Rage").current == 2  # Still depleted

    def test_recover_long_rest(self):
        """Should recover all resources and hit dice."""
        pool = ResourcePool()
        pool.hit_dice = HitDice(die_size=10, total=5, current=1)
        pool.add_feature("Second Wind", maximum=1, recover_on=RestType.SHORT)
        pool.add_feature("Rage", maximum=3, recover_on=RestType.LONG)

        pool.use_feature("Second Wind")
        pool.use_feature("Rage", 2)
        pool.short_rests_since_long = 2

        recovered = pool.recover_long_rest()

        assert "Second Wind" in recovered
        assert "Rage" in recovered
        assert recovered["Rage"] == 2
        assert "Hit Dice" in recovered
        assert recovered["Hit Dice"] == 2  # 5 // 2 = 2
        assert pool.short_rests_since_long == 0  # Reset

    def test_can_short_rest(self):
        """Should track short rest limit."""
        pool = ResourcePool()

        assert pool.can_short_rest()
        pool.record_short_rest()
        assert pool.can_short_rest()
        pool.record_short_rest()
        assert not pool.can_short_rest()

    def test_record_short_rest(self):
        """Should record short rest and enforce limit."""
        pool = ResourcePool()

        result = pool.record_short_rest()
        assert result is True
        assert pool.short_rests_since_long == 1

        result = pool.record_short_rest()
        assert result is True
        assert pool.short_rests_since_long == 2

        result = pool.record_short_rest()
        assert result is False  # Max reached
        assert pool.short_rests_since_long == 2

    def test_reset_all(self):
        """Should reset all resources."""
        pool = ResourcePool()
        pool.hit_dice = HitDice(die_size=8, total=4, current=1)
        pool.add_feature("Rage", maximum=3, recover_on=RestType.LONG)
        pool.use_feature("Rage", 2)
        pool.short_rests_since_long = 2

        pool.reset_all()

        assert pool.hit_dice.current == 4
        assert pool.get_feature("Rage").current == 3
        assert pool.short_rests_since_long == 0


class TestCharacterResources:
    """Tests for resource integration with Character."""

    def test_character_has_hit_dice(self):
        """Character should have hit dice initialized."""
        char = create_character(
            name="Test Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=5,
        )

        assert char.resources.hit_dice is not None
        assert char.resources.hit_dice.die_size == 10  # Fighter d10
        assert char.resources.hit_dice.total == 5
        assert char.resources.hit_dice.current == 5

    def test_barbarian_hit_dice(self):
        """Barbarian should have d12 hit dice."""
        char = create_character(
            name="Test Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
            level=3,
        )

        assert char.resources.hit_dice.die_size == 12

    def test_rogue_hit_dice(self):
        """Rogue should have d8 hit dice."""
        char = create_character(
            name="Test Rogue",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.ROGUE,
            level=2,
        )

        assert char.resources.hit_dice.die_size == 8


class TestResourcesStorage:
    """Tests for resources YAML persistence."""

    def test_save_and_load_resources(self, tmp_path: Path):
        """Should preserve resources across save/load."""
        char = create_character(
            name="Resourceful Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=5,
        )

        # Add some feature uses
        char.resources.add_feature("Second Wind", maximum=1, recover_on=RestType.SHORT)
        char.resources.add_feature("Rage", maximum=3, recover_on=RestType.LONG)

        # Modify state
        char.resources.use_feature("Second Wind")
        char.resources.use_feature("Rage")
        char.resources.hit_dice.spend(2)
        char.resources.short_rests_since_long = 1

        filepath = save_character(char, tmp_path)
        loaded = load_character(filepath)

        # Check hit dice
        assert loaded.resources.hit_dice.die_size == 10
        assert loaded.resources.hit_dice.total == 5
        assert loaded.resources.hit_dice.current == 3

        # Check feature uses
        assert loaded.resources.get_feature("Second Wind").current == 0
        assert loaded.resources.get_feature("Rage").current == 2

        # Check short rest counter
        assert loaded.resources.short_rests_since_long == 1

    def test_load_character_without_resources(self, tmp_path: Path):
        """Loading character without resources should initialize them."""
        char = create_character(
            name="Old Character",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            level=3,
        )

        filepath = save_character(char, tmp_path)

        # Manually remove resources from the YAML
        import yaml
        with open(filepath) as f:
            data = yaml.safe_load(f)
        del data["resources"]
        with open(filepath, "w") as f:
            yaml.dump(data, f)

        loaded = load_character(filepath)

        # Should still have hit dice initialized by model_post_init
        assert loaded.resources.hit_dice is not None
        assert loaded.resources.hit_dice.die_size == 10
        assert loaded.resources.hit_dice.total == 3
