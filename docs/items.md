# Items and Equipment

This guide covers weapons, armor, and equipment.

## Weapons

### Listing Weapons

```python
from dnd_bot.items import list_weapons, get_weapon, get_all_weapons, WeaponCategory

# List all weapon IDs
for weapon_id in list_weapons():
    weapon = get_weapon(weapon_id)
    print(f"{weapon.id}: {weapon.name} - {weapon.damage_dice} {weapon.damage_type.value}")

# Or get all weapons as objects directly
for weapon in get_all_weapons():
    print(f"{weapon.id}: {weapon.name}")

# Filter by category (returns IDs)
simple_ids = list_weapons(WeaponCategory.SIMPLE)
martial_ids = list_weapons(WeaponCategory.MARTIAL)
```

### Getting a Weapon

```python
longsword = get_weapon("longsword")

print(f"Name: {longsword.name}")
print(f"Damage: {longsword.damage_dice} {longsword.damage_type.value}")
print(f"Properties: {[p.value for p in longsword.properties]}")
print(f"Versatile: {longsword.versatile_dice}")  # 1d10 when two-handed
```

### Weapon Properties

```python
# Check properties
weapon.is_finesse    # Can use DEX instead of STR
weapon.is_light      # Good for two-weapon fighting
weapon.is_heavy      # Disadvantage for Small creatures
weapon.is_two_handed # Requires two hands
weapon.is_ranged     # Uses DEX, has range

# Range (ranged/thrown weapons)
print(f"Range: {weapon.range_normal}/{weapon.range_long}")
```

### Available Weapons

#### Simple Melee
| ID | Name | Damage | Properties |
|----|------|--------|------------|
| `club` | Club | 1d4 bludgeoning | Light |
| `dagger` | Dagger | 1d4 piercing | Finesse, Light, Thrown |
| `greatclub` | Greatclub | 1d8 bludgeoning | Two-Handed |
| `handaxe` | Handaxe | 1d6 slashing | Light, Thrown |
| `javelin` | Javelin | 1d6 piercing | Thrown |
| `light_hammer` | Light Hammer | 1d4 bludgeoning | Light, Thrown |
| `mace` | Mace | 1d6 bludgeoning | - |
| `quarterstaff` | Quarterstaff | 1d6 bludgeoning | Versatile (1d8) |
| `sickle` | Sickle | 1d4 slashing | Light |
| `spear` | Spear | 1d6 piercing | Thrown, Versatile (1d8) |

#### Simple Ranged
| ID | Name | Damage | Range | Properties |
|----|------|--------|-------|------------|
| `light_crossbow` | Light Crossbow | 1d8 piercing | 80/320 | Ammunition, Loading, Two-Handed |
| `shortbow` | Shortbow | 1d6 piercing | 80/320 | Ammunition, Two-Handed |
| `sling` | Sling | 1d4 bludgeoning | 30/120 | Ammunition |

#### Martial Melee
| ID | Name | Damage | Properties |
|----|------|--------|------------|
| `battleaxe` | Battleaxe | 1d8 slashing | Versatile (1d10) |
| `glaive` | Glaive | 1d10 slashing | Heavy, Reach, Two-Handed |
| `greataxe` | Greataxe | 1d12 slashing | Heavy, Two-Handed |
| `greatsword` | Greatsword | 2d6 slashing | Heavy, Two-Handed |
| `longsword` | Longsword | 1d8 slashing | Versatile (1d10) |
| `rapier` | Rapier | 1d8 piercing | Finesse |
| `scimitar` | Scimitar | 1d6 slashing | Finesse, Light |
| `shortsword` | Shortsword | 1d6 piercing | Finesse, Light |
| `warhammer` | Warhammer | 1d8 bludgeoning | Versatile (1d10) |

#### Martial Ranged
| ID | Name | Damage | Range | Properties |
|----|------|--------|-------|------------|
| `hand_crossbow` | Hand Crossbow | 1d6 piercing | 30/120 | Ammunition, Light, Loading |
| `heavy_crossbow` | Heavy Crossbow | 1d10 piercing | 100/400 | Ammunition, Heavy, Loading, Two-Handed |
| `longbow` | Longbow | 1d8 piercing | 150/600 | Ammunition, Heavy, Two-Handed |

## Armor

### Listing Armor

```python
from dnd_bot.items import list_armor, get_armor, get_all_armor, ArmorType

# List all armor IDs
for armor_id in list_armor():
    armor = get_armor(armor_id)
    print(f"{armor.id}: {armor.name} - AC {armor.base_ac}")

# Or get all armor as objects directly
for armor in get_all_armor():
    print(f"{armor.id}: {armor.name}")

# Filter by type (returns IDs)
light_ids = list_armor(ArmorType.LIGHT)
medium_ids = list_armor(ArmorType.MEDIUM)
heavy_ids = list_armor(ArmorType.HEAVY)
```

