# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal tasks repository that manages one-off scripts using `mise` as the task runner. The project supports two types of scripts:

1. **Isolated scripts**: Self-contained Python scripts using UV's PEP 723 inline metadata
2. **Shared library scripts**: Scripts that use common functionality from the `journal_lib` package

## Architecture

### Directory Structure
```
/tasks/
├── mise-tasks/              # Executable scripts (discovered by mise)
├── packages/
│   └── journal-lib/         # Shared library package
│       ├── pyproject.toml   # Library configuration
│       └── src/journal_lib/ # Python modules
├── mise.toml               # Task runner configuration
└── pyproject.toml          # Workspace configuration
```

### Script Types

#### Isolated Scripts
- Use shebang: `#!/usr/bin/env -S uv run --script`
- Include PEP 723 metadata block for dependencies
- Executable with `chmod +x`
- Run directly or via `mise run <script-name>`

#### Shared Library Scripts  
- Use shebang: `#!/usr/bin/env python`
- Import from `journal_lib` package
- Must run via `mise run <script-name>` to use proper uv workspace environment
- Library automatically available via uv workspace after `uv sync`

### Key Library: journal_lib.github

The main shared library provides GitHub integration for daily journal automation:
- Fetches issues/PRs created, worked on, closed, and merged
- Formats GitHub references as markdown links with checkmarks for closed issues
- Updates daily review sections in markdown files
- Searches across organizations: "digitalgedacht", "nexiles", and personal repos

## Development Commands

### Creating New Scripts
```bash
# Create new isolated script
mise run new-python-script <script-name>

# OR using mise flag syntax
mise run new-python-script --name <script-name>
```

### Running Scripts
```bash
# Run any script in mise-tasks/
mise run <script-name>

# List available tasks
mise run
```

### Package Management
```bash
# Install workspace packages and dependencies automatically
uv sync

# Install development dependencies
uv sync --group dev
```

### Development Quality Tasks
```bash
# Code linting
mise run lint

# Code formatting
mise run format

# Check code formatting without making changes  
mise run format-check

# Type checking with ty (Astral's fast type checker)
mise run typecheck

# Run tests with coverage
mise run test

# Run all quality checks (uses mise depends for parallel execution)
mise run check
```

### Existing Tasks
- `format-github-refs`: Format unformatted GitHub references in markdown files
- `ccusage`: Monitor usage with bunx ccusage blocks --live

## Configuration

### Project Configuration
- **Root pyproject.toml**: Defines uv workspace with `packages/*` members
- **Library pyproject.toml**: Standalone `journal-lib` package configuration
- **mise.toml**: Configures UV as package manager, sets up virtual environment in `.venv`
- Uses `.env` file for environment variables

### GitHub Integration
- Requires `gh` CLI tool to be authenticated
- Default repository: `digitalgedacht/careassist-odoo`
- Personal notes directory: `/Users/seletz/develop/notes`
- Daily notes stored in `daily/YYYY-MM-DD.md` format

## tmux Integration

The repository is integrated with tmux via a popup window:
```tmux
bind T display-popup \
         -w 70% -h 70% \
         -d "$HOME/develop/tasks" \
         "mise run"
```

## Code Quality & Style

### Tooling Stack
- **Linting**: `ruff` - Fast Python linter and code formatter
- **Type Checking**: `ty` - Astral's extremely fast Python type checker (pre-alpha)
- **Testing**: `pytest` with coverage reporting (≥90% required)
- **Formatting**: `ruff format` - Consistent code style

### Code Style Guidelines
- Use RST-style docstrings for Python functions
- Follow existing patterns when adding new scripts
- Maintain separation between executable scripts (mise-tasks/) and libraries (src/)
- Modern type hints with `list[T]` and `dict[K, V]` instead of `typing.List[T]`
- Do not close issues, we use PRs and code reviews

### Quality Standards
- All code must pass `mise run check` before committing
- Tests require ≥90% coverage
- Type checking with `ty` must pass (note: ty is pre-alpha, expect warnings)
- Code must be formatted with `ruff format`
- Focus on BEHAVIOUR in tests. Simple clear tests over 100% test coverage

### CI/CD Pipeline
- **GitHub Actions** automatically run quality checks on PRs and commits
- **Workflows**: `ci.yml` runs comprehensive quality checks (lint, format, typecheck, test)
- **Coverage reporting** with Codecov integration
- **Branch protection**: Requires passing checks for `develop` and `main` branches
- **ALWAYS** run code checks before committing.