# Extending the System

This guide covers how to add custom content to the character system.

## Custom Weapons

Add weapons to the registry in `src/dnd_bot/items/weapons.py`:

```python
from dnd_bot.items.base import DamageType, Weapon, WeaponCategory, WeaponProperty

# Define the weapon
MAGIC_SWORD = Weapon(
    id="magic_sword",
    name="Sword of Flame",
    description="A magical longsword wreathed in fire.",
    weight=3.0,
    value=5000,
    category=WeaponCategory.MARTIAL,
    damage_dice="1d8",
    damage_type=DamageType.SLASHING,
    properties=[WeaponProperty.VERSATILE],
    versatile_dice="1d10",
)

# Add to registry
WEAPON_REGISTRY["magic_sword"] = MAGIC_SWORD
```

## Custom Armor

Add armor to the registry in `src/dnd_bot/items/armor.py`:

```python
from dnd_bot.items.base import Armor, ArmorType

MITHRAL_CHAIN = Armor(
    id="mithral_chain",
    name="Mithral Chain Shirt",
    description="A chain shirt made of mithral, light as cloth.",
    weight=10.0,
    value=5000,
    armor_type=ArmorType.MEDIUM,
    base_ac=13,
    max_dex_bonus=2,
    stealth_disadvantage=False,  # Mithral removes disadvantage
    strength_required=None,
)

ARMOR_REGISTRY["mithral_chain"] = MITHRAL_CHAIN
```

## Custom Subclasses

Add subclasses to `src/dnd_bot/character/subclasses.py`:

```python
from dnd_bot.character.classes import (
    ClassFeature,
    ClassName,
    FeatureMechanic,
    FeatureMechanicType,
    RestType,
)
from dnd_bot.character.subclasses import Subclass, SUBCLASS_REGISTRY

BATTLE_MASTER = Subclass(
    id="battle_master",
    name="Battle Master",
    parent_class=ClassName.FIGHTER,
    description="Masters of combat maneuvers and tactical superiority.",
    features=[
        ClassFeature(
            name="Combat Superiority",
            level=3,
            description=(
                "You learn maneuvers powered by superiority dice. "
                "You have four d8 superiority dice."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.RESOURCE,
                resource_name="Superiority Dice",
                uses_per_rest=4,
                recover_on=RestType.SHORT,
                dice="1d8",
            ),
        ),
        ClassFeature(
            name="Know Your Enemy",
            level=7,
            description=(
                "You can study a creature for 1 minute to learn certain info."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        # Add more features for levels 10, 15, 18...
    ],
)

# Register it
SUBCLASS_REGISTRY["battle_master"] = BATTLE_MASTER
```

## Custom Species

Add species to `src/dnd_bot/character/species.py`:

```python
from dnd_bot.character.species import (
    CreatureType,
    Size,
    Species,
    SpeciesName,
    Trait,
    SPECIES_REGISTRY,
)

# First, add to the enum (requires modifying SpeciesName)
# SpeciesName.TIEFLING = "tiefling"

TIEFLING = Species(
    name=SpeciesName.TIEFLING,  # After adding to enum
    creature_type=CreatureType.HUMANOID,
    size=Size.MEDIUM,
    speed=30,
    traits=[
        Trait(
            name="Darkvision",
            description="You can see in dim light within 60 feet as if bright light.",
        ),
        Trait(
            name="Hellish Resistance",
            description="You have resistance to fire damage.",
        ),
        Trait(
            name="Infernal Legacy",
            description="You know the thaumaturgy cantrip.",
        ),
    ],
)

SPECIES_REGISTRY[SpeciesName.TIEFLING] = TIEFLING
```

## Custom Class Features

Extend existing classes in `src/dnd_bot/character/classes.py`:

```python
# Add a new feature to Fighter
FIGHTER.features.append(
    ClassFeature(
        name="Indomitable",
        level=9,
        description=(
            "You can reroll a saving throw that you fail. "
            "You must use the new roll."
        ),
        mechanic=FeatureMechanic(
            mechanic_type=FeatureMechanicType.RESOURCE,
            resource_name="Indomitable",
            uses_per_rest=1,
            recover_on=RestType.LONG,
        ),
    )
)
```

## Custom Conditions

Add conditions in `src/dnd_bot/character/conditions.py`:

```python
from enum import Enum

# Extend the Condition enum (requires modifying the source)
class Condition(str, Enum):
    # ... existing conditions ...
    EXHAUSTED = "exhausted"  # Custom condition

# Add condition effects to CONDITION_EFFECTS dict
CONDITION_EFFECTS[Condition.EXHAUSTED] = {
    "attack_disadvantage": True,
    "ability_check_disadvantage": True,
}
```

## Feature Mechanic Types

When creating features, use the appropriate mechanic type:

| Type | Usage | Examples |
|------|-------|----------|
| `PASSIVE` | Always active | Sneak Attack, Unarmored Defense |
| `RESOURCE` | Limited uses per rest | Second Wind, Rage, Focus Points |
| `TOGGLE` | Activate/deactivate | Rage (while active) |
| `REACTION` | Uses reaction | Uncanny Dodge, Deflect Missiles |

## Adding Extra Data

Use `extra_data` for mechanic-specific information:

```python
FeatureMechanic(
    mechanic_type=FeatureMechanicType.PASSIVE,
    extra_data={
        "critical_range": [19, 20],  # For Improved Critical
        "damage_bonus": 2,           # For Rage damage
        "speed_bonus": 10,           # For Fast Movement
        "resistances": ["fire"],     # For damage resistances
    },
)
```

## YAML Data Files (Future)

For user-extensible content, YAML files can be used:

```yaml
# custom_weapons.yaml
magic_sword:
  name: "Sword of Flame"
  category: martial
  damage_dice: "1d8"
  damage_type: slashing
  properties:
    - versatile
  versatile_dice: "1d10"
  value: 5000
```

Load with a custom registry loader (to be implemented).

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
