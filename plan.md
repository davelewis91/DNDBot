# Phase 1: Single Player Agent with Human DM

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a LangGraph-based player agent that controls one D&D character, with a human acting as Dungeon Master via CLI.

**Architecture:** A LangGraph graph with perceive→decide→act nodes drives a character agent. The CLI provides a DM interface with natural language input parsing (via lightweight LLM) and slash command shortcuts. Characters are loaded from existing YAML files.

**Tech Stack:** LangGraph, LangChain (Anthropic + Ollama providers), Rich terminal UI, Pydantic, existing dnd_bot character system.

---

## Existing Code to Reuse

- `src/dnd_bot/agents/state.py` - `GameContext`, `PlayerState` classes (already defined)
- `src/dnd_bot/character/storage.py` - `load_character()` function
- `src/dnd_bot/character/background.py` - `Background.to_prompt_context()`
- `src/dnd_bot/dice.py` - dice rolling utilities
- `pyproject.toml` - already has `langgraph>=1.0.7`

---

### ✅ Task 1: Add Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add new dependencies to pyproject.toml**

In the `[project] dependencies` list, add:
```toml
"langchain-anthropic>=0.3.0",
"langchain-ollama>=0.2.0",
"rich>=13.0.0",
```

**Step 2: Add CLI entry point**

In `[project.scripts]`:
```toml
dndbot = "dnd_bot.cli.game:main"
```

**Step 3: Install and verify**

Run: `pip install -e ".[dev]"`
Expected: No errors, packages installed

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add langchain, ollama, and rich dependencies"
```

---

### ✅ Task 2: LLM Configuration (`agents/llm.py`)

**Files:**
- Modify: `src/dnd_bot/agents/llm.py` (currently empty placeholder)
- Test: `tests/test_agent_llm.py`

**Step 1: Write the failing test**

```python
# tests/test_agent_llm.py
import pytest
from unittest.mock import patch, MagicMock
from dnd_bot.agents.llm import get_llm


def test_get_llm_ollama_returns_model():
    with patch("dnd_bot.agents.llm.ChatOllama", return_value=MagicMock()):
        result = get_llm(provider="ollama", model="llama3:8b")
    assert result is not None


def test_get_llm_anthropic_returns_model():
    with patch("dnd_bot.agents.llm.ChatAnthropic", return_value=MagicMock()):
        result = get_llm(provider="anthropic", model="claude-haiku-4-5-20251001")
    assert result is not None


def test_get_llm_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_llm(provider="unknown")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_llm.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `agents/llm.py`**

```python
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel


def get_llm(
    model: str = "llama3:8b",
    temperature: float = 0.7,
    provider: str = "ollama",
) -> BaseChatModel:
    """
    Get a configured LLM client.

    Parameters
    ----------
    model : str
        Model name (e.g. "llama3:8b" or "claude-haiku-4-5-20251001")
    temperature : float
        Sampling temperature (0.0-1.0)
    provider : str
        Either "ollama" (local, free) or "anthropic" (cloud, paid)

    Returns
    -------
    BaseChatModel
        Configured LangChain chat model
    """
    if provider == "ollama":
        return ChatOllama(model=model, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Use 'ollama' or 'anthropic'.")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_llm.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/agents/llm.py tests/test_agent_llm.py
git commit -m "feat: add LLM configuration with ollama and anthropic providers"
```

---

### ✅ Task 3: Prompt System (`agents/prompts.py`)

**Files:**
- Modify: `src/dnd_bot/agents/prompts.py` (currently empty placeholder)
- Test: `tests/test_agent_prompts.py`

**Note on `PlayerState`**: It extends `MessagesState` (a `TypedDict`), so it only supports `state["key"]` dict access, not `state.key` attribute access. `build_character_context` therefore takes `character` and `mode` as separate arguments rather than a `PlayerState` object.

**Step 1: Write failing tests**

