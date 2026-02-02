# D&D Character Stats System - Implementation Plan

## Status: Complete

Last updated: 2026-02-02

---

## Completed Tasks

### 1. Exhaustion System ✅
- File: `src/dnd_bot/character/exhaustion.py`
- D&D 2024 rules: levels 0-10, -1 penalty per level, death at 10
- Integrated into Character with penalty applied to all d20 tests

### 2. Conditions System ✅
- File: `src/dnd_bot/character/conditions.py`
- All 14 standard conditions (blinded, charmed, etc.)
- ActiveCondition with source and duration tracking
- ConditionManager with advantage/disadvantage helpers

### 3. Resource Tracking Foundation ✅
- File: `src/dnd_bot/character/resources.py`
- HitDice for short rest healing
- Resource for class features (Second Wind, Rage, etc.)
- ResourcePool managing all character resources

### 4. Rest System ✅
- Methods in `src/dnd_bot/character/character.py`
- Short rest: spend hit dice, recover short-rest resources, max 2 per long rest
- Long rest: recover all HP, half hit dice, all resources, remove 1 exhaustion

### 5. Death Saving Throws ✅
- Methods in `src/dnd_bot/character/character.py`
- `make_death_save()` - rolls d20, handles nat 1/20, tracks successes/failures
- `heal()` resets death saves when going from 0 HP to positive
- Damage at 0 HP adds failures (2 for critical hits)

### 6. Items System ✅
- New module: `src/dnd_bot/items/`
- Base classes: Item, Weapon, Armor, Shield, Consumable, Ammunition
- 21 weapons, 12 armors, potions, ammunition defined
- AC calculation from equipped armor (light/medium/heavy rules)
- Unarmored Defense for Barbarian (DEX+CON) and Monk (DEX+WIS)

### 7. Class Features with Mechanics ✅
- Modified: `src/dnd_bot/character/classes.py`
- Added `FeatureMechanic` and `FeatureMechanicType` models
- All class features now have mechanical data (PASSIVE, RESOURCE, TOGGLE, REACTION)
- Helper functions: `get_sneak_attack_dice()`, `get_rage_uses()`, `get_martial_arts_die()`
- Auto-registers class feature resources when character is created
- Helper methods: `use_second_wind()`, `use_action_surge()`, `start_rage()`, `use_focus_points()`
- 50 tests added in `tests/test_class_features.py`

### 8. Subclasses ✅
- New file: `src/dnd_bot/character/subclasses.py`
- Four martial subclasses implemented:
  - **Champion** (Fighter): Improved Critical, Remarkable Athlete, Superior Critical, Survivor
  - **Thief** (Rogue): Fast Hands, Second-Story Work, Supreme Sneak, Use Magic Device
  - **Berserker** (Barbarian): Frenzy, Mindless Rage, Intimidating Presence, Retaliation
  - **Way of the Open Hand** (Monk): Open Hand Technique, Wholeness of Body, Tranquility, Quivering Palm
- Character integration: `subclass` field, `set_subclass()`, `get_all_features()`, `has_feature()`, `get_critical_range()`
- Subclass resources auto-registered (e.g., Wholeness of Body)
- YAML storage support for subclass persistence
- 30 tests added in `tests/test_subclasses.py`

### 9. Documentation ✅
- Created `docs/` folder with comprehensive documentation:
  - `README.md` - Overview, quick start, architecture
  - `character_creation.md` - Creating and customizing characters
  - `combat.md` - Attack rolls, damage, death saves, conditions
  - `rests.md` - Short and long rest mechanics
  - `items.md` - Weapons, armor, equipment
  - `extending.md` - Adding custom content

---

## Implementation Complete

All tasks finished:
1. ~~**Class Features with Mechanics**~~ ✅
2. ~~**Subclasses**~~ ✅
3. ~~**Documentation**~~ ✅

---

## Testing Strategy

For each task:
1. Write unit tests first (TDD when possible)
2. Run `pytest` - all tests must pass
3. Run `ruff check .` - no lint errors
4. Test YAML round-trip for new Character fields
5. Integration test with existing features

---

## Notes

- All code follows D&D 5e 2024 rules
- Python 3.13+ required
- Use Pydantic models for all data structures
- Prefer code-defined registries over YAML for core content
- YAML can be used for user-extensible content (custom items, subclasses)
