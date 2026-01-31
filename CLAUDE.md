# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DNDBot is a Discord bot for D&D gaming. Currently in early alpha (v0.1.0) with foundational structure in place but minimal implementation.

## Development Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests with coverage
pytest

# Lint code
ruff check .

# Fix lint issues automatically
ruff check --fix .
```

## Architecture

- **Package location**: `src/dnd_bot/` - main source code
- **Tests**: `tests/` - pytest test modules
- **Build system**: Hatchling (PEP 517)

## Code Standards

- Python 3.13+ required
- Line length: 100 characters
- Linting: ruff with rules E, W, F, I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade)
- Test coverage reporting enabled