```python
# tests/test_agent_prompts.py
from dnd_bot.agents.prompts import build_character_context, PLAYER_SYSTEM_PROMPT, MODE_GUIDANCE
from dnd_bot.character.skills import Skill
from unittest.mock import MagicMock


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = "Dwarf"
    char.current_hp = 28
    char.max_hp = 32
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS, Skill.PERCEPTION]
    char.background.to_prompt_context.return_value = "A gruff dwarven warrior."
    char.equipment = []
    return char


def test_build_character_context_contains_name():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "Thorin" in ctx


def test_build_character_context_contains_hp():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "28/32" in ctx


def test_build_character_context_contains_mode():
    ctx = build_character_context(make_mock_character(), "exploration")
    assert "exploration" in ctx.lower()


def test_player_system_prompt_is_string():
    assert isinstance(PLAYER_SYSTEM_PROMPT, str)


def test_mode_guidance_has_all_modes():
    assert "combat" in MODE_GUIDANCE
    assert "exploration" in MODE_GUIDANCE
    assert "roleplay" in MODE_GUIDANCE
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_prompts.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `agents/prompts.py`**

```python
from dnd_bot.character.abilities import Ability
from dnd_bot.character.skills import Skill

PLAYER_SYSTEM_PROMPT = """\
You are roleplaying as {character_context}

Always stay in character. Make decisions that reflect your personality, \
background, and motivations. Use your class abilities and skills appropriately.

Current mode guidance:
{mode_guidance}

Respond with your character's action. Use the available tools to execute \
mechanical actions (attacks, skill checks, etc.). Keep dialogue brief and \
in-character.
"""

MODE_GUIDANCE = {
    "exploration": (
        "You are exploring. Look for clues, interact with the environment, "
        "use perception and investigation. Be curious but cautious."
    ),
    "combat": (
        "You are in combat. Act tactically based on your class. "
        "Use class features when advantageous. Protect allies."
    ),
    "roleplay": (
        "You are in a social situation. Use your background and personality. "
        "Persuasion, deception, or insight may be useful."
    ),
}

_ABILITY_ABBREV = {
    Ability.STRENGTH: "STR", Ability.DEXTERITY: "DEX", Ability.CONSTITUTION: "CON",
    Ability.INTELLIGENCE: "INT", Ability.WISDOM: "WIS", Ability.CHARISMA: "CHA",
}


