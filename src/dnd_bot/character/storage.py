"""YAML-based character storage for persistence."""

from pathlib import Path

import yaml

from .abilities import Ability, AbilityBonus, AbilityScores
from .background import Background, Motivation, PersonalityTraits
from .character import Character, Equipment
from .classes import ClassName, get_class
from .conditions import Condition, ConditionManager
from .exhaustion import Exhaustion
from .skills import Skill, SkillProficiency, SkillSet
from .species import SpeciesName, get_species

DEFAULT_CHARACTERS_DIR = Path("./characters")


def _character_to_dict(character: Character) -> dict:
    """Convert a Character to a YAML-friendly dictionary."""
    # Skill proficiencies - only save proficient/expertise skills
    skill_profs = {}
    for skill in Skill:
        prof = character.skills.proficiencies[skill]
        if prof.proficient or prof.expertise:
            skill_profs[skill.value] = {
                "proficient": prof.proficient,
                "expertise": prof.expertise,
            }

    # Ability bonuses
    ability_bonuses = []
    for ab in character.ability_bonuses:
        ability_bonuses.append({
            "ability": ab.ability.value,
            "value": ab.value,
            "source": ab.source,
            "is_temporary": ab.is_temporary,
        })

    # Saving throw proficiencies
    save_profs = [a.value for a in character.saving_throw_proficiencies]

    # Background with motivations
    motivations = []
    for m in character.background.motivations:
        motivations.append({
            "description": m.description,
            "priority": m.priority,
            "is_secret": m.is_secret,
        })

    return {
        "name": character.name,
        "level": character.level,
        "species": character.species.name.value,
        "class": character.character_class.name.value,
        "ability_scores": {
            "strength": character.ability_scores.strength,
            "dexterity": character.ability_scores.dexterity,
            "constitution": character.ability_scores.constitution,
            "intelligence": character.ability_scores.intelligence,
            "wisdom": character.ability_scores.wisdom,
            "charisma": character.ability_scores.charisma,
        },
        "skill_proficiencies": skill_profs,
        "saving_throw_proficiencies": save_profs,
        "ability_bonuses": ability_bonuses,
        "combat": {
            "current_hp": character.current_hp,
            "max_hp": character.max_hp,
            "temp_hp": character.temp_hp,
            "armor_class": character.armor_class,
        },
        "exhaustion": character.exhaustion.level,
        "conditions": [
            {
                "condition": ac.condition.value,
                "source": ac.source,
                "duration": ac.duration,
            }
            for ac in character.conditions.active
        ],
        "equipment": {
            "weapons": character.equipment.weapons,
            "armor": character.equipment.armor,
            "shield": character.equipment.shield,
            "items": character.equipment.items,
            "gold": character.equipment.gold,
        },
        "experience_points": character.experience_points,
        "background": {
            "name": character.background.name,
            "backstory": character.background.backstory,
            "personality": {
                "traits": character.background.personality.traits,
                "ideals": character.background.personality.ideals,
                "bonds": character.background.personality.bonds,
                "flaws": character.background.personality.flaws,
            },
            "motivations": motivations,
            "fears": character.background.fears,
            "allies": character.background.allies,
            "enemies": character.background.enemies,
            "notes": character.background.notes,
        },
    }


