# Design: list-workspaces-command

## Architecture

### File Layout

```
rose_cli/commands/workspace/
├── __init__.py          # adds `list` subcommand (existing file, extend)
├── create.py            # unchanged
└── list.py              # new
```

### Workspace Discovery

A workspace is any direct child directory of `workspace_path` that contains a `*.code-workspace` file. The `.code-workspace` file written by `workspace create` embeds a `rose` block:

```json
{
  "rose": {
    "name": "my-feature",
    "created": "2026-06-09",
    "repos": {
      "MyOrg/api.abc": { "branch": "my-feature", "default_branch": "main" }
    }
  }
}
```

Discovery reads this block to build the picker label. If the file is missing or malformed, fall back to the directory name only.

### Command Flow

```
rose workspace list
│
├─ 1. Load and validate config (reuse _load_and_validate_config)
│
├─ 2. Scan workspace root
│     ├─ No workspaces found → print "No workspaces found in <path>." → exit 0
│     └─ Found N workspaces → build picker choices
│
├─ 3. Present InquirerPy fuzzy single-select
│     Label format: "<name>  [<repos>]  (<created>)"
│     Example:      "clin-1234  [api.abc, api.bcd]  (2026-06-09)"
│     Sort: newest first (by `rose.created`, then directory mtime as fallback)
│
├─ 4. User selects (or Ctrl-C to abort)
│
├─ 5. Call _open_cursor(ws_file)
```

### Module: `rose_cli/commands/workspace/list.py`

```python
@click.command("list")
def list_cmd() -> None:
    """List workspaces and open one in Cursor."""
```

Key helpers:

- `_scan_workspaces(root: Path) -> list[WorkspaceInfo]` — discovers and parses workspaces
- `WorkspaceInfo` — dataclass: `name`, `created`, `repos`, `ws_file`, `workspace_path`
- `_build_label(info: WorkspaceInfo) -> str` — formats the picker display string
- `_pick_workspace(infos: list[WorkspaceInfo]) -> WorkspaceInfo` — wraps InquirerPy fuzzy

### Reuse

- `_load_and_validate_config` from `create.py` → extract to module-level in `__init__.py` or a shared `_helpers.py`
- `_open_cursor` from `create.py` → same extraction

> **Decision**: extract shared helpers to `rose_cli/commands/workspace/_helpers.py` so both `create.py` and `list.py` import from one place. Import changes are the only modification to `create.py`.

### Label Format

```
clin-1234  [api.abc, api.bcd]  (2026-06-09)
```

- Repo names are short names (`repo_name_from_full`), comma-separated
- Date is `rose.created` from the `.code-workspace` file
- If `rose` block absent: label is just the directory name

### Error States

| Condition | Behavior |
|-----------|----------|
| No config | "Run 'rose init' first." → exit 1 |
| Workspace root doesn't exist | "No workspaces found in `<path>`." → exit 0 |
| No workspace dirs found | "No workspaces found in `<path>`." → exit 0 |
| `.code-workspace` unreadable/malformed | Skip `rose` metadata; show dir name only |
| Cursor not in PATH | Warn + print manual command (existing `_open_cursor` behavior) |
| User cancels picker (Ctrl-C) | Exit 0 silently |
