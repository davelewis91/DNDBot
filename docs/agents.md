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

# Switch game mode (affects system prompt guidance)
agent.set_mode("combat")       # tactical, use class features
agent.set_mode("exploration")  # curious, use perception/investigation
agent.set_mode("roleplay")     # social, use background/personality
```

## Available Tools

Tools are built by `build_tools(ToolContext(character=char))` and bound to the LLM. The LLM can call any of these during a turn:

| Tool | Description |
|------|-------------|
| `check_status` | Current HP and active conditions |
| `check_inventory` | Equipped weapons and items |
| `skill_check` | Proficiency-aware skill roll (e.g. `perception`, `athletics`) |
| `ability_check` | Raw ability check (e.g. `strength`, `dexterity`) |
| `attack` | Attack roll + damage against a named target |
| `make_saving_throw` | Saving throw for a given ability |
| `speak` | Say something in character |
| `describe_action` | Narrate a non-mechanical action |

### Attack tool

The `attack` tool resolves weapon selection and ability automatically:

```
attack(target="goblin", weapon="longsword")         # armed, STR by default
attack(target="goblin", weapon="rapier")             # finesse → best of STR/DEX
attack(target="goblin", weapon="longsword", two_handed=True)  # versatile grip
attack(target="goblin")                              # unarmed strike
```

Monks automatically use their Martial Arts die and best of STR/DEX for unarmed strikes.

## Prompt System

`build_character_context(character, mode)` produces the character sheet injected into the system prompt — name, class, HP, ability modifiers, proficient skills, equipment, and background.

`PLAYER_SYSTEM_PROMPT` is a format string with `{character_context}` and `{mode_guidance}` placeholders.

`MODE_GUIDANCE` is a dict mapping mode names to brief tactical guidance strings.
