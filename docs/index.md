# Personal Tasks

This is a repo where I keep my one-off scripts.

## one-off scripts

I use `mise` to run tasks.  They're located in the `mise-tasks`
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

For more complex scripts that share functionality, this project uses a **uv workspace** structure with a dedicated library package:

```
/tasks/
├── packages/
│   └── journal-lib/          # Shared library package
│       ├── pyproject.toml    # Library configuration
│       └── src/
│           └── journal_lib/  # Python modules
│               ├── __init__.py
│               └── github.py # GitHub integration functions
├── mise-tasks/               # Executable scripts
│   ├── format-github-refs    # Uses journal_lib.github
│   └── update-daily-work     # Uses journal_lib.github
└── pyproject.toml           # Workspace configuration
```

### Setup Process

1. **Workspace Structure**: Uses uv's workspace feature to manage multiple packages
2. **Root pyproject.toml**: Configures workspace and dependencies:
   ```toml
   [project]
   name = "tasks"
   dependencies = ["journal-lib"]
   
   [tool.uv.workspace]
   members = ["packages/*"]
   
   [tool.uv.sources]
   journal-lib = { workspace = true }
   ```
3. **Library pyproject.toml**: Clean, standalone package configuration:
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   
   [project]
   name = "journal-lib"
   version = "0.1.0"
   description = "Personal journal automation library with GitHub integration"
   ```
4. **Automatic Setup**: Run `uv sync` to automatically install workspace packages in editable mode
5. **Script Shebang**: Scripts using libraries use `#!/usr/bin/env python` instead of the isolated `uv run --script`
6. **Execution**: Run via `mise run script-name` to use the proper uv-managed environment

### Benefits

- **Clean Separation**: Library code is properly isolated in its own package
- **No Circular Dependencies**: Clear dependency flow from scripts to library
- **Workspace Management**: uv handles multiple packages automatically
- **Eliminate Code Duplication**: Shared functions live in one place
- **Maintainability**: Bug fixes and improvements benefit all scripts
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