def _dict_to_character(data: dict) -> Character:
    """Convert a YAML dictionary back to a Character."""
    # Rebuild ability scores
    ability_scores = AbilityScores(**data["ability_scores"])

    # Get species and class from registry
    species = get_species(SpeciesName(data["species"]))
    character_class = get_class(ClassName(data["class"]))

    # Rebuild skill proficiencies
    skills = SkillSet()
    for skill_name, prof_data in data.get("skill_proficiencies", {}).items():
        skill = Skill(skill_name)
        skills.proficiencies[skill] = SkillProficiency(
            skill=skill,
            proficient=prof_data.get("proficient", False),
            expertise=prof_data.get("expertise", False),
        )

    # Rebuild ability bonuses
    ability_bonuses = []
    for ab_data in data.get("ability_bonuses", []):
        ability_bonuses.append(AbilityBonus(
            ability=Ability(ab_data["ability"]),
            value=ab_data["value"],
            source=ab_data.get("source", ""),
            is_temporary=ab_data.get("is_temporary", True),
        ))

    # Rebuild saving throw proficiencies
    save_profs = [Ability(a) for a in data.get("saving_throw_proficiencies", [])]

    # Rebuild equipment
    equip_data = data.get("equipment", {})
    equipment = Equipment(
        weapons=equip_data.get("weapons", []),
        armor=equip_data.get("armor", ""),
        shield=equip_data.get("shield", False),
        items=equip_data.get("items", []),
        gold=equip_data.get("gold", 0),
    )

    # Rebuild background
    bg_data = data.get("background", {})
    personality_data = bg_data.get("personality", {})
    personality = PersonalityTraits(
        traits=personality_data.get("traits", []),
        ideals=personality_data.get("ideals", []),
        bonds=personality_data.get("bonds", []),
        flaws=personality_data.get("flaws", []),
    )

    motivations = []
    for m_data in bg_data.get("motivations", []):
        motivations.append(Motivation(
            description=m_data["description"],
            priority=m_data.get("priority", 1),
            is_secret=m_data.get("is_secret", False),
        ))

    background = Background(
        name=bg_data.get("name", ""),
        backstory=bg_data.get("backstory", ""),
        personality=personality,
        motivations=motivations,
        fears=bg_data.get("fears", []),
        allies=bg_data.get("allies", []),
        enemies=bg_data.get("enemies", []),
        notes=bg_data.get("notes", ""),
    )

    # Combat stats
    combat_data = data.get("combat", {})

    # Exhaustion
    exhaustion = Exhaustion(level=data.get("exhaustion", 0))

    # Conditions
    conditions = ConditionManager()
    for cond_data in data.get("conditions", []):
        conditions.add(
            condition=Condition(cond_data["condition"]),
            source=cond_data.get("source", ""),
            duration=cond_data.get("duration"),
        )

    return Character(
        name=data["name"],
        level=data.get("level", 1),
        ability_scores=ability_scores,
        skills=skills,
        species=species,
        character_class=character_class,
        background=background,
        current_hp=combat_data.get("current_hp", 0),
        max_hp=combat_data.get("max_hp", 0),
        temp_hp=combat_data.get("temp_hp", 0),
        armor_class=combat_data.get("armor_class", 10),
        equipment=equipment,
        ability_bonuses=ability_bonuses,
        exhaustion=exhaustion,
        conditions=conditions,
        saving_throw_proficiencies=save_profs,
        experience_points=data.get("experience_points", 0),
    )


def save_character(character: Character, directory: Path | None = None) -> Path:
    """Save a character to a YAML file.

    The filename is derived from the character's name.

    Args:
        character: The character to save.
        directory: Directory to save to. Defaults to ./characters/

    Returns:
        Path to the saved file.
    """
    if directory is None:
        directory = DEFAULT_CHARACTERS_DIR

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    # Create a safe filename from the character name
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in character.name)
    safe_name = safe_name.strip().replace(" ", "_").lower()
    filename = directory / f"{safe_name}.yaml"

    data = _character_to_dict(character)

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return filename


def load_character(filepath: Path | str) -> Character:
    """Load a character from a YAML file.

    Args:
        filepath: Path to the YAML file.

    Returns:
        The loaded Character.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        yaml.YAMLError: If the file is not valid YAML.
        ValueError: If the YAML doesn't represent a valid character.
    """
    filepath = Path(filepath)

    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return _dict_to_character(data)


def list_characters(directory: Path | None = None) -> list[Path]:
    """List all character files in a directory.

    Args:
        directory: Directory to search. Defaults to ./characters/

    Returns:
        List of paths to character YAML files.
    """
    if directory is None:
        directory = DEFAULT_CHARACTERS_DIR

    directory = Path(directory)

    if not directory.exists():
        return []

    return sorted(directory.glob("*.yaml"))


def delete_character(filepath: Path | str) -> bool:
    """Delete a character file.

    Args:
        filepath: Path to the YAML file.

    Returns:
        True if deleted, False if file didn't exist.
    """
    filepath = Path(filepath)

    if filepath.exists():
        filepath.unlink()
        return True
    return False
