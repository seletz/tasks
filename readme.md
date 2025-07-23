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

## tmux integration

I have this integrated in my `tmux` config.  I bound a `display-popup`
window to `T` like so:

```text
bind T display-popup \
         -w 70% -h 70% \
         -d "$HOME/develop/tasks" \
         "mise run"
```



