"""Tests for armor class calculation."""

from dnd_bot.character import (
    AbilityScores,
    ClassName,
    SpeciesName,
    create_character,
)
from dnd_bot.character.character import Equipment


class TestEquipment:
    """Tests for the Equipment model."""

    def test_default_equipment(self):
        """Default equipment should be empty."""
        equip = Equipment()
        assert equip.weapon_ids == []
        assert equip.armor_id is None
        assert equip.shield_equipped is False
        assert equip.other_items == []
        assert equip.gold == 0

    def test_equipment_with_items(self):
        """Should be able to set equipment."""
        equip = Equipment(
            weapon_ids=["longsword", "dagger"],
            armor_id="chain_mail",
            shield_equipped=True,
            gold=50,
        )
        assert equip.weapon_ids == ["longsword", "dagger"]
        assert equip.armor_id == "chain_mail"
        assert equip.shield_equipped is True
        assert equip.gold == 50

    def test_backwards_compatibility_properties(self):
        """Legacy property names should work."""
        equip = Equipment(
            weapon_ids=["longsword"],
            armor_id="leather",
            shield_equipped=True,
        )
        # Old property names should work
        assert equip.weapons == ["longsword"]
        assert equip.armor == "leather"
        assert equip.shield is True
        assert equip.items == []


class TestArmorClassCalculation:
    """Tests for Character.calculate_armor_class()."""

    def test_unarmored_base_ac(self):
        """Unarmored AC should be 10 + DEX."""
        scores = AbilityScores(dexterity=14)  # +2 DEX
        char = create_character(
            name="Unarmored Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        # Base unarmored: 10 + 2 = 12
        assert char.armor_class == 12

    def test_unarmored_barbarian(self):
        """Barbarian unarmored defense: 10 + DEX + CON."""
        scores = AbilityScores(dexterity=14, constitution=16)  # +2 DEX, +3 CON
        char = create_character(
            name="Unarmored Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
            ability_scores=scores,
        )
        # Barbarian unarmored: 10 + 2 + 3 = 15
        assert char.armor_class == 15

    def test_unarmored_monk(self):
        """Monk unarmored defense: 10 + DEX + WIS."""
        scores = AbilityScores(dexterity=16, wisdom=14)  # +3 DEX, +2 WIS
        char = create_character(
            name="Unarmored Monk",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.MONK,
            ability_scores=scores,
        )
        # Monk unarmored: 10 + 3 + 2 = 15
        assert char.armor_class == 15

    def test_light_armor(self):
        """Light armor adds full DEX."""
        scores = AbilityScores(dexterity=16)  # +3 DEX
        char = create_character(
            name="Light Armor Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.armor_id = "leather"  # Base AC 11
        char.recalculate_armor_class()
        # Leather: 11 + 3 = 14
        assert char.armor_class == 14

    def test_medium_armor_caps_dex(self):
        """Medium armor caps DEX bonus at 2."""
        scores = AbilityScores(dexterity=18)  # +4 DEX
        char = create_character(
            name="Medium Armor Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.armor_id = "chain_shirt"  # Base AC 13, max DEX +2
        char.recalculate_armor_class()
        # Chain shirt: 13 + 2 (capped) = 15
        assert char.armor_class == 15

    def test_heavy_armor_no_dex(self):
        """Heavy armor doesn't add DEX."""
        scores = AbilityScores(dexterity=18)  # +4 DEX (ignored)
        char = create_character(
            name="Heavy Armor Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.armor_id = "plate"  # Base AC 18
        char.recalculate_armor_class()
        # Plate: 18 (no DEX)
        assert char.armor_class == 18

    def test_shield_bonus(self):
        """Shield should add +2 AC."""
        scores = AbilityScores(dexterity=14)  # +2 DEX
        char = create_character(
            name="Shield Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.armor_id = "leather"  # 11 + 2 = 13
        char.equipment.shield_equipped = True  # +2
        char.recalculate_armor_class()
        # Leather + shield: 13 + 2 = 15
        assert char.armor_class == 15

    def test_shield_with_unarmored(self):
        """Shield should work with unarmored."""
        scores = AbilityScores(dexterity=14)  # +2 DEX
        char = create_character(
            name="Shield Only Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.shield_equipped = True
        char.recalculate_armor_class()
        # Unarmored + shield: 12 + 2 = 14
        assert char.armor_class == 14

    def test_barbarian_unarmored_with_shield(self):
        """Barbarian unarmored defense should work with shield."""
        scores = AbilityScores(dexterity=14, constitution=16)  # +2 DEX, +3 CON
        char = create_character(
            name="Shield Barbarian",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.BARBARIAN,
            ability_scores=scores,
        )
        char.equipment.shield_equipped = True
        char.recalculate_armor_class()
        # Barbarian unarmored + shield: 15 + 2 = 17
        assert char.armor_class == 17

    def test_unknown_armor_falls_back(self):
        """Unknown armor ID should fall back to base AC."""
        scores = AbilityScores(dexterity=14)  # +2 DEX
        char = create_character(
            name="Unknown Armor Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        char.equipment.armor_id = "magical_mystery_armor"  # Unknown
        char.recalculate_armor_class()
        # Falls back to base: 10 + 2 = 12
        assert char.armor_class == 12

    def test_recalculate_updates_armor_class(self):
        """recalculate_armor_class should update the stored value."""
        scores = AbilityScores(dexterity=14)
        char = create_character(
            name="Fighter",
            species_name=SpeciesName.HUMAN,
            class_name=ClassName.FIGHTER,
            ability_scores=scores,
        )
        initial_ac = char.armor_class

        # Equip armor and recalculate
        char.equipment.armor_id = "plate"
        new_ac = char.recalculate_armor_class()

        assert new_ac == 18
        assert char.armor_class == 18
        assert char.armor_class != initial_ac
