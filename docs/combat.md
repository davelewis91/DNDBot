# Combat Mechanics

This guide covers combat-related mechanics including attack rolls, damage, conditions, and death saves.

## Attack Rolls

```python
from dnd_bot.character import Ability

# Make an attack roll
# Returns (total, die_roll)
total, roll = char.make_attack_roll(
    ability=Ability.STRENGTH,  # or DEXTERITY for finesse/ranged
    is_proficient=True,
    advantage=False,
    disadvantage=False,
)

print(f"Rolled {roll}, total {total}")

# Check for critical hit
if roll in char.get_critical_range():
    print("Critical hit!")
```

### Critical Range

Most characters crit on a natural 20. Champions expand this:

```python
# Default
char.get_critical_range()  # [20]

# Champion (level 3+)
champion.get_critical_range()  # [19, 20]

# Champion (level 15+)
high_champion.get_critical_range()  # [18, 19, 20]
```

## Ability Checks and Saving Throws

```python
# Ability check
total, roll = char.make_ability_check(
    ability=Ability.STRENGTH,
    advantage=False,
    disadvantage=False,
)

# Skill check (includes proficiency if applicable)
total, roll = char.make_skill_check(
    skill=Skill.STEALTH,
    advantage=False,
    disadvantage=False,
)

# Saving throw
total, roll = char.make_saving_throw(
    ability=Ability.DEXTERITY,
    advantage=False,
    disadvantage=False,
)
```

### Exhaustion Penalty

All d20 tests (attack rolls, ability checks, saving throws) include the exhaustion penalty:

```python
char.exhaustion.level = 3
total, roll = char.make_ability_check(Ability.STRENGTH)
# total = roll + modifier - 3 (exhaustion penalty)
```

## Damage and Healing

```python
# Take damage
actual_damage = char.take_damage(15)
print(f"Took {actual_damage} damage, now at {char.current_hp} HP")

# Temporary HP absorbs damage first
char.set_temp_hp(10)
char.take_damage(5)  # Reduces temp HP to 5

# Heal
actual_heal = char.heal(20)
print(f"Healed {actual_heal} HP, now at {char.current_hp}/{char.max_hp}")
```

### Damage at 0 HP

Taking damage while at 0 HP causes death save failures:

```python
char.current_hp = 0
char.take_damage(10)  # Adds 1 death save failure
char.take_damage(10, is_critical=True)  # Adds 2 failures
```

## Death Saving Throws

When at 0 HP, characters make death saving throws:

```python
from dnd_bot.character import DeathSaveOutcome

result = char.make_death_save()

print(f"Rolled: {result.roll}")
print(f"Outcome: {result.outcome}")
print(f"Successes: {result.successes}, Failures: {result.failures}")

# Check outcome
if result.outcome == DeathSaveOutcome.CRITICAL_SUCCESS:
    print("Nat 20! Regained 1 HP")
elif result.outcome == DeathSaveOutcome.CRITICAL_FAILURE:
    print("Nat 1! Two failures")
elif result.outcome == DeathSaveOutcome.STABILIZED:
    print("Three successes - stabilized!")
elif result.outcome == DeathSaveOutcome.DEAD:
    print("Three failures - dead")
```

### Death Save Rules

- **10+**: Success
- **9 or lower**: Failure
- **Natural 20**: Regain 1 HP, reset death saves
- **Natural 1**: Two failures
- **3 successes**: Stabilized (unconscious but not dying)
- **3 failures**: Death

Healing above 0 HP resets death saves automatically.

## Conditions

### Adding and Removing Conditions

```python
from dnd_bot.character import Condition

# Add a condition
char.add_condition(
    condition=Condition.POISONED,
    source="Giant Spider",
    duration=10,  # rounds (None for indefinite)
)

# Check for condition
if char.has_condition(Condition.POISONED):
    print("Character is poisoned")

# Remove condition
removed = char.remove_condition(Condition.POISONED)
print(f"Removed {removed} poisoned condition(s)")

# Remove by source
char.remove_condition(Condition.FRIGHTENED, source="Dragon")
```

### Available Conditions

| Condition | Effect |
|-----------|--------|
| BLINDED | Can't see, auto-fail sight checks |
| CHARMED | Can't attack charmer, charmer has advantage on social checks |
| DEAFENED | Can't hear, auto-fail hearing checks |
| FRIGHTENED | Disadvantage on checks/attacks while source visible |
| GRAPPLED | Speed becomes 0 |
| INCAPACITATED | Can't take actions or reactions |
| INVISIBLE | Heavily obscured, advantage on attacks |
| PARALYZED | Incapacitated, auto-fail STR/DEX saves |
| PETRIFIED | Turned to stone, incapacitated |
| POISONED | Disadvantage on attacks and ability checks |
| PRONE | Disadvantage on attacks, melee attacks have advantage |
| RESTRAINED | Speed 0, disadvantage on attacks and DEX saves |
| STUNNED | Incapacitated, auto-fail STR/DEX saves |
| UNCONSCIOUS | Incapacitated, drop what holding, fall prone |

### Condition Helpers

```python
# Check for advantage/disadvantage on attacks
if char.conditions.has_attack_disadvantage():
    print("Has disadvantage on attacks")

if char.conditions.has_advantage_on_attacks():
    print("Has advantage on attacks")

# Get all active conditions
for active in char.conditions.active:
    print(f"{active.condition.value} from {active.source}")
```

## Exhaustion

D&D 2024 exhaustion rules (levels 0-10):

```python
# Add exhaustion
char.exhaustion.add(1)

# Check level and penalty
print(f"Exhaustion level: {char.exhaustion.level}")
print(f"Penalty to d20 tests: {char.exhaustion.penalty}")  # -1 per level

# Remove exhaustion (long rest removes 1 level)
char.exhaustion.remove(1)

# Check for death
if char.exhaustion.is_dead:
    print("Exhaustion level 10 - dead!")
```

## Class Features in Combat

### Fighter

```python
# Second Wind (1/short rest)
if char.can_use_second_wind():
    healed = char.use_second_wind()  # 1d10 + level HP
    print(f"Second Wind healed {healed} HP")

# Action Surge (1/short rest, level 2+)
if char.can_use_action_surge():
    char.use_action_surge()
    print("Action Surge! Take an additional action")
```

### Rogue

```python
# Sneak Attack damage dice
dice = char.get_sneak_attack_dice()
print(f"Sneak Attack: {dice}d6")  # Scales with level
```

### Barbarian

```python
# Enter rage (sets is_raging = True, returns False if no uses remain)
if char.can_rage():
    char.start_rage()
    bonus = char.get_rage_damage_bonus()
    print(f"Raging! +{bonus} damage on STR attacks")

# Check rage state
if char.is_raging:
    print("Currently raging")

# End rage
char.end_rage()  # sets is_raging = False
```

### Monk

```python
# Use Focus Points
if char.use_focus_points(1):
    print("Spent 1 Focus Point for Flurry of Blows")

remaining = char.get_focus_points()
print(f"Focus Points remaining: {remaining}")
```

## Initiative

When the player agent switches to combat mode via `change_mode`, initiative is rolled automatically.
The result is included in the tool's return value so the DM can use it immediately.

```python
# Get initiative modifier
initiative = char.initiative  # DEX modifier

# Roll initiative (standard ability check)
total, roll = char.make_ability_check(Ability.DEXTERITY)

# Or use the dedicated helper (called automatically by change_mode)
total, die_roll = char.roll_initiative()
```

## Passive Perception

```python
passive = char.passive_perception  # 10 + Perception bonus
```
