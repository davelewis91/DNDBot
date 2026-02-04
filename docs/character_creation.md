# Character Creation

This guide covers creating D&D characters programmatically.

## Basic Character

Use `create_character()` for the simplest approach:

```python
from dnd_bot.character import SpeciesName, create_character

# Minimal character with defaults
char = create_character(
    name="Gandalf",
    species_name=SpeciesName.HUMAN,
    class_type="fighter",
)
```

This creates a level 1 Human Fighter with:
- Standard ability scores (10 in all abilities)
- No skill proficiencies beyond class defaults
- Max HP calculated from class hit die + CON modifier
- Default equipment (none)

## Available Class Types

Use `class_type` to specify the character's class or subclass:

| class_type | Class | Description |
|------------|-------|-------------|
| `"fighter"` | Fighter | Martial weapons master |
| `"champion"` | Champion (Fighter) | Critical hit specialist |
| `"barbarian"` | Barbarian | Rage-fueled warrior |
| `"berserker"` | Berserker (Barbarian) | Frenzy and intimidation |
| `"rogue"` | Rogue | Sneak attack expert |
| `"thief"` | Thief (Rogue) | Fast hands and agility |
| `"monk"` | Monk | Martial arts master |
| `"openhand"` | Way of the Open Hand (Monk) | Unarmed combat specialist |

Subclasses can be created at any level - the subclass features will be available when the character reaches the appropriate level.

## Custom Ability Scores

```python
from dnd_bot.character import AbilityScores, Ability, SpeciesName, create_character

scores = AbilityScores(
    strength=16,
    dexterity=14,
    constitution=14,
    intelligence=10,
    wisdom=12,
    charisma=8,
)

char = create_character(
    name="Thorin",
    species_name=SpeciesName.DWARF,
    class_type="fighter",
    ability_scores=scores,
)

# Check modifiers
print(char.get_ability_modifier(Ability.STRENGTH))  # +3
```

## Skill Proficiencies

```python
from dnd_bot.character import Skill, SpeciesName, create_character

char = create_character(
    name="Shadow",
    species_name=SpeciesName.ELF,
    class_type="rogue",
    skill_proficiencies=[
        Skill.STEALTH,
        Skill.PERCEPTION,
        Skill.DECEPTION,
        Skill.SLEIGHT_OF_HAND,
    ],
)

# Add expertise
char.skills.set_expertise(Skill.STEALTH)

# Check skill bonus
bonus = char.get_skill_bonus(Skill.STEALTH)  # Includes double proficiency
```

## Higher Level Characters

```python
char = create_character(
    name="Veteran",
    species_name=SpeciesName.HUMAN,
    class_type="fighter",
    level=5,
)

print(char.proficiency_bonus)  # +3 at level 5
print(char.max_hp)  # Higher due to level
```

## Subclasses

Subclasses are created directly by specifying the subclass as the `class_type`:

```python
from dnd_bot.character import Champion, Thief, Berserker, OpenHand

# Create a Champion (Fighter subclass)
champion = create_character(
    name="Champion",
    species_name=SpeciesName.HUMAN,
    class_type="champion",
    level=3,
)

# The character is an instance of the Champion class
assert isinstance(champion, Champion)

# Access Champion-specific features
print(champion.get_critical_range())  # [19, 20]

# Create other subclasses similarly
thief = create_character(name="Thief", species_name=SpeciesName.HALFLING, class_type="thief", level=3)
berserker = create_character(name="Berserker", species_name=SpeciesName.HUMAN, class_type="berserker", level=3)
open_hand = create_character(name="Monk", species_name=SpeciesName.HUMAN, class_type="openhand", level=3)
```

## Class Inheritance

Each subclass inherits from its parent class, so all parent methods are available:

```python
from dnd_bot.character import Champion, Fighter

champion = create_character(
    name="Champion",
    species_name=SpeciesName.HUMAN,
    class_type="champion",
    level=5,
)

# Champion is a Fighter subclass
assert isinstance(champion, Champion)
assert isinstance(champion, Fighter)

# Fighter methods available
if champion.can_use_second_wind():
    champion.use_second_wind()

if champion.can_use_action_surge():
    champion.use_action_surge()

# Champion-specific methods
print(champion.get_critical_range())  # [19, 20]
```

