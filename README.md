# DNDBot

> Run D&D sessions from your terminal, powered by LLMs.

A D&D 5e character simulation library and LangGraph agent framework. An AI-controlled player
character responds to DM narration using proper D&D 2024 mechanics — attack rolls, skill checks,
conditions, class features, and more.

## Key Features

- **4 character classes** with subclasses, levels 1–20: Fighter (Champion), Barbarian (Berserker),
  Rogue (Thief), Monk (Open Hand)
- **Full combat mechanics**: attack rolls, damage, death saves, 14 conditions, exhaustion
  (D&D 2024 rules)
- **Equipment**: 21 weapons, 12 armor types, shields, potions
- **LLM providers**: Ollama (local, free) or Anthropic (Claude)
- **CLI game runner**: DM input parsing, automatic mode switching (exploration/combat/roleplay),
  slash commands
- **YAML character storage**: human-readable save files, `create_character()` factory for new
  characters

## Prerequisites

- Python 3.13+
- [Ollama](https://ollama.com) running locally (default) **or** `ANTHROPIC_API_KEY` set in your
  environment
  - Note: Ollama models must support tool usage in LangGraph, which not all of them do (and my PC can't run the ones that do :( )

## Installation

```bash
pip install -e .
# or for development
pip install -e ".[dev]"
```

## Quick Start (CLI)

```bash
# Run a session with the included example character (requires Ollama)
dndbot characters/durgin_ironbeard.yaml

# Use Anthropic Claude instead
dndbot characters/durgin_ironbeard.yaml --provider anthropic --model claude-haiku-4-5-20251001
```

Example session:

```
DM> You enter a dimly lit tavern. A hooded figure watches from the corner.

  Durgin narrows his eyes and surveys the room, hand resting on his axe. He mutters a
  prayer to Moradin and notes the exits before approaching the bar. [Perception: 14]

DM> /damage 8
  → Took 8 damage. HP: 20/28

DM> The orc charges, swinging a greataxe at you!
  → Mode: combat

  Durgin bellows a war cry and activates Second Wind, then readies his axe for a
  counterattack. "Come on then, greenskin!" [Attack roll: 18 vs AC]
```

### Slash Commands

| Command | Effect |
|---------|--------|
| `/status` | Print character card (HP, class, level) |
| `/damage <N>` | Apply N damage directly |
| `/heal <N>` | Heal N HP directly |
| `/uncondition <name>` | Remove a condition (e.g. `/uncondition poisoned`) |
| `/quit` | End the session |

The slash commands are not always needed - the DM Intent Parser should pick up use of relevant phrases (e.g. "he hits you for 8 damage") and call the correct tool. These commands are mostly useful as a fallback in case of failure (and for ending the session).

## Python API

### Creating a character

```python
from dnd_bot.character import create_character, AbilityScores, SpeciesName

fighter = create_character(
    name="Durgin Ironbeard",
    class_type="champion",
    species_name=SpeciesName.DWARF,
    level=5,
    ability_scores=AbilityScores(strength=17, constitution=16),
)
print(f"HP: {fighter.current_hp}/{fighter.max_hp}")
print(f"AC: {fighter.armor_class}")
```

### Running an agent

```python
from dnd_bot.agents import PlayerAgent
from dnd_bot.character import load_character

character = load_character("characters/durgin_ironbeard.yaml")
agent = PlayerAgent(character=character, provider="ollama")

result = agent.process_turn("You enter a damp cave. A goblin lunges at you!")
print(result.narrative)
```

## Project Status

**v0.1.0 alpha.** The core character library and CLI game runner are functional. Planned features:

- Spell system and spellcasting classes (Wizard, Cleric, etc.)
- Additional martial classes (Paladin, Ranger)
- Multi-character sessions and a DM agent

## Documentation

Full documentation is in [`docs/`](docs/):

- [Character System](docs/README.md) — architecture overview, quick start
- [Character Creation](docs/character_creation.md) — creating and customising characters
- [Combat](docs/combat.md) — attack rolls, damage, death saves, conditions
- [Rests](docs/rests.md) — short and long rest mechanics
- [Items](docs/items.md) — weapons, armor, equipment
- [CLI Usage](docs/cli.md) — running sessions, DM input, slash commands
- [Agent System](docs/agents.md) — PlayerAgent API, available tools
- [Extending](docs/extending.md) — adding custom content

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Fix lint issues automatically
ruff check --fix .
```

## License

MIT
D&D Ruleset taken from 2024 SRD