def build_character_context(character, mode: str) -> str:
    """
    Build a character context string for the system prompt.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character
    mode : str
        Current game mode ("exploration", "combat", or "roleplay")

    Returns
    -------
    str
        Formatted character context for injection into the system prompt
    """
    ability_lines = "\n".join(
        f"  {abbrev}: {character.get_ability_modifier(ability):+d}"
        for ability, abbrev in _ABILITY_ABBREV.items()
    )
    proficient_skills = character.skills.get_proficient_skills()
    skill_lines = "\n".join(
        f"  {skill.value.replace('_', ' ').title()}: {character.get_skill_bonus(skill):+d}"
        for skill in proficient_skills
    )
    equipment_summary = (
        ", ".join(item.name for item in character.equipment) if character.equipment else "None"
    )
    mode_text = MODE_GUIDANCE.get(mode, "")

    return (
        f"{character.name} - Level {character.level} {character.species} {character.character_class}\n"
        f"HP: {character.current_hp}/{character.max_hp}\n\n"
        f"Ability Modifiers:\n{ability_lines}\n\n"
        f"Proficient Skills:\n{skill_lines}\n\n"
        f"Equipment: {equipment_summary}\n\n"
        f"Background:\n{character.background.to_prompt_context()}\n\n"
        f"Current Mode: {mode}\n"
        f"Mode Guidance: {mode_text}"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_prompts.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/agents/prompts.py tests/test_agent_prompts.py
git commit -m "feat: add prompt templates and character context builder"
```

---

### ✅ Task 4: Agent Tools (`agents/tools.py`)

**Files:**
- Modify: `src/dnd_bot/agents/tools.py` (currently empty placeholder)
- Test: `tests/test_agent_tools.py`

**Background:** The character base class already implements all dice mechanics:
- `make_skill_check(Skill, advantage, disadvantage) -> (total, die_roll)` — includes proficiency, exhaustion penalty
- `make_ability_check(Ability, advantage, disadvantage) -> (total, die_roll)`
- `make_saving_throw(Ability, advantage, disadvantage) -> (total, die_roll)`
- `make_attack_roll(Ability, is_proficient, advantage, disadvantage) -> (total, die_roll)`

The tools are thin wrappers that convert string inputs to enums, delegate to the character, and format results. Do NOT re-implement dice rolling or modifier lookups.

`Ability` values: `"strength"`, `"dexterity"`, `"constitution"`, `"intelligence"`, `"wisdom"`, `"charisma"` (from `dnd_bot.character.abilities`)
`Skill` values: `"perception"`, `"athletics"`, `"stealth"`, `"sleight_of_hand"`, etc. (from `dnd_bot.character.skills`)

**Step 1: Write failing tests**

```python
# tests/test_agent_tools.py
from unittest.mock import MagicMock
from dnd_bot.agents.tools import build_tools, ToolContext


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment = []
    char.make_skill_check.return_value = (18, 14)   # (total, die_roll)
    char.make_ability_check.return_value = (15, 13)
    char.make_saving_throw.return_value = (12, 10)
    char.make_attack_roll.return_value = (17, 14)
    return char


def test_build_tools_returns_list():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = build_tools(ctx)
    assert len(tools) > 0


def test_check_status_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["check_status"].invoke({})
    assert "Thorin" in result
    assert "28/32" in result


def test_skill_check_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["skill_check"].invoke({"skill": "perception"})
    assert "Perception" in result
    assert "18" in result


def test_ability_check_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["ability_check"].invoke({"ability": "strength"})
    assert "Strength" in result
    assert "15" in result


def test_speak_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["speak"].invoke({"message": "Hello there!"})
    assert "Hello there!" in result


def test_describe_action_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["describe_action"].invoke({"action": "looks around carefully"})
    assert "looks around carefully" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_tools.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `agents/tools.py`**

```python
from dataclasses import dataclass
from langchain_core.tools import tool
from dnd_bot.character.abilities import Ability
from dnd_bot.character.skills import Skill


@dataclass
class ToolContext:
    """Holds the character reference for tool closures."""
    character: object


def build_tools(ctx: ToolContext) -> list:
    """
    Build LangChain tools bound to a character instance.

    Parameters
    ----------
    ctx : ToolContext
        Context containing the character to bind tools to

    Returns
    -------
    list
        List of LangChain tool objects
    """
    char = ctx.character

    @tool
    def check_status() -> str:
        """Check current HP, conditions, and available resources."""
        conditions = ", ".join(str(c) for c in char.conditions) if char.conditions else "None"
        return (
            f"{char.name}: HP {char.current_hp}/{char.max_hp} | "
            f"Conditions: {conditions}"
        )

    @tool
    def check_inventory() -> str:
        """List all carried equipment."""
        if not char.equipment:
            return "No equipment."
        return "\n".join(f"- {item.name}" for item in char.equipment)

    @tool
    def skill_check(skill: str, advantage: bool = False, disadvantage: bool = False) -> str:
        """
        Make a skill check using the character's proficiency and modifiers.

        Parameters
        ----------
        skill : Skill name in lowercase (e.g. "perception", "athletics", "sleight_of_hand")
        advantage : Roll with advantage (roll twice, take higher)
        disadvantage : Roll with disadvantage (roll twice, take lower)
        """
        try:
            skill_enum = Skill(skill.lower().replace(" ", "_"))
        except ValueError:
            valid = ", ".join(s.value for s in Skill)
            return f"Unknown skill '{skill}'. Valid skills: {valid}"
        total, die_roll = char.make_skill_check(skill_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"{skill.title()} check{adv_str}: {total} (rolled {die_roll} + {bonus:+d})"

    @tool
    def ability_check(ability: str, advantage: bool = False, disadvantage: bool = False) -> str:
        """
        Make a raw ability check.

        Parameters
        ----------
        ability : Ability name (strength/dexterity/constitution/intelligence/wisdom/charisma)
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            return f"Unknown ability '{ability}'. Use: strength, dexterity, constitution, intelligence, wisdom, charisma"
        total, die_roll = char.make_ability_check(ability_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"{ability.capitalize()} check{adv_str}: {total} (rolled {die_roll} + {bonus:+d})"

    @tool
    def attack(target: str, ability: str = "strength", is_proficient: bool = True,
               advantage: bool = False, disadvantage: bool = False) -> str:
        """
        Make an attack roll against a target.

        Parameters
        ----------
        target : Description of the target
        ability : Ability for the attack — "strength" for melee, "dexterity" for ranged/finesse
        is_proficient : Whether proficient with the weapon (default True)
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            ability_enum = Ability.STRENGTH
        total, die_roll = char.make_attack_roll(ability_enum, is_proficient, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"Attack{adv_str} vs {target}: {total} to hit (rolled {die_roll} + {bonus:+d})"

    @tool
    def make_saving_throw(ability: str, advantage: bool = False,
                          disadvantage: bool = False) -> str:
        """
        Make a saving throw.

        Parameters
        ----------
        ability : Ability for the save (e.g. "dexterity", "constitution")
        advantage : Roll with advantage
        disadvantage : Roll with disadvantage
        """
        try:
            ability_enum = Ability(ability.lower())
        except ValueError:
            return f"Unknown ability '{ability}'."
        total, die_roll = char.make_saving_throw(ability_enum, advantage, disadvantage)
        bonus = total - die_roll
        adv_str = " (advantage)" if advantage else " (disadvantage)" if disadvantage else ""
        return f"{ability.capitalize()} saving throw{adv_str}: {total} (rolled {die_roll} + {bonus:+d})"

    @tool
    def speak(message: str, target: str = "") -> str:
        """
        Say something in character.

        Parameters
        ----------
        message : The words to speak
        target : Who you are addressing (optional)
        """
        if target:
            return f'[{char.name} → {target}] "{message}"'
        return f'[{char.name}] "{message}"'

    @tool
    def describe_action(action: str) -> str:
        """
        Describe a non-mechanical action (movement, gestures, expressions).

        Parameters
        ----------
        action : Description of what the character does
        """
        return f"[{char.name}] {action}"

    return [
        check_status, check_inventory, skill_check, ability_check,
        attack, make_saving_throw, speak, describe_action,
    ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_tools.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/agents/tools.py tests/test_agent_tools.py
git commit -m "feat: add LangChain tools delegating to character mechanics"
```

---

### ✅ Task 5: LangGraph Agent (`agents/player.py`)

**Files:**
- Modify: `src/dnd_bot/agents/player.py` (currently empty placeholder)
- Test: `tests/test_agent_graph.py`

**Step 1: Write failing tests**

```python
# tests/test_agent_graph.py
from unittest.mock import MagicMock, patch
from dnd_bot.agents.player import PlayerAgent
from dnd_bot.character.skills import Skill


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = "Dwarf"
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment = []
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS]
    char.background.to_prompt_context.return_value = "A warrior."
    return char


def test_player_agent_init():
    char = make_mock_character()
    with patch("dnd_bot.agents.player.get_llm", return_value=MagicMock()):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
    assert agent is not None
    assert agent.character is char
    assert agent.mode == "exploration"


def test_process_turn_returns_string():
    char = make_mock_character()
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "I look around carefully."
    mock_response.tool_calls = []
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("dnd_bot.agents.player.get_llm", return_value=mock_llm):
        agent = PlayerAgent(character=char, provider="ollama", model="llama3:8b")
        result = agent.process_turn("You enter the cave.")
    assert isinstance(result, str)
    assert len(result) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_graph.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `agents/player.py`**

Note: `PlayerState` is a TypedDict (via `MessagesState`) used for LangGraph graph state — it doesn't support attribute access. `PlayerAgent` stores character and mode as direct attributes instead.

```python
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.prompts import build_character_context, PLAYER_SYSTEM_PROMPT
from dnd_bot.agents.tools import build_tools, ToolContext


class PlayerAgent:
    """
    Player agent for D&D, using an LLM with tool-calling to control a character.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character this agent controls
    model : str
        LLM model name
    provider : str
        LLM provider ("ollama" or "anthropic")
    """

    def __init__(self, character, model: str = "llama3:8b", provider: str = "ollama"):
        self.character = character
        self.mode = "exploration"
        self.tools = build_tools(ToolContext(character=character))
        self._tool_map = {t.name: t for t in self.tools}
        llm = get_llm(model=model, temperature=0.7, provider=provider)
        self._llm = llm.bind_tools(self.tools)
        self._history: list = []

    def process_turn(self, dm_input: str) -> str:
        """
        Process a DM message and return the agent's action.

        Parameters
        ----------
        dm_input : str
            The DM's scene description or prompt

        Returns
        -------
        str
            The agent's response including any tool results
        """
        char_context = build_character_context(self.character, self.mode)
        system = PLAYER_SYSTEM_PROMPT.format(
            character_context=char_context,
            mode_guidance="",  # Already embedded in char_context
        )
        messages = [SystemMessage(content=system)] + self._history + [
            HumanMessage(content=dm_input)
        ]

        response: AIMessage = self._llm.invoke(messages)
        self._history.append(HumanMessage(content=dm_input))
        self._history.append(response)

        parts = []
        if response.content:
            parts.append(str(response.content))

        for tool_call in response.tool_calls:
            tool = self._tool_map.get(tool_call["name"])
            if tool:
                result = tool.invoke(tool_call["args"])
                parts.append(f"ACTION: {tool_call['name']}({tool_call['args']})\nResult: {result}")

        return "\n".join(parts) if parts else "(no response)"

    def set_mode(self, mode: str) -> None:
        """Update the game mode (exploration/combat/roleplay)."""
        self.mode = mode
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_graph.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/agents/player.py tests/test_agent_graph.py
git commit -m "feat: implement PlayerAgent with LangGraph tool-calling"
```

---

### ✅ Task 6: DM Input Parser (`cli/dm_parser.py`)

**Files:**
- Create: `src/dnd_bot/cli/__init__.py`
- Create: `src/dnd_bot/cli/dm_parser.py`
- Test: `tests/test_dm_parser.py`

**Step 1: Write failing tests**

```python
# tests/test_dm_parser.py
from unittest.mock import MagicMock, patch
from dnd_bot.cli.dm_parser import parse_dm_input, DMIntent, DMCommand


def mock_llm_response(json_str: str):
    mock = MagicMock()
    mock.content = json_str
    return mock


def test_parse_dm_input_narrative_passthrough():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "You see a goblin.", "commands": []}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("You see a goblin.", provider="ollama")
    assert result.narrative == "You see a goblin."
    assert result.commands == []


