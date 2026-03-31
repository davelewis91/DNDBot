# Agent System

The agent system uses a LangGraph multi-agent architecture. A party of AI-controlled characters
responds to DM narration using proper D&D 2024 mechanics — attack rolls, skill checks, conditions,
class features, and more. A party manager LLM routes between characters and yields back to the DM
when appropriate.

## Architecture

```
party_graph (StateGraph[GameState])
├── party_manager_node  ← routes to next speaker or yields to DM
└── player_node         ← executes one character turn, loops back to party_manager
```

All state flows through `GameState`, a `TypedDict` shared by every node.

## GameState

Defined in `src/dnd_bot/agents/state.py`.

| Field | Type | Description |
|-------|------|-------------|
| `messages` | `list[AnyMessage]` | Full conversation history (append-only via `add_messages` reducer) |
| `mode` | `"exploration" \| "combat"` | Current game mode |
| `party` | `list[AnyCharacter]` | Character instances in the party |
| `initiative_order` | `list[str]` | Character names in descending initiative order |
| `initiative_rolls` | `dict[str, int]` | Maps character name to their initiative roll value |
| `initiative_index` | `int` | Index into `initiative_order` for the current turn |
| `next_speaker` | `str \| None` | Set by `party_manager`; `None` signals yield-to-DM |
| `consecutive_agent_turns` | `int` | Agent turns since the last DM input (circuit breaker) |

## player_node

Defined in `src/dnd_bot/agents/player_node.py`.

`make_player_node(model, provider)` is a factory that returns a stateless LangGraph node
function. The node:

1. Looks up the character named in `state["next_speaker"]` from the party list.
2. Builds the full tool set via `build_tools(ToolContext(character=...))` and appends a
   `change_mode` closure that captures the character and records any mode transitions.
3. Filters tools to those appropriate for the current mode (see **Mode-Based Tool Filtering**
   below).
4. Binds the mode-filtered tools to the base LLM (created once per factory call) and invokes
   with system prompt + full history.
5. Parses a `[Importance: X]` self-report from the LLM response, stores the value in
   `response.additional_kwargs["importance"]` (float, 0–10), and strips the tag from the
   message content so it doesn't leak into display or accumulate in history. The character
   name is stored in `additional_kwargs["character_name"]`.
6. Executes any tool calls and appends `ToolMessage` results.
7. Returns updated `messages`, `mode` (if changed), and an incremented
   `consecutive_agent_turns`.

## party_manager_node

Defined in `src/dnd_bot/agents/party_manager.py`.

`make_party_manager_node(model, provider, max_turns)` is a factory returning a LangGraph node
that uses **structured output** to produce a `PartyManagerDecision`.

### PartyManagerDecision

| Field | Type | Description |
|-------|------|-------------|
| `next_speaker` | `str \| None` | Name of the character who should act next, or `None` |
| `yield_to_dm` | `bool` | If `True`, return control to the DM |
| `reasoning` | `str` | One-sentence explanation of the routing decision |

The node builds a system prompt containing:

- Party roster (name, class, HP, conditions)
- Current mode and initiative order (combat only)
- `consecutive_agent_turns` / `max_turns` (circuit breaker progress)
- Importance score from the most recent `AIMessage.additional_kwargs["importance"]`

A hard check at the top of the node short-circuits the LLM call entirely when
`consecutive_agent_turns >= max_turns`, returning `next_speaker=None` and resetting the counter
to 0. This guarantees the circuit breaker fires even if the LLM ignores the prompt instruction,
and saves an LLM call.

To reduce token usage, the party manager only receives the last 3 messages (not the full
history) — it only needs recent context for routing decisions.

If the hard check does not fire, the node calls the LLM. If `yield_to_dm` is `True` or
`next_speaker` is `None`, the node sets `next_speaker=None` and resets
`consecutive_agent_turns` to 0. Otherwise it sets `next_speaker` to the chosen character name.