### Getting Armor

```python
plate = get_armor("plate")

print(f"Name: {plate.name}")
print(f"Base AC: {plate.base_ac}")
print(f"Type: {plate.armor_type.value}")
print(f"Stealth Disadvantage: {plate.stealth_disadvantage}")
print(f"Strength Required: {plate.strength_required}")
```

### AC Calculation

```python
# Armor calculates AC based on DEX modifier
leather = get_armor("leather")  # Light armor
ac = leather.calculate_ac(dex_modifier=3)  # 11 + 3 = 14

chain_shirt = get_armor("chain_shirt")  # Medium armor
ac = chain_shirt.calculate_ac(dex_modifier=4)  # 13 + 2 (max) = 15

plate = get_armor("plate")  # Heavy armor
ac = plate.calculate_ac(dex_modifier=4)  # 18 (no DEX)
```

### Available Armor

#### Light Armor
| ID | Name | AC | Stealth Disadvantage |
|----|------|----|--------------------|
| `padded` | Padded Armor | 11 + DEX | Yes |
| `leather` | Leather Armor | 11 + DEX | No |
| `studded_leather` | Studded Leather | 12 + DEX | No |

#### Medium Armor
| ID | Name | AC | Stealth Disadvantage |
|----|------|----|--------------------|
| `hide` | Hide Armor | 12 + DEX (max 2) | No |
| `chain_shirt` | Chain Shirt | 13 + DEX (max 2) | No |
| `scale_mail` | Scale Mail | 14 + DEX (max 2) | Yes |
| `breastplate` | Breastplate | 14 + DEX (max 2) | No |
| `half_plate` | Half Plate | 15 + DEX (max 2) | Yes |

#### Heavy Armor
| ID | Name | AC | STR Required | Stealth Disadvantage |
|----|------|----|--------------|--------------------|
| `ring_mail` | Ring Mail | 14 | - | Yes |
| `chain_mail` | Chain Mail | 16 | 13 | Yes |
| `splint` | Splint Armor | 17 | 15 | Yes |
| `plate` | Plate Armor | 18 | 15 | Yes |

### Shield

```python
from dnd_bot.items import get_shield

shield = get_shield("shield")
print(f"AC Bonus: +{shield.ac_bonus}")  # +2
```

## Equipping Items

```python
# Equip weapons
char.equipment.weapon_ids = ["longsword", "dagger"]

# Equip armor
char.equipment.armor_id = "chain_mail"

# Equip shield
char.equipment.shield_equipped = True

# IMPORTANT: Recalculate AC after changing armor/shield
char.recalculate_armor_class()

# Other items
char.equipment.other_items = ["rope", "torch", "rations"]
char.equipment.gold = 100
```

## Armor Class Calculation

The character's AC is calculated based on:

1. **Equipped Armor**: Base AC + DEX modifier (capped for medium, ignored for heavy)
2. **Shield**: +2 if equipped
3. **Unarmored Defense**: Special AC for Barbarian and Monk

```python
# Standard calculation
char.recalculate_armor_class()
print(char.armor_class)

# Unarmored Defense examples:
# Barbarian: 10 + DEX + CON (can use shield)
# Monk: 10 + DEX + WIS (cannot use shield)
```

## Consumables

### Potions

```python
from dnd_bot.items import get_consumable, list_potions

# List healing potion IDs
for potion_id in list_potions():
    potion = get_consumable(potion_id)
    print(f"{potion.id}: {potion.name} - heals {potion.healing_dice}")

# Get specific potion
healing = get_consumable("potion_of_healing")
print(f"Heals: {healing.healing_dice}")  # 2d4+2
```

| ID | Name | Healing |
|----|------|---------|
| `potion_of_healing` | Potion of Healing | 2d4+2 |
| `potion_of_greater_healing` | Potion of Greater Healing | 4d4+4 |
| `potion_of_superior_healing` | Potion of Superior Healing | 8d4+8 |
| `potion_of_supreme_healing` | Potion of Supreme Healing | 10d4+20 |

### Ammunition

```python
from dnd_bot.items import get_ammunition

arrows = get_ammunition("arrows")
print(f"{arrows.name}: {arrows.quantity} pieces")
print(f"Used with: {arrows.weapon_types}")
```

| ID | Name | Quantity | Weapons |
|----|------|----------|---------|
| `arrows` | Arrows (20) | 20 | longbow, shortbow |
| `bolts` | Crossbow Bolts (20) | 20 | light_crossbow, heavy_crossbow, hand_crossbow |
| `sling_bullets` | Sling Bullets (20) | 20 | sling |