def test_parse_dm_input_extracts_damage():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "The goblin hits you.", '
            '"commands": [{"type": "damage", "value": 5}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("The goblin hits for 5 damage.", provider="ollama")
    assert any(c.type == "damage" and c.value == 5 for c in result.commands)


def test_dm_intent_has_narrative_and_commands():
    intent = DMIntent(narrative="test", commands=[])
    assert intent.narrative == "test"
    assert intent.commands == []


def test_dm_command_types():
    cmd = DMCommand(type="damage", value=3)
    assert cmd.type == "damage"
    assert cmd.value == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dm_parser.py -v`
Expected: FAIL with ImportError

**Step 3: Create `cli/__init__.py` and `cli/dm_parser.py`**

`src/dnd_bot/cli/__init__.py` - empty file

`src/dnd_bot/cli/dm_parser.py`:
```python
import json
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from dnd_bot.agents.llm import get_llm


class DMCommand(BaseModel):
    """A structured game command extracted from DM input."""
    type: str  # "damage", "heal", "mode", "condition", "rest"
    value: int | str | None = None


class DMIntent(BaseModel):
    """Structured interpretation of DM natural language input."""
    narrative: str
    commands: list[DMCommand]


_PARSER_SYSTEM = """\
You are a D&D game state parser. Given DM narration, extract:
1. The narrative text to show the player (preserve dramatic language)
2. Any mechanical game commands embedded in the text

Respond ONLY with valid JSON matching this schema:
{"narrative": "...", "commands": [{"type": "...", "value": ...}]}

Command types: "damage" (value=int), "heal" (value=int), "mode" (value="combat"|"exploration"|"roleplay"),
"condition" (value=str), "rest" (value="short"|"long"), "initiative" (value=null)

If no commands, use an empty list. Include ONLY commands you are certain about.
"""


