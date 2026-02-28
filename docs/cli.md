# CLI: Running a Game Session

## Installation

```bash
pip install -e ".[dev]"
```

The `dndbot` entry point is registered automatically.

## Starting a Session

```bash
dndbot <character.yaml> [--provider ollama|anthropic] [--model <name>]
```

**Examples:**

```bash
# Local Ollama (default)
dndbot characters/thorin.yaml

# Anthropic Claude
dndbot characters/thorin.yaml --provider anthropic --model claude-haiku-4-5-20251001

# Different local model
dndbot characters/thorin.yaml --model mistral:7b
```

Requires [Ollama](https://ollama.com) running locally for the default provider, or `ANTHROPIC_API_KEY` set for Anthropic.

## DM Input

Type scene descriptions freely. The DM parser (a lightweight LLM call) extracts mechanical commands embedded in natural language:

```
DM> You enter a damp cave. A goblin lunges at you, dealing 7 damage!
  → Took 7 damage. HP: 21/28

DM> The antidote takes effect — you are no longer poisoned.
  → Condition removed: poisoned

DM> Roll for initiative, combat begins!
  → Mode: combat
```

## Slash Commands

Slash commands bypass the LLM parser for direct game state control:

| Command | Effect |
|---------|--------|
| `/status` | Print the character card (HP, class, level) |
| `/damage <N>` | Apply N damage directly |
| `/heal <N>` | Heal N HP directly |
| `/uncondition <name>` | Remove a condition (e.g. `/uncondition poisoned`) |
| `/quit` | End the session |

**Valid condition names:** `blinded`, `charmed`, `deafened`, `frightened`, `grappled`, `incapacitated`, `invisible`, `paralyzed`, `petrified`, `poisoned`, `prone`, `restrained`, `stunned`, `unconscious`

## Session Flow

Each turn:

1. **DM types** a scene description or slash command
2. **Parser** extracts narrative + mechanical commands (damage, heal, mode change, conditions)
3. **Commands** are applied to character state
4. **Agent** receives the narrative and responds using tools (attack, skill checks, etc.)
5. **Response** is printed to the terminal

## Programmatic Use

```python
from dnd_bot.agents import PlayerAgent
from dnd_bot.character.storage import load_character
from dnd_bot.cli.game import GameSession

character = load_character("characters/thorin.yaml")
agent = PlayerAgent(character=character, provider="ollama")
session = GameSession(agent=agent)
session.run()
```
