# CLI: Running a Game Session

## Installation

```bash
pip install -e ".[dev]"
```

The `dndbot` entry point is registered automatically.

## Starting a Session

```bash
dndbot <character.yaml> [<character.yaml> ...] [--provider ollama|anthropic] [--model <name>]
```

Pass one YAML file per player character. All characters are loaded into the party and controlled
by separate AI agents.

**Examples:**

```bash
# Two-character party with local Ollama (default)
dndbot characters/vorn_ashgrip.yaml characters/yue_windsong.yaml

# Anthropic Claude
dndbot characters/vorn_ashgrip.yaml characters/yue_windsong.yaml \
  --provider anthropic --model claude-haiku-4-5-20251001

# Single character, different local model
dndbot characters/vorn_ashgrip.yaml --model mistral:7b
```

Requires [Ollama](https://ollama.com) running locally for the default provider, or
`ANTHROPIC_API_KEY` set for Anthropic.

## DM Input

Type scene descriptions freely. The DM parser (a lightweight LLM call) extracts mechanical
commands embedded in natural language, including target character names when mentioned:

```
DM> The goblin slashes at Vorn for 7 damage!
  → Vorn took 7 damage. HP: 21/28

DM> The antidote takes effect — Yue is no longer poisoned.
  → Yue: condition poisoned removed

DM> Roll for initiative, combat begins!
  → Mode: combat
```

When a target name is extracted, commands apply only to that character. If no target is
mentioned, commands apply to the whole party.

## Slash Commands

Slash commands bypass the LLM parser for direct game state control.

### Character commands

Per-character commands require a `<name>` argument (case-insensitive). The name can be the full
character name (e.g. `vorn ashgrip`) or an unambiguous prefix (e.g. `vorn`). If a partial name
matches multiple characters, an error is shown.

| Command | Effect |
|---------|--------|
| `/status` | Print the character card for every party member (HP, AC, prof bonus, conditions) |
| `/damage <name> <n>` | Apply N damage to the named character |
| `/heal <name> <n>` | Heal the named character by N HP |
| `/condition <name> <cond>` | Apply a condition to the named character |
| `/uncondition <name> <cond>` | Remove a condition from the named character |

**Examples:**

```
/damage vorn 5               # matches "Vorn Ashgrip"
/damage vorn ashgrip 5       # full name also works
/heal yue 10                 # matches "Yue Windsong"
/condition yue windsong poisoned
```

**Valid condition names:** `blinded`, `charmed`, `deafened`, `frightened`, `grappled`,
`incapacitated`, `invisible`, `paralyzed`, `petrified`, `poisoned`, `prone`, `restrained`,
`stunned`, `unconscious`

### Rest and mode commands

| Command | Effect |
|---------|--------|
| `/rest short` | Take a short rest (all party members) |
| `/rest long` | Take a long rest — resets all HP and resources (all party members) |
| `/mode combat` | Force switch to combat mode |
| `/mode exploration` | Force switch to exploration mode |

### Initiative commands

Initiative is tracked separately from the agent system. Use these commands to manage turn order
in combat.

| Command | Effect |
|---------|--------|
| `/initiative add <name> <roll>` | Add a character to the initiative order at the given roll value |
| `/initiative remove <name>` | Remove a character from the initiative order |
| `/initiative next` | Advance to the next character's turn |
| `/initiative show` | Display the current initiative order (current turn marked with →) |

### Utility commands

| Command | Effect |
|---------|--------|
| `/roll <dice>` | Roll dice as the DM (e.g. `/roll 2d6`, `/roll 1d20`) |
| `/quit` | End the session |

## Session Flow

Each turn:

1. **DM types** a scene description or slash command.
2. **Parser** extracts narrative + mechanical commands (damage, heal, mode change, conditions).
3. **Commands** are applied to party state.
4. **Party graph** is invoked: the `party_manager` routes to each character in turn, with each
   `player_node` responding using tools (attack, skill checks, etc.).
5. **Responses** are printed to the terminal as each character acts.
6. **Party manager** yields back to the DM when appropriate or after the circuit breaker limit
   (5 consecutive agent turns) is reached.

## Programmatic Use

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

## DM Parser API

The DM parser converts free-text DM narration into structured game commands using an LLM call.
It requires the same Ollama or Anthropic provider as the agents.

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
| `type` | `str` | Command type: `"damage"`, `"heal"`, `"mode"`, `"condition"`, or `"remove_condition"` |
| `value` | `int \| str \| None` | Integer for damage/heal, string for mode/condition/rest, or `None` |
| `target` | `str \| None` | Character name(s) targeted, or `None` for whole party |

**`type` values:**

| Value | `value` type | When emitted |
|-------|-------------|--------------|
| `"damage"` | `int` | Player takes N damage |
| `"heal"` | `int` | Player regains N HP |
| `"mode"` | `"combat"` or `"exploration"` | Combat begins or ends |
| `"condition"` | `str` condition name | A condition is applied |
| `"remove_condition"` | `str` condition name | A condition ends |

The `target` field is extracted automatically from the DM narration when character names are
mentioned. Comma-separated names (e.g. `"Vorn, Yue"`) target multiple characters. Commands
without a target apply to the whole party.