def parse_dm_input(
    text: str,
    provider: str = "ollama",
    model: str = "llama3:8b",
) -> DMIntent:
    """
    Parse natural language DM input into structured intent.

    Parameters
    ----------
    text : str
        Raw DM input text
    provider : str
        LLM provider for parsing ("ollama" or "anthropic")
    model : str
        Model to use for parsing

    Returns
    -------
    DMIntent
        Structured narrative and commands
    """
    llm = get_llm(model=model, temperature=0.0, provider=provider)
    messages = [
        SystemMessage(content=_PARSER_SYSTEM),
        HumanMessage(content=text),
    ]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
        return DMIntent(
            narrative=data.get("narrative", text),
            commands=[DMCommand(**c) for c in data.get("commands", [])],
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        # Fallback: treat entire input as narrative with no commands
        return DMIntent(narrative=text, commands=[])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dm_parser.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/cli/__init__.py src/dnd_bot/cli/dm_parser.py tests/test_dm_parser.py
git commit -m "feat: add DM input parser for natural language game commands"
```

---

### ✅ Task 7: Terminal Display (`cli/display.py`)

**Files:**
- Create: `src/dnd_bot/cli/display.py`
- Test: `tests/test_cli_display.py`

**Step 1: Write failing tests**

```python
# tests/test_cli_display.py
from io import StringIO
from unittest.mock import MagicMock, patch
from rich.console import Console
from dnd_bot.cli.display import (
    print_character_card, print_scene, print_agent_action, print_dice_roll
)


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = "Dwarf"
    char.current_hp = 28
    char.max_hp = 32
    return char


def test_print_character_card_outputs_name():
    char = make_mock_character()
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_character_card(char)
    assert "Thorin" in buf.getvalue()


def test_print_scene_outputs_description():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_scene("You enter a dark cave.")
    assert "dark cave" in buf.getvalue()


def test_print_agent_action_outputs_character_and_action():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_agent_action("Thorin", "I swing my warhammer!")
    assert "Thorin" in buf.getvalue()


def test_print_dice_roll_outputs_total():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_dice_roll("Attack", 15, "12 + 3")
    assert "15" in buf.getvalue()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_display.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `cli/display.py`**

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def print_character_card(character) -> None:
    """Print a formatted character summary panel."""
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Class", f"{character.species} {character.character_class}")
    table.add_row("Level", str(character.level))
    table.add_row("HP", f"{character.current_hp}/{character.max_hp}")
    console.print(Panel(table, title=f"[bold]{character.name}[/bold]", border_style="blue"))


def print_scene(description: str) -> None:
    """Print a scene description from the DM."""
    console.print(Panel(description, title="[bold yellow]DM[/bold yellow]", border_style="yellow"))


def print_agent_action(character_name: str, action: str) -> None:
    """Print the agent's chosen action."""
    console.print(
        Panel(action, title=f"[bold green]{character_name}[/bold green]", border_style="green")
    )


def print_dice_roll(roll_type: str, total: int, breakdown: str) -> None:
    """Print a formatted dice roll result."""
    console.print(f"  [dim]🎲 {roll_type}:[/dim] [bold]{total}[/bold] [dim]({breakdown})[/dim]")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_display.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/cli/display.py tests/test_cli_display.py
git commit -m "feat: add Rich terminal display utilities"
```

---

### ✅ Task 8: CLI Game Session (`cli/game.py`)

**Files:**
- Create: `src/dnd_bot/cli/game.py`
- Test: `tests/test_cli_game.py`

**Step 1: Write failing tests**

```python
# tests/test_cli_game.py
from io import StringIO
from unittest.mock import MagicMock, patch
from rich.console import Console
from dnd_bot.cli.game import GameSession, apply_commands
from dnd_bot.cli.dm_parser import DMCommand


class SimpleCharacter:
    """Minimal character stub for testing apply_commands state changes."""
    name = "Thorin"
    current_hp = 28
    max_hp = 32
    conditions: list = []
    character_class = "Fighter"
    level = 3
    species = "Dwarf"

    def take_damage(self, amount: int) -> int:
        self.current_hp -= amount
        return amount

    def heal(self, amount: int) -> int:
        healed = min(self.max_hp - self.current_hp, amount)
        self.current_hp += healed
        return healed


class SimpleAgent:
    """Minimal agent stub for testing mode changes."""
    def __init__(self):
        self.mode = "exploration"
        self.character = SimpleCharacter()

    def set_mode(self, mode: str) -> None:
        self.mode = mode


def make_mock_agent():
    agent = MagicMock()
    agent.process_turn.return_value = "I attack the goblin!"
    agent.character = SimpleCharacter()
    return agent


def test_apply_commands_damage():
    char = SimpleCharacter()
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="damage", value=5)], char)
    assert char.current_hp == 23  # 28 - 5 via take_damage


