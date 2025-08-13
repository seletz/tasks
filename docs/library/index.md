# Python Library

This section documents the `journal-lib` Python package that provides shared functionality for tasks.

## Overview

The `journal-lib` package is a workspace-local library that provides common functionality, particularly for GitHub integration and daily journal automation.

## Key Features

- **GitHub Integration**: Fetch issues, PRs, and format GitHub references
- **Daily Journal Support**: Automated updates to daily review sections
- **Multi-Organization Support**: Search across multiple GitHub organizations
- **Markdown Formatting**: Generate properly formatted markdown links and references

## Package Structure

```
packages/journal-lib/
├── pyproject.toml          # Package configuration
└── src/
    └── journal_lib/
        ├── __init__.py     # Package initialization
        └── github.py       # GitHub integration functions
```

## Installation

The library is automatically installed when you run `uv sync` in the workspace root, as it's configured as a workspace dependency.

## API Reference

For detailed API documentation, see the [API Reference](../reference/journal_lib/index.md) section.