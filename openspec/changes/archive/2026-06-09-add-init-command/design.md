# Design: add-init-command

## Architecture

### File Layout

```
~/.rose/
├── config.toml                   # Persisted init config
└── templates/
    └── default/                  # Default workspace template
        ├── .cursor/
        │   └── skills/
        │       └── docs/
        │           └── SKILL.md  # Docs skill (user-provided content)
        └── docs/                 # Empty docs folder
```

### Config Schema (`~/.rose/config.toml`)

```toml
[workspace]
path = "/absolute/path/to/worktrees"

[template]
path = "~/.rose/templates/default"
```

Both values are absolute paths. Tilde (`~`) is expanded on read.

## Command Flow

```
rose init
│
├─ 1. Print ASCII greeting
│     Rose character with speech bubble
│
├─ 2. Check GitHub CLI
│     ├─ `gh` not found → warn "Install gh: https://cli.github.com"
│     ├─ `gh auth status` fails → warn "Run `gh auth login`"
│     └─ `gh auth status` passes → ✓ "GitHub authenticated"
│     (always continue)
│
├─ 3. Check existing config
│     ├─ ~/.rose/config.toml exists → warn, prompt to overwrite
│     │   ├─ user says no → abort
│     │   └─ user says yes → continue
│     └─ doesn't exist → continue
│
├─ 4. Prompt: workspace_path
│     Default: ~/workspaces
│     Validate: parent directory exists or can be created
│     Action: create directory if it doesn't exist
│
├─ 5. Prompt: template_path
│     Default: ~/.rose/templates/default
│     ├─ Path exists → register as-is, print contents
│     └─ Path doesn't exist → scaffold default template
│
├─ 6. Write ~/.rose/config.toml
│     Create ~/.rose/ if needed
│
└─ 7. Print summary
      ✓ Config saved
      ✓ Workspace path created
      ✓ Template ready
      ⚠ GitHub warnings (if any)
      "All set! Rose is ready to grow! 🌹"
```

## Implementation Details

### ASCII Greeting

```
                        .-"""-.
                       / .===. \
                       \/ 6 6 \/
                       ( \___/ )
  _________________ooo__\_____/_____________________
 /                                                  \
| Hi! I'm Rose! I keep your workspace tidy          |
| and your worktrees happy. Let's get started!      |
 \______________________________ooo_________________/
                       |  |  |
                       |_ | _|
                       |  |  |
                       |__|__|
                       /-'Y'-\
                      (__/ \__)
```

### GitHub Auth Check

Uses `subprocess.run` to call:
1. `which gh` (or `shutil.which("gh")`) — check if installed
2. `gh auth status` — check if authenticated (exit code 0 = authed)

No dependency on `gh` Python bindings. Pure subprocess.

### Config Persistence

Use Python `tomllib` (read, stdlib 3.11+) and `tomli_w` (write, third-party) for TOML.
Since project targets Python 3.9+, use `tomli` for reading on <3.11 and `tomli_w` for writing.

Alternative: keep it simple with a hand-written TOML serializer for two flat sections. Avoids new dependencies.

**Decision: hand-write TOML.** Config is two keys in two sections — no need for a library.

### Template Scaffolding

When creating default template at `~/.rose/templates/default/`:
1. Create directory structure: `.cursor/skills/docs/` and `docs/`
2. Write `SKILL.md` with the docs skill content (hardcoded in Python)

### Prompts

Use `click.prompt()` for input with defaults. Use `click.confirm()` for overwrite confirmation.

### New Dependencies

None. All stdlib + click (already a dependency).

## Code Organization

```
rose_cli/
├── __init__.py
├── main.py           # CLI group + init command registration
├── commands/
│   └── init.py       # init command implementation
├── config.py         # Config read/write helpers
└── ascii.py          # Rose ASCII art constant
```

Split into modules now to avoid `main.py` growing into a monolith as more commands are added.