def test_apply_commands_heal():
    char = SimpleCharacter()
    char.current_hp = 20
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="heal", value=5)], char)
    assert char.current_hp == 25  # 20 + 5 via heal


def test_apply_commands_mode_change():
    agent = SimpleAgent()
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="mode", value="combat")], agent.character, agent=agent)
    assert agent.mode == "combat"


def test_game_session_init():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    assert session.agent is agent


def test_handle_slash_command_status():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    buf = StringIO()
    # print_character_card uses display.console, not game.console
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        result = session._handle_slash_command("/status")
    assert result is True
    assert "Thorin" in buf.getvalue()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_game.py -v`
Expected: FAIL with ImportError

**Step 3: Implement `cli/game.py`**

```python
import argparse
from dnd_bot.agents.player import PlayerAgent
from dnd_bot.character.storage import load_character
from dnd_bot.cli.dm_parser import parse_dm_input, DMCommand
from dnd_bot.cli.display import (
    console, print_character_card, print_scene, print_agent_action
)


def apply_commands(
    commands: list[DMCommand],
    character,
    agent: PlayerAgent | None = None,
) -> None:
    """
    Apply parsed DM commands to game state.

    Parameters
    ----------
    commands : list[DMCommand]
        Commands extracted from DM input
    character : AnyCharacter
        The player character to modify
    agent : PlayerAgent, optional
        Agent to update mode on
    """
    for cmd in commands:
        if cmd.type == "damage" and isinstance(cmd.value, int):
            character.take_damage(cmd.value)
            console.print(
                f"  [red]Took {cmd.value} damage. HP: {character.current_hp}/{character.max_hp}[/red]"
            )
        elif cmd.type == "heal" and isinstance(cmd.value, int):
            character.heal(cmd.value)
            console.print(
                f"  [green]Healed {cmd.value}. HP: {character.current_hp}/{character.max_hp}[/green]"
            )
        elif cmd.type == "mode" and agent is not None:
            agent.set_mode(str(cmd.value))
            console.print(f"  [cyan]Mode: {cmd.value}[/cyan]")
        elif cmd.type == "condition":
            character.conditions.append(str(cmd.value))
            console.print(f"  [yellow]Condition applied: {cmd.value}[/yellow]")


