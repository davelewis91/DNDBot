# DNDBot

> Run D&D sessions from your terminal, powered by LLMs.

A D&D 5e character simulation library and LangGraph multi-agent framework. A party of
AI-controlled characters responds to DM narration using proper D&D 2024 mechanics — attack rolls,
skill checks, conditions, class features, and more. A party manager LLM routes between characters
and yields back to the DM when appropriate.

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
# Run a two-character party (requires Ollama)
dndbot characters/vorn_ashgrip.yaml characters/yue_windsong.yaml

# Use Anthropic Claude instead
dndbot characters/vorn_ashgrip.yaml characters/yue_windsong.yaml \
  --provider anthropic --model claude-haiku-4-5-20251001
```

Example session:

```
DM> You enter a dimly lit tavern. A hooded figure watches from the corner.

  Vorn narrows his eyes and surveys the room, hand resting on his axe. He notes the exits
  before approaching the bar. [Perception: 14]

  Yue moves quietly to a corner table, keeping an eye on the hooded figure. [Stealth: 16]

DM> /damage vorn 8
  → Vorn took 8 damage. HP: 20/28

DM> The orc charges, swinging a greataxe at Vorn!
  → Mode: combat
```

### Slash Commands

| Command | Effect |
|---------|--------|
| `/status` | Print the character card for every party member (HP, AC, conditions) |
| `/damage <name> <N>` | Apply N damage to the named character |
| `/heal <name> <N>` | Heal the named character by N HP |
| `/condition <name> <cond>` | Apply a condition to the named character |
| `/uncondition <name> <cond>` | Remove a condition from the named character |
| `/rest short` | Take a short rest (all party members) |
| `/rest long` | Take a long rest — resets all HP and resources (all party members) |
| `/mode combat` | Force switch to combat mode |
| `/mode exploration` | Force switch to exploration mode |
| `/roll <dice>` | Roll dice as the DM (e.g. `/roll 2d6`, `/roll 1d20`) |
| `/initiative add <name> <roll>` | Add a character to the initiative order |
| `/initiative remove <name>` | Remove a character from the initiative order |
| `/initiative next` | Advance to the next character's turn |
| `/initiative show` | Display the current initiative order |
| `/quit` | End the session |

The slash commands are not always needed — the DM parser should pick up relevant phrases
(e.g. "he hits Vorn for 8 damage") and apply the correct mechanical effect automatically.
These commands are mostly useful as a fallback and for direct state control.

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

### Running a session

```python
from dnd_bot.character.storage import load_character
from dnd_bot.cli.game import GameSession

party = [
    load_character("characters/vorn_ashgrip.yaml"),
    load_character("characters/yue_windsong.yaml"),
]
session = GameSession(party=party, provider="ollama")
session.run()
```

## Project Status

**v0.2.2** The multi-agent update.

* Full LangGraph multi-agent architecture: each party member is a separate `player_node`,
  coordinated by a `party_manager_node` using structured output routing
* Party subgraph loops until the party manager yields to the DM or the circuit breaker
  (5 consecutive agent turns) is triggered
* Mode-based tool filtering: combat tools hidden during exploration, exploration tools hidden
  during combat — reduces token usage and prevents incorrect tool offers
* Session history automatically summarised at 40 messages to prevent unbounded context growth
* Initiative tracking via `/initiative` slash commands
* Per-character targeting for `/damage`, `/heal`, `/condition`, `/uncondition`

**v0.2.0** The Skills & Features update — class features as LLM tools, skills guidance, automatic
initiative rolling, session history summarisation.

**v0.1.0 alpha.** The core character library and CLI game runner.

Planned features:

- Spell system and spellcasting classes (Wizard, Cleric, etc.)
- Additional martial classes (Paladin, Ranger)
- DM agent

## Documentation

Full documentation is in [`docs/`](docs/):

- [Character System](docs/README.md) — architecture overview, quick start
- [Character Creation](docs/character_creation.md) — creating and customising characters
- [Combat](docs/combat.md) — attack rolls, damage, death saves, conditions
- [Rests](docs/rests.md) — short and long rest mechanics
- [Items](docs/items.md) — weapons, armor, equipment
- [CLI Usage](docs/cli.md) — running sessions, DM input, slash commands
- [Agent System](docs/agents.md) — multi-agent graph, available tools
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
