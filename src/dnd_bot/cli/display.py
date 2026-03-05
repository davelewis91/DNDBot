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
        conditions_str = ", ".join(c.value for c in character.conditions)
        table.add_row("Conditions", conditions_str)
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
    console.print(f"  [dim]{roll_type}:[/dim] [bold]{total}[/bold] [dim]({breakdown})[/dim]")


def print_turn_result(character_name: str, turn) -> None:
    """
    Print a formatted turn result: narrative text and tool actions with results.

    Parameters
    ----------
    character_name : str
        Name of the character whose turn it is
    turn : TurnResult
        The structured turn result to display
    """
    sections = []
    if turn.narrative:
        sections.append(turn.narrative)
    for action in turn.actions:
        sections.append(
            f"[bold yellow]⚡ {action.name}[/bold yellow]\n[dim]{action.result}[/dim]"
        )
    content = "\n\n".join(sections) if sections else "[dim](no response)[/dim]"
    console.print(Panel(
        content,
        title=f"[bold green]{character_name}[/bold green] [dim cyan]{turn.mode}[/dim cyan]",
        border_style="green",
    ))


def print_mode_change(mode: str) -> None:
    """Print a mode change notification."""
    console.print(f"[bold cyan]● Mode → {mode}[/bold cyan]")