class GameSession:
    """
    Manages a D&D game session between a human DM and the player agent.

    Parameters
    ----------
    agent : PlayerAgent
        The player agent
    provider : str
        LLM provider for DM parsing
    model : str
        LLM model for DM parsing
    """

    def __init__(self, agent: PlayerAgent, provider: str = "ollama", model: str = "llama3:8b"):
        self.agent = agent
        self.provider = provider
        self.model = model

    def _handle_slash_command(self, text: str) -> bool:
        """Handle slash commands. Returns True if command was handled."""
        parts = text.strip().split()
        cmd = parts[0].lower()
        char = self.agent.character

        if cmd == "/status":
            print_character_card(char)
            return True
        elif cmd == "/damage" and len(parts) > 1:
            apply_commands([DMCommand(type="damage", value=int(parts[1]))], char)
            return True
        elif cmd == "/heal" and len(parts) > 1:
            apply_commands([DMCommand(type="heal", value=int(parts[1]))], char)
            return True
        elif cmd == "/quit":
            console.print("[bold red]Session ended.[/bold red]")
            raise SystemExit(0)
        return False

    def run(self) -> None:
        """Run the interactive game session loop."""
        char = self.agent.character
        console.print(f"\n[bold blue]=== D&D Session: {char.name} ===[/bold blue]\n")
        print_character_card(char)
        console.print("\nType your scene descriptions. Use /status, /damage N, /heal N, /quit\n")

        while True:
            try:
                raw = console.input("[bold yellow]DM>[/bold yellow] ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not raw:
                continue

            if raw.startswith("/"):
                try:
                    self._handle_slash_command(raw)
                except SystemExit:
                    break
                continue

            intent = parse_dm_input(raw, provider=self.provider, model=self.model)
            print_scene(intent.narrative)
            apply_commands(intent.commands, char, agent=self.agent)

            response = self.agent.process_turn(intent.narrative)
            print_agent_action(char.name, response)


def main() -> None:
    """CLI entry point: dndbot play <character_yaml>"""
    parser = argparse.ArgumentParser(description="D&D Player Agent CLI")
    parser.add_argument("character", help="Path to character YAML file")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "anthropic"])
    parser.add_argument("--model", default="llama3:8b")
    args = parser.parse_args()

    character = load_character(args.character)
    agent = PlayerAgent(character=character, model=args.model, provider=args.provider)
    session = GameSession(agent=agent, provider=args.provider, model=args.model)
    session.run()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_game.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add src/dnd_bot/cli/game.py tests/test_cli_game.py
