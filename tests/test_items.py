"""Tests for the items system."""

import pytest

from dnd_bot.items import (
    ARMOR_REGISTRY,
    WEAPON_REGISTRY,
    ArmorType,
    DamageType,
    WeaponCategory,
    WeaponProperty,
    get_ammunition,
    get_armor,
    get_consumable,
    get_shield,
    get_weapon,
    list_armor,
    list_potions,
    list_weapons,
)


class TestWeapons:
    """Tests for weapon definitions."""

    def test_get_weapon(self):
        """Should retrieve a weapon by ID."""
        dagger = get_weapon("dagger")
        assert dagger.name == "Dagger"
        assert dagger.damage_dice == "1d4"
        assert dagger.damage_type == DamageType.PIERCING

    def test_get_weapon_copy(self):
        """get_weapon should return a copy, not the original."""
        dagger1 = get_weapon("dagger")
        dagger2 = get_weapon("dagger")
        assert dagger1 is not dagger2

    def test_get_weapon_not_found(self):
        """Should raise KeyError for unknown weapon."""
        with pytest.raises(KeyError):
            get_weapon("not_a_weapon")

    def test_weapon_properties(self):
        """Weapons should have correct properties."""
        dagger = get_weapon("dagger")
        assert WeaponProperty.FINESSE in dagger.properties
        assert WeaponProperty.LIGHT in dagger.properties
        assert WeaponProperty.THROWN in dagger.properties
        assert dagger.is_finesse
        assert dagger.is_light
        assert not dagger.is_heavy
        assert not dagger.is_two_handed

    def test_greatsword_properties(self):
        """Greatsword should be heavy and two-handed."""
        greatsword = get_weapon("greatsword")
        assert greatsword.damage_dice == "2d6"
        assert greatsword.is_heavy
        assert greatsword.is_two_handed
        assert greatsword.category == WeaponCategory.MARTIAL

    def test_longbow_properties(self):
        """Longbow should be ranged with ammunition."""
        longbow = get_weapon("longbow")
        assert longbow.is_ranged
        assert WeaponProperty.AMMUNITION in longbow.properties
        assert longbow.range_normal == 150
        assert longbow.range_long == 600

    def test_versatile_weapon(self):
        """Versatile weapons should have alternate damage dice."""
        longsword = get_weapon("longsword")
        assert WeaponProperty.VERSATILE in longsword.properties
        assert longsword.damage_dice == "1d8"
        assert longsword.versatile_dice == "1d10"

    def test_list_weapons(self):
        """Should list all weapons."""
        weapons = list_weapons()
        assert len(weapons) == len(WEAPON_REGISTRY)
        assert any(w.id == "dagger" for w in weapons)

    def test_list_weapons_by_category(self):
        """Should filter weapons by category."""
        simple = list_weapons(WeaponCategory.SIMPLE)
        martial = list_weapons(WeaponCategory.MARTIAL)

        assert all(w.category == WeaponCategory.SIMPLE for w in simple)
        assert all(w.category == WeaponCategory.MARTIAL for w in martial)
        assert len(simple) + len(martial) == len(WEAPON_REGISTRY)


class TestArmor:
    """Tests for armor definitions."""

    def test_get_armor(self):
        """Should retrieve armor by ID."""
        leather = get_armor("leather")
        assert leather.name == "Leather Armor"
        assert leather.armor_type == ArmorType.LIGHT
        assert leather.base_ac == 11

    def test_get_armor_copy(self):
        """get_armor should return a copy, not the original."""
        armor1 = get_armor("leather")
        armor2 = get_armor("leather")
        assert armor1 is not armor2

    def test_light_armor_ac(self):
        """Light armor should add full DEX modifier."""
        leather = get_armor("leather")
        assert leather.calculate_ac(dex_modifier=3) == 14  # 11 + 3
        assert leather.calculate_ac(dex_modifier=-1) == 10  # 11 - 1

    def test_medium_armor_ac(self):
        """Medium armor should cap DEX bonus at 2."""
        chain_shirt = get_armor("chain_shirt")
        assert chain_shirt.armor_type == ArmorType.MEDIUM
        assert chain_shirt.max_dex_bonus == 2
        assert chain_shirt.calculate_ac(dex_modifier=1) == 14  # 13 + 1
        assert chain_shirt.calculate_ac(dex_modifier=3) == 15  # 13 + 2 (capped)
        assert chain_shirt.calculate_ac(dex_modifier=5) == 15  # 13 + 2 (capped)

    def test_heavy_armor_ac(self):
        """Heavy armor should not add DEX modifier."""
        plate = get_armor("plate")
        assert plate.armor_type == ArmorType.HEAVY
        assert plate.calculate_ac(dex_modifier=5) == 18  # No DEX added
        assert plate.calculate_ac(dex_modifier=-2) == 18  # No DEX subtracted

    def test_stealth_disadvantage(self):
        """Some armor should impose stealth disadvantage."""
        leather = get_armor("leather")
        chain_mail = get_armor("chain_mail")

        assert leather.stealth_disadvantage is False
        assert chain_mail.stealth_disadvantage is True

    def test_strength_requirement(self):
        """Heavy armor should have strength requirements."""
        chain_mail = get_armor("chain_mail")
        plate = get_armor("plate")

        assert chain_mail.strength_required == 13
        assert plate.strength_required == 15

    def test_get_shield(self):
        """Should retrieve shield by ID."""
        shield = get_shield("shield")
        assert shield.name == "Shield"
        assert shield.ac_bonus == 2

    def test_list_armor(self):
        """Should list all armor."""
        armor = list_armor()
        assert len(armor) == len(ARMOR_REGISTRY)

    def test_list_armor_by_type(self):
        """Should filter armor by type."""
        light = list_armor(ArmorType.LIGHT)
        medium = list_armor(ArmorType.MEDIUM)
        heavy = list_armor(ArmorType.HEAVY)

        assert all(a.armor_type == ArmorType.LIGHT for a in light)
        assert all(a.armor_type == ArmorType.MEDIUM for a in medium)
        assert all(a.armor_type == ArmorType.HEAVY for a in heavy)


class TestConsumables:
    """Tests for consumable items."""

    def test_get_consumable(self):
        """Should retrieve a consumable by ID."""
        potion = get_consumable("potion_of_healing")
        assert potion.name == "Potion of Healing"
        assert potion.healing_dice == "2d4+2"

    def test_get_ammunition(self):
        """Should retrieve ammunition by ID."""
        arrows = get_ammunition("arrows")
        assert arrows.name == "Arrows (20)"
        assert arrows.quantity == 20
        assert "longbow" in arrows.weapon_types

    def test_list_potions(self):
        """Should list all healing potions."""
        potions = list_potions()
        assert len(potions) >= 4  # At least the 4 healing potions
        assert all(p.healing_dice is not None for p in potions)