## Background

```python
from dnd_bot.character import Background, Motivation, PersonalityTraits, SpeciesName, create_character

background = Background(
    name="Soldier",
    backstory="Served in the king's army for ten years.",
    personality=PersonalityTraits(
        traits=["I am always calm under pressure."],
        ideals=["Greater Good: Protect the innocent."],
        bonds=["I fight for those who cannot fight."],
        flaws=["I have a weakness for fine wine."],
    ),
    motivations=[
        Motivation(
            description="Find the traitor who betrayed my unit",
            priority=1,
            is_secret=True,
        ),
    ],
    fears=["Drowning", "Betrayal"],
    allies=["The Silver Guard"],
    enemies=["The Shadow Syndicate"],
)

char = create_character(
    name="Veteran",
    species_name=SpeciesName.HUMAN,
    class_type="fighter",
    background=background,
)
```

## Equipment

Equipment is tracked by item IDs:

```python
from dnd_bot.items import get_weapon, get_armor, list_weapons

# See available weapons (returns IDs)
for weapon_id in list_weapons():
    weapon = get_weapon(weapon_id)
    print(f"{weapon.id}: {weapon.name} ({weapon.damage_dice})")

# Equip items
char.equipment.weapon_ids = ["longsword", "handaxe"]
char.equipment.armor_id = "chain_mail"
char.equipment.shield_equipped = True
char.equipment.gold = 50

# Recalculate AC after equipping armor
char.recalculate_armor_class()
```

## Available Species

| Species | Traits |
|---------|--------|
| Human | Resourceful, Skillful |
| Elf | Darkvision, Fey Ancestry, Trance |
| Dwarf | Darkvision, Dwarven Resilience, Dwarven Toughness |
| Halfling | Brave, Halfling Nimbleness, Luck |

## Available Classes

| Class | Hit Die | Primary Abilities | Key Features |
|-------|---------|-------------------|--------------|
| Fighter | d10 | STR/DEX, CON | Second Wind, Action Surge, Extra Attack |
| Rogue | d8 | DEX, INT | Sneak Attack, Cunning Action, Expertise |
| Barbarian | d12 | STR, CON | Rage, Reckless Attack, Unarmored Defense |
| Monk | d8 | DEX, WIS | Martial Arts, Focus Points, Unarmored Defense |

## Saving and Loading

```python
from dnd_bot.character import save_character, load_character, list_characters
from pathlib import Path

# Save
filepath = save_character(char, Path("characters/"))

# Load - automatically returns the correct class type
loaded = load_character(filepath)

# List all saved characters
for path in list_characters(Path("characters/")):
    print(path.stem)
```

## Direct Class Construction

For full control, construct the character class directly:

```python
from dnd_bot.character import (
    AbilityScores,
    Equipment,
    Fighter,
    SkillSet,
    SpeciesName,
    get_species,
)

fighter = Fighter(
    name="Custom",
    level=5,
    ability_scores=AbilityScores(strength=18),
    skills=SkillSet(),
    species=get_species(SpeciesName.HUMAN),
    current_hp=45,
    max_hp=45,
    armor_class=18,
    equipment=Equipment(
        weapon_ids=["greatsword"],
        armor_id="plate",
    ),
)

# Or for a subclass
from dnd_bot.character import Champion

champion = Champion(
    name="Custom Champion",
    level=5,
    ability_scores=AbilityScores(strength=18),
    skills=SkillSet(),
    species=get_species(SpeciesName.HUMAN),
)
```

## Type Checking

The library provides full type support:

```python
from dnd_bot.character import AnyCharacter, Fighter, Champion

def process_fighter(fighter: Fighter) -> None:
    # Works with Fighter or any Fighter subclass (Champion)
    fighter.use_second_wind()

def process_any_character(char: AnyCharacter) -> None:
    # Works with any character type
    print(char.name, char.level)
```