git commit -m "feat: add CLI game session with DM interface and slash commands"
```

---

### ✅ Task 9: Update `agents/__init__.py`

**Files:**
- Modify: `src/dnd_bot/agents/__init__.py`

**Step 1: Read current contents**

Read `src/dnd_bot/agents/__init__.py` to see existing exports.

**Step 2: Add new exports**

```python
from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.player import PlayerAgent
from dnd_bot.agents.tools import build_tools, ToolContext
from dnd_bot.agents.prompts import build_character_context, PLAYER_SYSTEM_PROMPT
```

**Step 3: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add src/dnd_bot/agents/__init__.py
git commit -m "feat: export agent components from agents package"
```

---

### ✅ Task 10: Documentation

**Files:**
- Create: `docs/agents.md`
- Create: `docs/cli.md`
- Modify: `docs/README.md`

**Step 1: Create `docs/agents.md`**

Document: architecture overview, PlayerAgent API, tools list, LLM provider setup.

**Step 2: Create `docs/cli.md`**

Document: installation, `dndbot play` command, DM input examples, slash commands.

**Step 3: Update `docs/README.md`**

Add "Agent System" section linking to agents.md and cli.md.

**Step 4: Commit**

```bash
git add docs/agents.md docs/cli.md docs/README.md
git commit -m "docs: add agent system and CLI documentation"
```

---

## Verification

1. **Run all tests:** `pytest -v` — all tests pass
2. **Lint check:** `ruff check .` — no errors
3. **Integration test:** `dndbot play <character_yaml>` with a real Ollama model
4. **Manual playtest:** Run a short session with `/status` working and agent responding in character

---

## Files Summary

| File | Status |
|------|--------|
| `src/dnd_bot/agents/llm.py` | ✅ Done (Task 2) |
| `src/dnd_bot/agents/prompts.py` | ✅ Done (Task 3) |
| `src/dnd_bot/agents/tools.py` | Implement (Task 4) |
| `src/dnd_bot/agents/player.py` | Implement (Task 5) |
| `src/dnd_bot/cli/__init__.py` | Create (Task 6) |
| `src/dnd_bot/cli/dm_parser.py` | Create (Task 6) |
| `src/dnd_bot/cli/display.py` | Create (Task 7) |
| `src/dnd_bot/cli/game.py` | Create (Task 8) |
| `src/dnd_bot/agents/__init__.py` | Modify (Task 9) |
| `pyproject.toml` | ✅ Done (Task 1) |
| `docs/agents.md` | Create (Task 10) |
| `docs/cli.md` | Create (Task 10) |
| `docs/README.md` | Modify (Task 10) |
