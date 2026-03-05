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

## DM Parser API

The DM parser converts free-text DM narration into structured game commands using an LLM call.
It requires the same Ollama or Anthropic provider as `PlayerAgent`.

### `parse_dm_input`

```python
from dnd_bot.cli.dm_parser import parse_dm_input

intent = parse_dm_input(text, provider="ollama", model="llama3:8b")
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `text` | `str` | Raw DM narration to parse |
| `provider` | `str` | `"ollama"` (default) or `"anthropic"` |
| `model` | `str` | Model name, e.g. `"llama3:8b"` |

Returns a `DMIntent`.

### `DMIntent`

| Field | Type | Description |
|-------|------|-------------|
| `narrative` | `str` | Dramatic text to show the player (extracted from DM input) |
| `commands` | `list[DMCommand]` | Zero or more mechanical commands extracted from the text |

### `DMCommand`

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Command type: `"damage"`, `"heal"`, `"mode"`, `"condition"`, `"remove_condition"`, or `"rest"` |
| `value` | `int \| str \| None` | Integer for damage/heal, string for mode/condition/rest, or `None` |

**`type` values:**

| Value | `value` type | When emitted |
|-------|-------------|--------------|
| `"damage"` | `int` | Player takes N damage |
| `"heal"` | `int` | Player regains N HP |
| `"mode"` | `"combat"` or `"exploration"` | Combat begins or ends |
| `"condition"` | `str` condition name | A condition is applied |
| `"remove_condition"` | `str` condition name | A condition ends |
| `"rest"` | `"short"` or `"long"` | A rest occurs |

### `apply_commands`

Applies a list of `DMCommand` objects to game state. Lives in `dnd_bot.cli.game`.

```python
from dnd_bot.cli.game import apply_commands

apply_commands(commands, character, agent=None)
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `commands` | `list[DMCommand]` | Commands returned by `parse_dm_input` |
| `character` | `AnyCharacter` | Character to modify (HP, conditions, etc.) |
| `agent` | `PlayerAgent \| None` | Agent to update mode on (optional) |

### Example

```python
from dnd_bot.cli.dm_parser import parse_dm_input
from dnd_bot.cli.game import apply_commands
from dnd_bot.character.storage import load_character
from dnd_bot.agents import PlayerAgent

character = load_character("characters/thorin.yaml")
agent = PlayerAgent(character=character, provider="ollama")

intent = parse_dm_input(
    "The goblin strikes! You take 8 piercing damage. Roll for initiative!",
    provider="ollama",
)
print(intent.narrative)        # "The goblin strikes!"
apply_commands(intent.commands, character, agent=agent)
# → Applies 8 damage to character HP
# → Switches agent to combat mode
```
