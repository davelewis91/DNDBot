# Dice Module

The `dice` module provides abstractions for D&D dice notation, replacing scattered `random.randint()` calls with a standardized API.

## Overview

The module handles standard D&D dice notation (e.g., "2d6+3") and provides specialized support for d20 rolls with advantage/disadvantage.

## Core Components

### DiceResult

A Pydantic model containing the result of a dice roll:

```python
from dnd_bot.dice import roll

result = roll("2d6+3")
print(result.rolls)     # [4, 2] - Individual die results
print(result.modifier)  # 3 - The modifier
print(result.total)     # 9 - Sum of rolls + modifier
print(result.notation)  # "2d6+3" - Original notation
print(result)           # "9 [4, 2]+3" - Formatted string
```

### Dice

A Pydantic model that parses and represents dice notation:

```python
from dnd_bot.dice import Dice

# Parse notation
dice = Dice.parse("2d6+3")
print(dice.count)     # 2
print(dice.sides)     # 6
print(dice.modifier)  # 3

# Roll the dice
result = dice.roll()
print(result.total)  # 5-15 (random)
```

Supported notation formats:
- `d20` - Single die (count defaults to 1)
- `2d6` - Multiple dice
- `1d8+3` - With positive modifier
- `2d4-1` - With negative modifier

### roll()

Convenience function that parses and rolls in one step:

```python
from dnd_bot.dice import roll

result = roll("1d6")
print(result.total)  # 1-6

result = roll("2d10+5")
print(result.total)  # 7-25
```

### d20()

Specialized function for d20 rolls with advantage/disadvantage support:

```python
from dnd_bot.dice import d20

# Normal roll
result = d20()
print(result.total)  # 1-20

# With advantage (roll twice, take higher)
result = d20(advantage=True)
print(result.rolls)  # [12, 18] - Both rolls shown
print(result.total)  # 18 - Higher value used

# With disadvantage (roll twice, take lower)
result = d20(disadvantage=True)
print(result.rolls)  # [12, 18]
print(result.total)  # 12 - Lower value used

# Advantage + disadvantage cancel out
result = d20(advantage=True, disadvantage=True)
print(len(result.rolls))  # 1 - Normal roll

# With modifier
result = d20(modifier=5)
print(result.total)  # 6-25
```

## Usage in Character Classes

The dice module is used throughout the character system:

### Ability Checks, Saves, and Attacks

```python
from dnd_bot.character import Fighter
from dnd_bot.character.abilities import Ability

fighter = Fighter(name="Grog", species=...)

# These methods use d20() internally
total, die_roll = fighter.make_ability_check(Ability.STRENGTH)
total, die_roll = fighter.make_saving_throw(Ability.CONSTITUTION, advantage=True)
total, die_roll = fighter.make_attack_roll(Ability.STRENGTH)
```

### Class Features

```python
# Fighter's Second Wind uses roll("1d10")
healed = fighter.use_second_wind()  # Heals 1d10 + level HP

# Monk's Wholeness of Body uses roll() with martial arts die
monk = OpenHand(name="Li", species=..., level=6)
healed = monk.use_wholeness_of_body()  # Heals martial arts die + WIS mod
```

### Hit Dice

```python
# Spending hit dice during short rest uses roll()
healed = fighter.spend_hit_die()  # Rolls 1d10 + CON mod
```

## Design Decisions

1. **Pydantic Models**: Both `Dice` and `DiceResult` are Pydantic models for validation and serialization.

2. **Separate d20()**: The d20 function is separate from `roll()` because advantage/disadvantage is unique to d20 rolls in D&D 5e.

3. **DiceResult contains all rolls**: For advantage/disadvantage, both rolled values are stored in `rolls`, with `total` reflecting the chosen value. This enables showing "You rolled 12 and 18, taking 18 with advantage."

4. **Notation in result**: The original notation is preserved in the result for logging and display purposes.
