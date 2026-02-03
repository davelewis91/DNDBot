# Extending the System

This guide covers how to add custom content to the character system.

## Overview

All game data is stored in YAML files under `src/dnd_bot/data/`. To add custom content, you can either:

1. **Edit the existing YAML files** to add new items, classes, etc.
2. **Create custom loader functions** for your own YAML files

## YAML File Structure

```
src/dnd_bot/data/
├── items/
│   ├── weapons.yaml      # Weapon definitions
│   ├── armor.yaml        # Armor definitions
│   ├── shields.yaml      # Shield definitions
│   ├── consumables.yaml  # Potions and other consumables
│   └── ammunition.yaml   # Arrows, bolts, bullets
├── classes/
│   ├── fighter.yaml      # Fighter class
│   ├── rogue.yaml        # Rogue class
│   ├── barbarian.yaml    # Barbarian class
│   └── monk.yaml         # Monk class
├── subclasses/
│   ├── fighter.yaml      # Champion subclass
│   ├── rogue.yaml        # Thief subclass
│   ├── barbarian.yaml    # Berserker subclass
│   └── monk.yaml         # Way of the Open Hand subclass
└── species.yaml          # All species definitions
```

## Custom Weapons

Add weapons to `src/dnd_bot/data/items/weapons.yaml`:

```yaml
# Simple weapon example
magic_dagger:
  name: Dagger of Venom
  category: simple
  damage_dice: "1d4"
  damage_type: piercing
  weight: 1.0
  value: 2500
  properties: [finesse, light, thrown]
  range_normal: 20
  range_long: 60
  rarity: rare
  magical: true
  description: "A curved blade that glistens with poison."

# Martial weapon example
flame_tongue:
  name: Flame Tongue Longsword
  category: martial
  damage_dice: "1d8"
  damage_type: slashing
  weight: 3.0
  value: 5000
  properties: [versatile]
  versatile_dice: "1d10"
  rarity: rare
  magical: true
  description: "A magical longsword wreathed in fire."
```

### Weapon Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name |
| `category` | `simple` \| `martial` | Yes | Weapon proficiency category |
| `damage_dice` | string | Yes | Damage dice (e.g., "1d8", "2d6") |
| `damage_type` | string | Yes | bludgeoning, piercing, slashing, etc. |
| `weight` | float | No | Weight in pounds (default: 0) |
| `value` | int | No | Value in copper pieces (default: 0) |
| `properties` | list | No | finesse, light, heavy, two_handed, versatile, thrown, ammunition, loading, reach, monk |
| `range_normal` | int | No | Normal range in feet (for ranged/thrown) |
| `range_long` | int | No | Long range in feet |
| `versatile_dice` | string | No | Damage when used two-handed |
| `rarity` | string | No | common, uncommon, rare, very_rare, legendary, artifact |
| `magical` | bool | No | Whether the item is magical (default: false) |
| `description` | string | No | Item description |

## Custom Armor

Add armor to `src/dnd_bot/data/items/armor.yaml`:

```yaml
mithral_chain:
  name: Mithral Chain Shirt
  armor_type: medium
  base_ac: 13
  max_dex_bonus: 2
  stealth_disadvantage: false  # Mithral removes disadvantage
  weight: 10.0
  value: 5000
  rarity: uncommon
  magical: true
  description: "A chain shirt made of mithral, light as cloth."

adamantine_plate:
  name: Adamantine Plate
  armor_type: heavy
  base_ac: 18
  strength_required: 15
  stealth_disadvantage: true
  weight: 65.0
  value: 10000
  rarity: uncommon
  magical: true
  description: "Plate armor reinforced with adamantine."
```

### Armor Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name |
| `armor_type` | `light` \| `medium` \| `heavy` | Yes | Armor category |
| `base_ac` | int | Yes | Base AC provided |
| `max_dex_bonus` | int | No | Max DEX bonus (null = unlimited, 0 = no DEX) |
| `strength_required` | int | No | Min STR to avoid speed penalty |
| `stealth_disadvantage` | bool | No | Imposes stealth disadvantage (default: false) |
| `weight` | float | No | Weight in pounds |
| `value` | int | No | Value in copper pieces |

## Custom Subclasses

Add subclasses to the appropriate file in `src/dnd_bot/data/subclasses/`. For example, add a Battle Master to `fighter.yaml`:

```yaml
battle_master:
  name: Battle Master
  parent_class: fighter
  description: "Masters of combat maneuvers and tactical superiority."
  features:
    - name: Combat Superiority
      level: 3
      description: >
        You learn maneuvers powered by superiority dice.
        You have four d8 superiority dice.
      mechanic:
        type: resource
        resource_name: Superiority Dice
        uses_per_rest: 4
        recover_on: short
        dice: "1d8"

    - name: Student of War
      level: 3
      description: "You gain proficiency with one type of artisan's tools."
      mechanic:
        type: passive

    - name: Know Your Enemy
      level: 7
      description: >
        You can study a creature for 1 minute to learn certain info
        about its capabilities.
      mechanic:
        type: passive

    - name: Improved Combat Superiority
      level: 10
      description: "Your superiority dice become d10s."
      mechanic:
        type: passive
        extra_data:
          dice_upgrade: "1d10"

    - name: Relentless
      level: 15
      description: >
        When you roll initiative and have no superiority dice remaining,
        you regain one superiority die.
      mechanic:
        type: passive
```

