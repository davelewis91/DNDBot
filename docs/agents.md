# Agent System

The agent system wraps a D&D character in a LangChain tool-calling loop, producing a player agent that can perceive DM narration and respond with in-character actions.

## Architecture

```
PlayerAgent
├── LLM (Ollama or Anthropic)  ← bound to tools via bind_tools()
├── ToolContext → build_tools() ← character mechanics exposed as LangChain tools
└── conversation history        ← full message history passed each turn
```

`PlayerAgent.process_turn(dm_input)` drives a single round-trip:

1. Builds a system prompt from the character's current state and game mode
2. Invokes the LLM with system prompt + history + DM message
3. Executes any tool calls (attack, skill check, etc.) against the real character
4. Returns the agent's narrative response plus tool results as a single string

## LLM Providers

Two providers are supported via `get_llm()`:

| Provider | Default model | Notes |
|----------|--------------|-------|
| `ollama` | `llama3:8b` | Local, free, requires Ollama running |
| `anthropic` | (any Claude model) | Cloud, requires `ANTHROPIC_API_KEY` |

```python
from dnd_bot.agents import get_llm

llm = get_llm(provider="ollama", model="llama3:8b")
llm = get_llm(provider="anthropic", model="claude-haiku-4-5-20251001")
```

## PlayerAgent API

```python
from dnd_bot.agents import PlayerAgent
from dnd_bot.character.storage import load_character

character = load_character("characters/thorin.yaml")
agent = PlayerAgent(character=character, provider="ollama", model="llama3:8b")

# Process a DM turn
response = agent.process_turn("You enter a dimly lit tavern.")
print(response)

# Switch game mode — also rebinds the LLM to the mode-appropriate tool set
agent.set_mode("combat")       # tactical, use class features
agent.set_mode("exploration")  # explore, converse with NPCs, use social and investigation skills
```

## Mode-Based Tool Filtering

The LLM is only given the tools relevant to the current mode. This halves tool-description token
usage (~350 tokens instead of ~700) and prevents semantically incorrect offers (e.g. `attack`
during exploration).

| Tool | Exploration | Combat |
|------|-------------|--------|
| `check_status` | yes | yes |
| `skill_check` | yes | yes |
| `speak` | yes | yes |
| `change_mode` | yes | yes |
| `check_inventory` | yes | no |
| `ability_check` | yes | no |
| `describe_action` | yes | no |
| `attack` | no | yes |
| `make_saving_throw` | no | yes |
| class ability tools | no | yes |

The mode constants `EXPLORATION_TOOLS` and `COMBAT_TOOLS` (sets of tool names) are exported from
`dnd_bot.agents.tools`. Class ability tools are always combat-only.

`set_mode(mode)` updates `self.mode`, filters `self.tools`, and rebinds `self._llm` automatically.

## Available Tools

Tools are built by `build_tools(ToolContext(character=char))` and bound to the LLM. The LLM can
call any of these during a turn (subject to mode filtering above):

| Tool | Description |
|------|-------------|
| `check_status` | Current HP, active conditions, and available resources |
| `check_inventory` | Equipped weapons and items |
| `skill_check` | Proficiency-aware skill roll (e.g. `perception`, `athletics`) |
| `ability_check` | Raw ability check (e.g. `strength`, `dexterity`) |
| `attack` | Attack roll + damage against a named target |
| `make_saving_throw` | Saving throw for a given ability |
| `speak` | Say something in character |
| `describe_action` | Narrate a non-mechanical action |
| `change_mode` | Switch game mode; switching to combat automatically rolls initiative and returns the result |

### Class Ability Tools

Additional tools are registered automatically based on the character's class:

| Class | Tool | Description |
|-------|------|-------------|
| Fighter | `second_wind` | Heal 1d10 + level HP (1/short rest) |
| Fighter | `action_surge` | Gain one additional action (1/short rest) |
| Barbarian | `toggle_rage` | Start or end Rage (uses/long rest) |
| Monk | `flurry_of_blows` | Spend 1 Focus Point for 2 unarmed strikes |
| Monk | `patient_defense` | Spend 1 Focus Point for Disengage + Dodge |
| Monk | `step_of_the_wind` | Spend 1 Focus Point for Dash + Disengage with doubled jump |
| Monk | `stunning_strike` | Spend 1 Focus Point to attempt a Stunning Strike |
| Monk (OpenHand) | `wholeness_of_body` | Heal with Martial Arts die + WIS mod (1/long rest) |
| Rogue | `cunning_action` | Dash, Disengage, or Hide as a Bonus Action |

### Attack tool

The `attack` tool resolves weapon selection and ability automatically:

```
attack(target="goblin", weapon="longsword")         # armed, STR by default
attack(target="goblin", weapon="rapier")             # finesse → best of STR/DEX
attack(target="goblin", weapon="longsword", two_handed=True)  # versatile grip
attack(target="goblin")                              # unarmed strike
```

Monks automatically use their Martial Arts die and best of STR/DEX for unarmed strikes.

## History Summarisation

`PlayerAgent` tracks a `_turn_count` (incremented each `process_turn` call). Every 15 turns it
calls `_summarise_history()` to prevent the conversation history from growing without bound.

### How it works

1. The last 3 turns (identified by the 3 most recent `HumanMessage` boundaries) are kept verbatim.
2. All older messages are passed to `self._base_llm` (the unbound LLM) with `SUMMARISATION_PROMPT`,
   which requests a ≤150-word narrative log covering key events, resources spent, HP changes,
   conditions, and NPC interactions.
3. If a previous summary exists it is prepended as context so successive summaries are cumulative.
4. `_history` is replaced with `[HumanMessage("Session so far: {summary}")]` + the last 3 turns.
5. The raw summary string is stored in `self._summary`.

This keeps context windows bounded regardless of session length while preserving full fidelity for
the most recent 3 turns.

## Prompt System

`build_character_context(character, mode)` produces the character sheet injected into the system prompt — name, class, HP, ability modifiers, proficient skills, equipment, background, and class abilities with resource use counts.

`PLAYER_SYSTEM_PROMPT` is a format string with `{character_context}` and `{mode_guidance}` placeholders.

`SUMMARISATION_PROMPT` instructs the LLM to produce a concise narrative log (≤150 words) of older
session history for compaction purposes.

`MODE_GUIDANCE` maps the two mode names (`"exploration"`, `"combat"`) to guidance strings injected into the system prompt. Exploration covers both investigation and NPC conversation; there is no separate roleplay mode.
