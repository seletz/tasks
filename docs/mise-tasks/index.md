# Mise Tasks

This section documents all available mise tasks in this repository.

Mise tasks are executable scripts located in the `mise-tasks/` directory that can be run using `mise run <task-name>` or directly executed.

## Types of Scripts

### Isolated Scripts
- Use `#!/usr/bin/env -S uv run --script` shebang
- Include PEP 723 inline metadata for dependencies
- Self-contained with no external library dependencies
- Can be run directly or via mise

### Shared Library Scripts
- Use `#!/usr/bin/env python` shebang
- Import functionality from the `journal_lib` package
- Must be run via `mise run <task-name>` to access workspace environment
- Leverage shared code for common functionality

## Available Tasks

See the [Tasks](tasks.md) page for detailed documentation of each available task.