## Party Subgraph

Defined in `src/dnd_bot/agents/party_graph.py`. Built with `build_party_graph(model, provider,
max_consecutive_turns)`.

```
party_manager ──(next_speaker set)──► player_node ──► party_manager
     │
     └──(next_speaker=None)──► END
```

The loop continues until `party_manager` yields to the DM. The circuit breaker enforces a hard
ceiling of `max_consecutive_turns` (default 5) agent turns per DM input — once reached, the
party manager is forced to yield regardless of narrative context.

## Importance Score

Each `player_node` response embeds a self-reported importance score as
`[Importance: X]` in the message content. The node extracts this value, stores it in
`AIMessage.additional_kwargs["importance"]` (float, 0–10), and strips the tag from the message
content so it doesn't leak into terminal output or accumulate in history.

`party_manager` reads this score from the most recent `AIMessage` and uses it when deciding
whether to let another agent act or yield. A score ≥ 7 favours continued agent turns; a score
≤ 3 favours yielding to the DM.

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

## Mode-Based Tool Filtering

`player_node` only gives the LLM tools relevant to the current mode. This reduces token usage
and prevents semantically incorrect offers (e.g. `attack` during exploration).

| Tool | Exploration | Combat |
|------|-------------|--------|
| `check_status` | yes | yes |
| `skill_check` | yes | yes |
| `speak` | yes | yes |
| `change_mode` | yes | yes |
| `check_inventory` | yes | no |
| `ability_check` | yes | yes |
| `describe_action` | yes | yes |
| `attack` | no | yes |
| `make_saving_throw` | no | yes |
| class ability tools | no | yes |

The mode constants `EXPLORATION_TOOLS` and `COMBAT_TOOLS` (sets of tool names) are exported from
`dnd_bot.agents.tools`. Class ability tools are always combat-only.

## Available Tools

Tools are built by `build_tools(ToolContext(character=char))`. The LLM can call any of these
during a turn (subject to mode filtering above):

| Tool | Description |
|------|-------------|
| `check_status` | Current HP, AC, active conditions, and available resources |
| `check_inventory` | Equipped weapons, items, and gold |
| `skill_check` | Proficiency-aware skill roll (e.g. `perception`, `athletics`) |
| `ability_check` | Raw ability check (e.g. `strength`, `dexterity`) |
| `attack` | Attack roll + damage against a named target |
| `make_saving_throw` | Saving throw for a given ability |
| `speak` | Say something in character |
| `describe_action` | Narrate a non-mechanical action |
| `change_mode` | Switch game mode; switching to combat automatically rolls initiative |

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

## History Summarisation

`GameSession` tracks total message count after each DM turn. When `len(messages) >= 40`, it
calls `_summarise_messages()` to prevent unbounded context growth.

### How it works

1. The most recent 6 messages are kept verbatim.
2. All older messages are passed to the LLM with `SUMMARISATION_PROMPT`, which requests a
   concise narrative log covering key events, resources spent, HP changes, conditions, and NPC
   interactions.
3. The history is replaced with `[SystemMessage("Session so far: {summary}")]` + the 6 recent
   messages.

## Prompt System

`build_character_context(character, mode)` produces the character sheet injected into the system
prompt — name, class, HP, ability modifiers, proficient skills, equipment, background, and class
abilities with resource use counts.

`PLAYER_SYSTEM_PROMPT` is a format string with a `{character_context}` placeholder. In
exploration mode `SKILLS_GUIDANCE` is appended; in all modes `_IMPORTANCE_INSTRUCTION` is
appended to request the `[Importance: X]` self-report.

`SUMMARISATION_PROMPT` instructs the LLM to produce a concise narrative log of older session
history for compaction purposes.

`MODE_GUIDANCE` maps the two mode names (`"exploration"`, `"combat"`) to guidance strings.
Exploration covers both investigation and NPC conversation; there is no separate roleplay mode.
