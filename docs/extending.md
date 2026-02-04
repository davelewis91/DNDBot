# Extending the System

This guide covers how to add custom content to the character system.

## Overview

The system uses two approaches for game data:

1. **YAML files** for items (weapons, armor, consumables, species)
2. **Python classes** for character classes and subclasses

## YAML File Structure

```
src/dnd_bot/data/
├── items/
│   ├── weapons.yaml      # Weapon definitions
│   ├── armor.yaml        # Armor definitions
│   ├── shields.yaml      # Shield definitions
│   ├── consumables.yaml  # Potions and other consumables
│   └── ammunition.yaml   # Arrows, bolts, bullets
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

Character classes are defined as Python classes, not YAML. To add a new class:

### 1. Create a new file (e.g., `src/dnd_bot/character/wizard.py`):

```python
from typing import Literal

from .abilities import Ability
from .base import Character, ClassFeature
from .resources import RestType


class Wizard(Character):
    """Wizard - arcane spellcaster."""

    class_type: Literal["wizard"] = "wizard"

    @property
    def hit_die(self) -> int:
        return 6

    @property
    def class_saving_throws(self) -> list[Ability]:
        return [Ability.INTELLIGENCE, Ability.WISDOM]

    @property
    def class_features(self) -> list[ClassFeature]:
        features = [
            ClassFeature(
                name="Spellcasting",
                level=1,
                description="You can cast wizard spells.",
            ),
            ClassFeature(
                name="Arcane Recovery",
                level=1,
                description="Recover spell slots during a short rest.",
            ),
        ]
        return [f for f in features if f.level <= self.level]

    def model_post_init(self, __context) -> None:
        """Initialize wizard-specific resources after model creation."""
        super().model_post_init(__context)
        # Register Arcane Recovery resource
        self.resources.add_feature(
            name="Arcane Recovery",
            maximum=1,
            recover_on=RestType.LONG,
        )

    def use_arcane_recovery(self, spell_slot_levels: int) -> bool:
        """Use Arcane Recovery to recover spell slots.

        Args:
            spell_slot_levels: Total levels of spell slots to recover.

        Returns:
            True if successful, False if not available.
        """
        max_levels = (self.level + 1) // 2
        if spell_slot_levels > max_levels:
            return False
        return self.resources.use_feature("Arcane Recovery")
```

### 2. Add to `types.py`:

```python
from .wizard import Wizard

# Add to the union
AnyCharacter = Annotated[
    Union[  # noqa: UP007
        Fighter, Champion,
        Barbarian, Berserker,
        Rogue, Thief,
        Monk, OpenHand,
        Wizard,  # Add new class
    ],
    Field(discriminator="class_type"),
]

# Add to CHARACTER_CLASSES
CHARACTER_CLASSES = {
    "fighter": Fighter,
    "champion": Champion,
    # ... existing ...
    "wizard": Wizard,
}
```

### 3. Export from `__init__.py`:

```python
from .wizard import Wizard
```

## Custom Subclasses

Subclasses extend their parent class:

```python
# In wizard.py or a new file
class Evoker(Wizard):
    """School of Evocation - explosive magic specialist."""

    class_type: Literal["evoker"] = "evoker"

    @property
    def class_features(self) -> list[ClassFeature]:
        features = super().class_features + [
            ClassFeature(
                name="Sculpt Spells",
                level=2,
                description="Create pockets of safety in your evocation spells.",
            ),
            ClassFeature(
                name="Potent Cantrip",
                level=6,
                description="Your damaging cantrips affect even creatures that succeed on saves.",
            ),
            ClassFeature(
                name="Empowered Evocation",
                level=10,
                description="Add INT modifier to evocation spell damage.",
            ),
            ClassFeature(
                name="Overchannel",
                level=14,
                description="Deal maximum damage with a spell.",
            ),
        ]
        return [f for f in features if f.level <= self.level]

    def get_empowered_damage_bonus(self) -> int:
        """Get the damage bonus from Empowered Evocation."""
        if self.level < 10:
            return 0
        return self.get_ability_modifier(Ability.INTELLIGENCE)
```

Then add `Evoker` to `types.py` and `__init__.py` as shown above.

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

### Items (YAML)

After adding custom content to YAML files, use the standard API:

```python
from dnd_bot.items import get_weapon, get_armor, list_weapons

# Get your custom weapon
flame_tongue = get_weapon("flame_tongue")
print(f"{flame_tongue.name}: {flame_tongue.damage_dice}")

# List all weapons including custom ones
all_weapon_ids = list_weapons()
```

### Classes (Python)

After adding a custom class, use `create_character()`:

```python
from dnd_bot.character import create_character, SpeciesName

wizard = create_character(
    name="Gandalf",
    species_name=SpeciesName.HUMAN,
    class_type="wizard",
    level=5,
)

# Use class methods
wizard.use_arcane_recovery(2)
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
from dnd_bot.character import create_character, SpeciesName

def test_wizard_arcane_recovery():
    wizard = create_character(
        name="Test Wizard",
        species_name=SpeciesName.HUMAN,
        class_type="wizard",
        level=5,
    )

    # Can recover up to 3 levels of spell slots at level 5
    assert wizard.use_arcane_recovery(3)
    assert not wizard.use_arcane_recovery(1)  # Already used

def test_wizard_class_type():
    wizard = create_character(
        name="Test",
        species_name=SpeciesName.HUMAN,
        class_type="wizard",
    )
    assert wizard.class_type == "wizard"
    assert wizard.hit_die == 6
```
