# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DNDBot is a multi-agent bot system for simulating D&D gaming. Currently in early alpha (v0.1.0) with foundational structure in place but minimal implementation.

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
- **Documentation**: `docs` - markdown files documenting code structure and design decisions

## Code Standards

- Python 3.13+ required
- Line length: 100 characters
- Linting: ruff with rules E, W, F, I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade)
- Test coverage reporting enabled
- Prioritise readable code over efficient code
- Re-use code where possible, use the least amount of code as possible while maintaining readability
- YAGNI - try not to overly abstract code, when it isn't required
- When a line is too long because of a string, don't just shorten the string, find a way to keep the same string but split it across multiple lines.

# Documentation

- Use numpy-style docstrings, except for very short functions, where a single line docstring is acceptable
- Keep the documentation in `docs` updated with every task

# Testing

- Test only entry and exit behaviours, i.e. testing input and output results match expectations. Do not test internal behaviour like whether a particular function is called (no `assert_called_once_with`).
- Minimise mocking except where necessary, such as an external API or a long-running (>10s) process.