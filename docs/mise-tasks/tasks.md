# Available Tasks

This page documents all available mise tasks in the repository.

## ccusage

**Type**: Mise-defined task  
**Description**: Monitor usage with ccusage blocks  
**Script type**: External command

### Usage
```bash
mise run ccusage
```

### What it does
Runs `bunx ccusage blocks --live` to monitor resource usage in real-time using the ccusage tool.

### Dependencies
- Node.js (for bunx)
- ccusage package (installed via bunx)

---

## format-github-refs

**Type**: Python script (shared library)  
**Description**: Format unformatted GitHub references in markdown files  
**Script type**: Shared library script using `journal_lib.github`

### Usage
```bash
# Format today's daily note
mise run format-github-refs

# Format specific file  
mise run format-github-refs path/to/file.md

# Dry run to preview changes
mise run format-github-refs --dry-run

# Specify repository
mise run format-github-refs --repo org/repo-name
```

### What it does
- Processes markdown files to format unformatted GitHub references
- Converts plain GitHub issue/PR numbers to properly formatted links
- Adds checkmarks for closed/merged items
- Uses the `journal_lib.github` module for GitHub API integration
- Defaults to today's daily note if no file specified

### Arguments
- `file` (optional): Markdown file to process
- `--repo`: GitHub repository in format `org/repo`
- `--dry-run`: Preview changes without modifying files

### Dependencies  
- Python 3.13+
- journal_lib package
- GitHub CLI (`gh`) authenticated

---

## lazydocker

**Type**: Bash script  
**Description**: Open lazydocker  
**Script type**: Isolated bash script

### Usage
```bash
# Open lazydocker in home directory (default)
mise run lazydocker

# Open lazydocker in specific directory  
mise run lazydocker <directory>
```

### What it does
Opens the lazydocker terminal UI for Docker management, optionally in a specific directory using direnv for environment management.

### Arguments
- `directory` (optional): Root directory to use (defaults to `$HOME`)

### Dependencies
- lazydocker
- direnv
- with-direnv utility

---

## new-python-script

**Type**: Bash script  
**Description**: Create a new Python script with UV inline metadata and shebang  
**Script type**: Isolated bash script

### Usage
```bash
# Create new script
mise run new-python-script script-name

# Using flag syntax
mise run new-python-script --name script-name
```

### What it does
- Creates a new Python script in the `mise-tasks/` directory
- Uses `uv init --script` to generate PEP 723 compliant script
- Adds proper shebang for uv script execution
- Makes the script executable

### Arguments
- `script-name`: Name of the script to create
- `--name`: Alternative flag-based way to specify script name

### Dependencies
- uv
- Standard Unix tools (awk, chmod)

---

## open-daily-note

**Type**: Bash script  
**Description**: Open daily note in obsidian  
**Script type**: Isolated bash script  

### Usage
```bash
mise run open-daily-note
```

### What it does
Opens today's daily note in Obsidian using the advanced URI plugin.

### Dependencies
- Obsidian with advanced URI plugin
- Notes vault named "notes"

---

## query-notes

**Type**: Bash script  
**Description**: Interactive note finder and opener  
**Script type**: Isolated bash script

### Usage
```bash
# Interactive mode with fzf
mise run query-notes

# Open specific note
mise run query-notes note-name

# Start with initial query
mise run query-notes -q "search term"
```

### What it does
- Uses fzf for interactive note selection
- Searches markdown files in the notes directory
- Opens selected notes in Obsidian
- Supports initial query for filtering

### Arguments
- `note-name` (optional): Specific note to open
- `-q <query>`: Initial search query

### Environment Variables
- `NOTES_DIR`: Directory containing notes (default: `/Users/seletz/develop/notes`)
- `EDITOR`: Editor to use (default: `emacsclient -c -n -a emacs`)

### Dependencies
- fzf
- fd (find alternative)
- bat (for preview)
- Obsidian

---

## update-daily-work

**Type**: Python script (shared library)  
**Description**: Update daily journal with GitHub activity  
**Script type**: Shared library script using `journal_lib.github`

### Usage
```bash
# Update today's note with today's activity
mise run update-daily-work

# Update specific date
mise run update-daily-work 2024-01-15

# Update with different time periods
mise run update-daily-work --period this-week
mise run update-daily-work --period this-month
mise run update-daily-work --period this-quarter

# Dry run to preview changes
mise run update-daily-work --dry-run
```

### What it does
- Fetches GitHub activity (issues created, PRs created, issues worked on, issues closed, PRs merged)
- Updates the "Daily Review" section in markdown daily notes
- Automatically formats GitHub references using `format-github-refs` functionality
- Supports different time periods and specific dates

### Arguments
- `date` (optional): Specific date in YYYY-MM-DD format
- `--period`: Time period for activity (`today`, `this-week`, `this-month`, `this-quarter`)
- `--dry-run`: Preview changes without modifying files

### Dependencies
- Python 3.13+
- journal_lib package
- GitHub CLI (`gh`) authenticated