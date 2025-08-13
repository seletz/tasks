# Personal Tasks

This is a repo where I keep my one-off scripts.

## one-off scripts

I use `mise` to run tasks.  They`re located in the `mise-tasks`
directory in this repo.

I can use whatever executable I place in that directory.

With `uv` and python, this is simple as `chmod +x` a script
which looks like this:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///


def main() -> None:
    print("Hello from foo!")


if __name__ == "__main__":
    main()
```

Note:

- The script uses a shebang which uses uv to run the script
- It uses [PEP 723](https://peps.python.org/pep-0723) for inline requirements,
  which is supported by `uv`

### New scripts

To create a new script, I use:

```bash
$ mise new-python-script bar
```

This will:
- call the `new-python-script` script in `mise-tasks`
- That script will run `uv init --script bar
- and then use `awk` to insert the shebang
- and then make it executable.

## Scripts with Shared Libraries

For more complex scripts that share functionality, this project uses a local Python package structure:

```
/tasks/
├── src/
│   └── journal_lib/          # Shared libraries
│       ├── __init__.py
│       └── github.py         # GitHub integration functions
├── mise-tasks/               # Executable scripts
│   ├── format-github-refs    # Uses journal_lib.github
│   └── update-daily-work     # Uses journal_lib.github
└── pyproject.toml           # Package configuration
```

### Setup Process

1. **Package Structure**: Libraries go in `src/journal_lib/` to avoid polluting the special `mise-tasks/` directory
2. **pyproject.toml Configuration**: Uses uv's native project format with hatchling build backend:
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   
   [project]
   dependencies = ["tasks"]
   
   [tool.hatch.build.targets.wheel]
   packages = ["src/journal_lib"]
   
   [tool.uv.sources]
   tasks = { path = ".", editable = true }
   ```
3. **Automatic Setup**: Run `uv sync` to automatically install the local package in editable mode
4. **Script Shebang**: Scripts using libraries use `#!/usr/bin/env python` instead of the isolated `uv run --script`
5. **Execution**: Run via `mise run script-name` to use the proper uv-managed environment

### Benefits

- **Eliminate Code Duplication**: Shared functions live in one place
- **Maintainability**: Bug fixes and improvements benefit all scripts
- **Clean Architecture**: Separation between library code and CLI interfaces
- **Testing**: Libraries can be tested independently

### Example Library Usage

```python
#!/usr/bin/env python

import journal_lib.github as gh

def main():
    # Use shared GitHub functions
    issues = gh.fetch_issues_created("today")
    for issue in issues:
        print(gh.format_issue_ref(issue))

if __name__ == "__main__":
    main()
```

## tmux integration

I have this integrated in my `tmux` config.  I bound a `display-popup`
window to `T` like so:

```text
bind T display-popup \
         -w 70% -h 70% \
         -d "$HOME/develop/tasks" \
         "mise run"
```