### Feature Mechanic Types

| Type | Usage | Examples |
|------|-------|----------|
| `passive` | Always active | Sneak Attack, Unarmored Defense |
| `resource` | Limited uses per rest | Second Wind, Rage, Focus Points |
| `toggle` | Activate/deactivate | Rage (while active) |
| `reaction` | Uses reaction | Uncanny Dodge, Deflect Missiles |

### Feature Mechanic Schema

```yaml
mechanic:
  type: resource        # passive, resource, toggle, or reaction
  resource_name: "Name" # Display name for resource tracking
  uses_per_rest: 2      # Fixed number of uses
  uses_per_rest_formula: "level"  # Or formula based on level
  recover_on: short     # short or long
  dice: "1d8"           # Associated dice (for superiority, etc.)
  dice_per_level:       # Scaling dice table
    1: "1d6"
    5: "1d8"
    11: "1d10"
  bonus: 2              # Static bonus value
  extra_data:           # Arbitrary mechanic-specific data
    critical_range: [19, 20]
    damage_bonus: 2
    resistances: ["fire"]
```

## Custom Species

Add species to `src/dnd_bot/data/species.yaml`:

```yaml
tiefling:
  name: Tiefling
  size: medium
  speed: 30
  darkvision: 60
  creature_type: humanoid
  languages:
    - Common
    - Infernal
  traits:
    - name: Darkvision
      description: "You can see in dim light within 60 feet as if bright light."
    - name: Hellish Resistance
      description: "You have resistance to fire damage."
    - name: Infernal Legacy
      description: "You know the thaumaturgy cantrip."
```

### Species Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name |
| `size` | `small` \| `medium` | Yes | Creature size |
| `speed` | int | Yes | Base walking speed in feet |
| `darkvision` | int | No | Darkvision range in feet (default: 0) |
| `creature_type` | string | No | Creature type (default: humanoid) |
| `languages` | list | No | Known languages |
| `traits` | list | Yes | Species traits with name and description |

**Note**: Adding a new species also requires adding it to the `SpeciesName` enum in `character/species.py`.

## Custom Classes

Add classes to `src/dnd_bot/data/classes/`. Each class gets its own file (e.g., `wizard.yaml`):

```yaml
name: Wizard
hit_die: 6
saving_throws:
  - intelligence
  - wisdom
skill_choices:
  count: 2
  options:
    - arcana
    - history
    - insight
    - investigation
    - medicine
    - religion
features:
  - name: Spellcasting
    level: 1
    description: "You can cast wizard spells."
    mechanic:
      type: passive

  - name: Arcane Recovery
    level: 1
    description: >
      Once per day during a short rest, you can recover spell slots
      with a combined level equal to half your wizard level (rounded up).
    mechanic:
      type: resource
      resource_name: Arcane Recovery
      uses_per_rest: 1
      recover_on: long
```

**Note**: Adding a new class also requires adding it to the `ClassName` enum in `character/classes.py` and updating the data loader.

## Custom Consumables

Add consumables to `src/dnd_bot/data/items/consumables.yaml`:

```yaml
potion_of_invisibility:
  name: Potion of Invisibility
  uses: 1
  effect: "You become invisible for 1 hour."
  rarity: very_rare
  value: 5000
  description: "A clear liquid that makes you invisible when consumed."

potion_of_speed:
  name: Potion of Speed
  uses: 1
  effect: "You gain the effects of the haste spell for 1 minute."
  rarity: very_rare
  value: 4000
```

## Using Custom Content

After adding custom content to YAML files, use the standard API:

```python
from dnd_bot.items import get_weapon, get_armor, list_weapons
from dnd_bot.character import get_subclass, list_subclasses, get_all_subclasses, ClassName

# Get your custom weapon
flame_tongue = get_weapon("flame_tongue")
print(f"{flame_tongue.name}: {flame_tongue.damage_dice}")

# List all weapons including custom ones
all_weapon_ids = list_weapons()

# Get your custom subclass
battle_master = get_subclass("battle_master")
for feature in battle_master.features:
    print(f"Level {feature.level}: {feature.name}")

# List subclass IDs for a class
fighter_ids = list_subclasses(ClassName.FIGHTER)

# Or get all subclasses as objects
fighter_subclasses = get_all_subclasses(ClassName.FIGHTER)
```

## Clearing Cache

If you modify YAML files at runtime, clear the cache to reload:

```python
from dnd_bot.data import clear_cache

clear_cache()  # Forces reload on next access
```

## Testing Custom Content

Always test custom content:

```python
import pytest
from dnd_bot.character import create_character, ClassName, SpeciesName

def test_battle_master_superiority_dice():
    char = create_character(
        name="Battle Master",
        species_name=SpeciesName.HUMAN,
        class_name=ClassName.FIGHTER,
        level=3,
        subclass_id="battle_master",
    )

    resource = char.resources.get_feature("Superiority Dice")
    assert resource is not None
    assert resource.maximum == 4
```
