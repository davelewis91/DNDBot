# DNDBot Character System

A Python library for D&D 5e (2024 edition) character management with full mechanical support.

## Features

- **Complete Character Model**: Abilities, skills, species, classes, backgrounds
- **Four Martial Classes**: Fighter, Rogue, Barbarian, Monk (levels 1-20)
- **Subclasses**: Champion, Thief, Berserker, Way of the Open Hand
- **Combat Mechanics**: Attack rolls, saving throws, damage, death saves
- **Conditions & Exhaustion**: All 14 standard conditions, exhaustion levels 0-10
- **Resource Tracking**: Hit dice, class features (Second Wind, Rage, Focus Points)
- **Rest System**: Short rests (2 per long rest) and long rests with proper recovery
- **Items System**: 21 weapons, 12 armors, potions, ammunition
- **AC Calculation**: Armor types, shields, unarmored defense (Barbarian/Monk)
- **YAML Persistence**: Human-readable character storage

## Quick Start

```python
from dnd_bot.character import (
    AbilityScores,
    Champion,
    SpeciesName,
    Skill,
    create_character,
    save_character,
    load_character,
)

# Create a level 3 Champion Fighter
champion = create_character(
    name="Thorin Ironforge",
    species_name=SpeciesName.DWARF,
    class_type="champion",  # Use subclass name directly
    level=3,
    ability_scores=AbilityScores(
        strength=16,
        dexterity=12,
        constitution=16,
        intelligence=10,
        wisdom=12,
        charisma=8,
    ),
    skill_proficiencies=[Skill.ATHLETICS, Skill.PERCEPTION],
)

# Check character stats
print(f"HP: {champion.current_hp}/{champion.max_hp}")
print(f"AC: {champion.armor_class}")
print(f"Critical range: {champion.get_critical_range()}")  # [19, 20] for Champion

# Use class features directly on the character
if champion.can_use_second_wind():
    healed = champion.use_second_wind()
    print(f"Second Wind healed {healed} HP")

# Save to YAML
filepath = save_character(champion, "characters/")
print(f"Saved to {filepath}")

# Load later - automatically returns the correct class type
loaded = load_character(filepath)
assert isinstance(loaded, Champion)
```

## Architecture

The character system uses an **inheritance-based architecture** where each D&D class is a Python class:

```
Character (base)           <- ability checks, HP, AC, species, rests, exhaustion
    ├── Fighter            <- Second Wind, Action Surge, Extra Attack
    │   └── Champion       <- Improved Critical, Superior Critical
    ├── Barbarian          <- Rage, Unarmored Defense
    │   └── Berserker      <- Frenzy, Intimidating Presence
    ├── Rogue              <- Sneak Attack, Cunning Action
    │   └── Thief          <- Fast Hands, Supreme Sneak
    └── Monk               <- Focus Points, Martial Arts
        └── OpenHand       <- Open Hand Technique, Wholeness of Body
```

### File Structure

```
src/dnd_bot/
├── character/
│   ├── abilities.py      # Ability scores and modifiers
│   ├── background.py     # Backstory, motivations, personality
│   ├── base.py           # Character base class
│   ├── fighter.py        # Fighter and Champion classes
│   ├── barbarian.py      # Barbarian and Berserker classes
│   ├── rogue.py          # Rogue and Thief classes
│   ├── monk.py           # Monk and OpenHand classes
│   ├── types.py          # AnyCharacter union, create_character factory
│   ├── conditions.py     # Blinded, Charmed, etc.
│   ├── exhaustion.py     # Exhaustion levels (D&D 2024)
│   ├── resources.py      # Hit dice, feature uses
│   ├── skills.py         # Skills and proficiencies
│   ├── species.py        # Species definitions loader
│   └── storage.py        # YAML save/load
├── items/
│   ├── base.py           # Item, Weapon, Armor models
│   ├── weapons.py        # Weapon definitions loader
│   ├── armor.py          # Armor definitions loader
│   └── consumables.py    # Consumables loader
└── data/                 # YAML game data
    ├── items/
    │   ├── weapons.yaml      # 21 weapon definitions
    │   ├── armor.yaml        # 12 armor definitions
    │   ├── shields.yaml      # Shield definitions
    │   ├── consumables.yaml  # Potions
    │   └── ammunition.yaml   # Arrows, bolts, bullets
    └── species.yaml          # Human, Elf, Dwarf, Halfling
```

## Documentation

- [Character Creation](character_creation.md) - Creating and customizing characters
- [Combat](combat.md) - Attack rolls, damage, death saves, conditions
- [Rests](rests.md) - Short and long rest mechanics
- [Items](items.md) - Weapons, armor, and equipment
- [Extending](extending.md) - Adding custom content

## D&D 2024 Rules

This library follows the D&D 5e 2024 edition rules:

- **Exhaustion**: Levels 0-10, -1 penalty per level to d20 tests, death at 10
- **Short Rests**: Maximum 2 per long rest
- **Class Features**: Updated per 2024 PHB (Martial Arts die, Focus Points, etc.)

## Requirements

- Python 3.13+
- pydantic
- PyYAML

## Development

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```
