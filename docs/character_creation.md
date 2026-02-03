# Character Creation

This guide covers creating D&D characters programmatically.

## Basic Character

Use `create_character()` for the simplest approach:

```python
from dnd_bot.character import ClassName, SpeciesName, create_character

# Minimal character with defaults
char = create_character(
    name="Gandalf",
    species_name=SpeciesName.HUMAN,
    class_name=ClassName.FIGHTER,
)
```

This creates a level 1 Human Fighter with:
- Standard ability scores (10 in all abilities)
- No skill proficiencies beyond class defaults
- Max HP calculated from class hit die + CON modifier
- Default equipment (none)

## Custom Ability Scores

```python
from dnd_bot.character import AbilityScores, ClassName, SpeciesName, create_character

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
    class_name=ClassName.FIGHTER,
    ability_scores=scores,
)

# Check modifiers
print(char.get_ability_modifier(Ability.STRENGTH))  # +3
```

## Skill Proficiencies

```python
from dnd_bot.character import Skill

char = create_character(
    name="Shadow",
    species_name=SpeciesName.ELF,
    class_name=ClassName.ROGUE,
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
    class_name=ClassName.FIGHTER,
    level=5,
)

print(char.proficiency_bonus)  # +3 at level 5
print(char.max_hp)  # Higher due to level
```

## Subclasses (Level 3+)

Characters gain a subclass at level 3:

```python
from dnd_bot.character import list_subclasses, get_all_subclasses, get_subclass

# List subclass IDs for a class
fighter_ids = list_subclasses(ClassName.FIGHTER)
for subclass_id in fighter_ids:
    sub = get_subclass(subclass_id)
    print(f"{sub.id}: {sub.name}")

# Or get all subclasses as objects directly
for sub in get_all_subclasses(ClassName.FIGHTER):
    print(f"{sub.id}: {sub.name}")

# Create with subclass
char = create_character(
    name="Champion",
    species_name=SpeciesName.HUMAN,
    class_name=ClassName.FIGHTER,
    level=3,
    subclass_id="champion",
)

# Or set later
char = create_character(
    name="Fighter",
    species_name=SpeciesName.HUMAN,
    class_name=ClassName.FIGHTER,
    level=3,
)
char.set_subclass("champion")
```

Available subclasses:
| Class | Subclass ID | Name |
|-------|-------------|------|
| Fighter | `champion` | Champion |
| Rogue | `thief` | Thief |
| Barbarian | `berserker` | Path of the Berserker |
| Monk | `way_of_the_open_hand` | Way of the Open Hand |

## Background

```python
from dnd_bot.character import Background, Motivation, PersonalityTraits

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
    class_name=ClassName.FIGHTER,
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

# Load
loaded = load_character(filepath)

# List all saved characters
for path in list_characters(Path("characters/")):
    print(path.stem)
```

## Direct Character Construction

For full control, construct the Character directly:

```python
from dnd_bot.character import (
    AbilityScores,
    Character,
    Equipment,
    SkillSet,
    get_class,
    get_species,
)

char = Character(
    name="Custom",
    level=5,
    ability_scores=AbilityScores(strength=18),
    skills=SkillSet(),
    species=get_species(SpeciesName.HUMAN),
    character_class=get_class(ClassName.FIGHTER),
    current_hp=45,
    max_hp=45,
    armor_class=18,
    equipment=Equipment(
        weapon_ids=["greatsword"],
        armor_id="plate",
    ),
)
```
