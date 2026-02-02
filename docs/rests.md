# Rest Mechanics

This guide covers short and long rest mechanics, resource recovery, and hit dice.

## Short Rests

Characters can take up to 2 short rests between long rests.

```python
# Check if short rest is available
if char.can_short_rest():
    result = char.short_rest(hit_dice_to_spend=2)

    print(f"HP recovered: {result.hp_recovered}")
    print(f"Hit dice spent: {result.hit_dice_spent}")
    print(f"Resources recovered: {result.resources_recovered}")
else:
    print("Already taken 2 short rests since last long rest")
```

### Short Rest Recovery

- **Hit Dice**: Spend to heal (roll hit die + CON modifier per die)
- **Short Rest Resources**: Second Wind, Action Surge, Focus Points

```python
# Spend hit dice during short rest
result = char.short_rest(hit_dice_to_spend=3)

# Or spend manually outside of rest
hp_healed = char.spend_hit_die()  # Rolls 1 hit die + CON
```

### Hit Dice Pool

```python
# Check available hit dice
available = char.resources.hit_dice.available
total = char.resources.hit_dice.total  # Equals character level

print(f"Hit dice: {available}/{total} d{char.resources.hit_dice.die_size}")
```

## Long Rests

Long rests fully restore the character.

```python
result = char.long_rest()

print(f"HP recovered: {result.hp_recovered}")
print(f"Hit dice recovered: {result.hit_dice_recovered}")
print(f"Exhaustion removed: {result.exhaustion_removed}")
print(f"Resources recovered: {result.resources_recovered}")
```

### Long Rest Recovery

- **HP**: Recover all HP
- **Hit Dice**: Recover half of total (rounded down, minimum 1)
- **Resources**: All feature uses reset (Second Wind, Action Surge, Rage, Focus Points)
- **Exhaustion**: Remove 1 level
- **Short Rest Counter**: Reset to 0

### Session End Flag

Long rests set `ends_session=True` to indicate the D&D session typically ends:

```python
if result.ends_session:
    print("Long rest complete - good stopping point!")
```

## Resource Tracking

### Class Feature Resources

Resources are automatically registered when characters are created:

```python
# Fighter (level 2+)
char.resources.has_feature_available("Second Wind")  # True
char.resources.has_feature_available("Action Surge")  # True

# Barbarian
char.resources.has_feature_available("Rage")  # True

# Monk (level 2+)
char.resources.has_feature_available("Focus Points")  # True
```

### Manual Resource Management

```python
# Check resource status
resource = char.resources.get_feature("Rage")
print(f"Rage: {resource.current}/{resource.maximum}")

# Use resource manually
if char.resources.use_feature("Rage"):
    print("Rage activated!")
else:
    print("No Rage uses remaining")

# Check availability
if char.resources.has_feature_available("Second Wind"):
    print("Second Wind ready")
```

### Recovery Types

Resources recover on either short or long rests:

| Resource | Class | Recover On |
|----------|-------|------------|
| Second Wind | Fighter | Short Rest |
| Action Surge | Fighter | Short Rest |
| Rage | Barbarian | Long Rest |
| Focus Points | Monk | Short Rest |
| Wholeness of Body | Open Hand Monk | Long Rest |

## Exhaustion Recovery

Long rests remove 1 level of exhaustion:

```python
char.exhaustion.level = 3
char.long_rest()
print(char.exhaustion.level)  # 2
```

## Example: Combat Day

```python
# Morning - full resources
fighter = create_character(
    name="Fighter",
    species_name=SpeciesName.HUMAN,
    class_name=ClassName.FIGHTER,
    level=5,
)

# Combat 1
fighter.take_damage(20)
fighter.use_second_wind()  # Heal
fighter.use_action_surge()  # Extra action

# Short rest 1
fighter.short_rest(hit_dice_to_spend=2)
# Second Wind and Action Surge recovered

# Combat 2
fighter.take_damage(15)
fighter.use_second_wind()  # Available again

# Short rest 2
fighter.short_rest(hit_dice_to_spend=1)

# Combat 3
# Can't take another short rest until long rest
print(fighter.can_short_rest())  # False

# Long rest
fighter.long_rest()
# All HP, resources, and short rest counter reset
# Half hit dice recovered
# 1 exhaustion removed (if any)
```

## Rest Result Details

Both rest methods return a `RestResult`:

```python
class RestResult:
    rest_type: RestType       # SHORT or LONG
    success: bool             # True if rest completed
    error: str | None         # Error message if failed
    hp_recovered: int         # HP healed
    hit_dice_spent: int       # Hit dice used (short rest)
    hit_dice_recovered: int   # Hit dice regained (long rest)
    exhaustion_removed: int   # Exhaustion levels removed
    resources_recovered: dict # {resource_name: amount_recovered}
    ends_session: bool        # True for long rests
```
