from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_character_card(character) -> None:
    """Print a formatted character summary panel."""
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Class", f"{character.species.name.value.title()} {character.character_class}")
    table.add_row("Level", str(character.level))
    table.add_row("HP", f"{character.current_hp}/{character.max_hp}")
    table.add_row("AC", str(character.armor_class))
    table.add_row("Prof Bonus", f"+{character.proficiency_bonus}")
    table.add_row("Initiative", f"{character.initiative:+d}")
    if character.conditions:
        conditions_str = ", ".join(c for c in character.conditions.list_conditions())
        table.add_row("Conditions", conditions_str)
    console.print(Panel(table, title=f"[bold]{character.name}[/bold]", border_style="blue"))


def print_scene(description: str) -> None:
    """Print a scene description from the DM."""
    console.print(Panel(description, title="[bold yellow]DM[/bold yellow]", border_style="yellow"))


def print_agent_turn(
    character_name: str,
    narrative: str,
    tool_results: list[str],
    mode: str,
) -> None:
    """
    Print a player agent's turn from multi-agent session data.

    Parameters
    ----------
    character_name : str
        Name of the acting character
    narrative : str
        The character's narrative response text
    tool_results : list[str]
        Tool result strings to display below the narrative
    mode : str
        Current game mode shown in the panel title
    """
    sections = []
    if narrative:
        sections.append(narrative)
    for result in tool_results:
        sections.append(f"[dim]{result}[/dim]")
    content = "\n\n".join(sections) if sections else "[dim](no response)[/dim]"
    console.print(Panel(
        content,
        title=f"[bold green]{character_name}[/bold green] [dim cyan]{mode}[/dim cyan]",
        border_style="green",
    ))


def print_mode_change(mode: str) -> None:
    """Print a mode change notification."""
    console.print(f"[bold cyan]● Mode → {mode}[/bold cyan]")
