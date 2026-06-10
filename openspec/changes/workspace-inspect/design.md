# Design: workspace-inspect

## Architecture

No new files required. One new command file added to the existing `workspace/` group.

```
rose_cli/
├── commands/
│   └── workspace/
│       ├── __init__.py      # Updated: register `inspect` subcommand
│       └── inspect.py       # New: workspace inspect command
└── git.py                   # Updated: add worktree_status() helper
```

## Command Interface

```
rose workspace inspect <name> [--no-git]
```

- `<name>` — required positional arg; matched against `rose.name` in each `.code-workspace` file
- `--no-git` — skip git queries; show metadata + docs only

## Workspace Resolution

Walk `workspace_path` for subdirectories containing `<subdir>/<subdir>.code-workspace`. Load JSON and check `rose.name == name`. First match wins.

```python
def _find_workspace(workspace_path: Path, name: str) -> tuple[Path, dict]:
    """Return (workspace_dir, rose_metadata) or abort."""
    for ws_dir in sorted(workspace_path.iterdir()):
        ws_file = ws_dir / f"{ws_dir.name}.code-workspace"
        if not ws_file.exists():
            continue
        data = json.loads(ws_file.read_text())
        rose = data.get("rose", {})
        if rose.get("name") == name:
            return ws_dir, rose
    click.echo(f"  ✗  Workspace '{name}' not found in {workspace_path}")
    raise SystemExit(1)
```

## Git Helper: `worktree_status`

Add to `rose_cli/git.py`:

```python
def worktree_status(worktree_path: Path) -> dict:
    """Return status info for a worktree.

    Returns:
        {
          "branch": str,          # current branch name (or "(detached)")
          "ahead": int,           # commits ahead of upstream
          "behind": int,          # commits behind upstream
          "modified": int,        # staged + unstaged modified files
          "untracked": int,       # untracked files
        }
    """
```

Implementation:
- **branch**: `git -C <path> rev-parse --abbrev-ref HEAD`
- **ahead/behind**: `git -C <path> rev-list --count --left-right @{upstream}...HEAD`
  - Parse `"<behind>\t<ahead>"` — catch `subprocess.CalledProcessError` (no upstream) → both 0
- **modified/untracked**: `git -C <path> status --porcelain`
  - Count lines starting with `' M'`, `'M '`, `'MM'`, `'A '`, `'D '` etc. for modified
  - Count lines starting with `'??'` for untracked

## Output Format

```
Workspace: my-feature
Path:      ~/workspaces/my-feature/
Created:   2026-06-09

Repos ──────────────────────────────────────────────────────
  api-abc       my-feature        ↑2 ↓0   2M 1?
  frontend           my-feature        ↑0 ↓3   clean
  api-gateway        my-feature        ↑0 ↓0   clean

Docs ───────────────────────────────────────────────────────
  findings.md            # Investigation Findings
  implementation-plan.md # Implementation Plan
  (no docs found)
```

Legend printed at bottom only when dirty indicators present:
```
  M = modified files   ? = untracked files   ↑/↓ = ahead/behind origin
```

Column widths computed dynamically from longest repo name and branch name.

## Command Flow

```
rose workspace inspect <name> [--no-git]
│
├─ 1. Load config — abort if missing
│
├─ 2. Resolve workspace
│     Walk workspace_path for .code-workspace files
│     Match rose.name == <name>
│     Abort with clear error if not found
│
├─ 3. Print header (name, path, created)
│
├─ 4. Unless --no-git:
│     For each repo in rose.repos:
│       worktree_path = workspace_dir / "repos" / repo_name_from_full(full_name)
│       If path missing: show "  ✗  <repo>  (worktree missing)"
│       Else: call git.worktree_status(worktree_path)
│     Print Repos table
│
├─ 5. Scan docs/
│     docs_dir = workspace_dir / "docs"
│     List *.md files (top-level only, sorted)
│     Extract first heading (first line starting with "# ")
│     Print Docs section
│
└─ 6. Print legend if any repo was dirty
```

## Error Cases

| Condition | Behavior |
|---|---|
| Config missing | `✗  No config found. Run 'rose init' first.` → exit 1 |
| Workspace not found | `✗  Workspace '<name>' not found in <path>` → exit 1 |
| Worktree dir missing | Row shows `(worktree missing)` in red, continues |
| No upstream set | ahead/behind shown as `--` |
| No docs folder | Docs section shows `(no docs found)` |

## Implementation Details

### `git rev-list --count --left-right`

```python
result = subprocess.run(
    ["git", "-C", str(path), "rev-list", "--count", "--left-right", "@{upstream}...HEAD"],
    capture_output=True, text=True,
)
if result.returncode != 0:
    behind, ahead = 0, 0  # no upstream
else:
    behind, ahead = (int(x) for x in result.stdout.strip().split())
```

### Dirty state from `git status --porcelain`

```python
modified = untracked = 0
for line in output.splitlines():
    if line.startswith("??"):
        untracked += 1
    else:
        modified += 1
```

### First heading extraction

```python
def _first_heading(md_path: Path) -> str:
    for line in md_path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""
```

### Click integration

```python
# rose_cli/commands/workspace/__init__.py
from rose_cli.commands.workspace.inspect import inspect
workspace.add_command(inspect)
```
