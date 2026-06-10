# Design: deactivate-workspace

## Architecture

No new modules required. One new command file in the existing `workspace/` group; one new helper in `git.py`.

```
rose_cli/
├── commands/
│   └── workspace/
│       ├── __init__.py      # Updated: register `deactivate` subcommand
│       └── deactivate.py    # New: workspace deactivate command
└── git.py                   # Updated: add remove_worktree() and worktree_status()
```

> `worktree_status()` is also needed by the planned `workspace inspect` command — adding it here once avoids duplication.

## Command Interface

```
rose workspace deactivate <name> [--force]
```

- `<name>` — required positional arg; matched against `rose.name` in each `.code-workspace` file
- `--force` — skip uncommitted/unpushed safety checks and force-remove dirty worktrees

## Workspace Resolution

Reuse the same walk pattern established in `workspace inspect`:

```python
def _find_workspace(workspace_path: Path, name: str) -> tuple[Path, dict]:
    """Return (workspace_dir, code_workspace_data) or abort."""
    for ws_dir in sorted(workspace_path.iterdir()):
        ws_file = ws_dir / f"{ws_dir.name}.code-workspace"
        if not ws_file.exists():
            continue
        data = json.loads(ws_file.read_text())
        if data.get("rose", {}).get("name") == name:
            return ws_dir, data
    click.echo(f"  ✗  Workspace '{name}' not found in {workspace_path}")
    raise SystemExit(1)
```

## Git Helpers

### `worktree_status(worktree_path)` — add to `git.py`

```python
def worktree_status(worktree_path: Path) -> dict:
    """Return status info for a live worktree.

    Returns:
        {
          "branch": str,     # current branch name (or "(detached)")
          "ahead": int,      # commits ahead of upstream
          "behind": int,     # commits behind upstream
          "modified": int,   # staged + unstaged changed files
          "untracked": int,  # untracked files
        }
    """
```

Implementation:
- **branch**: `git -C <path> rev-parse --abbrev-ref HEAD`
- **ahead/behind**: `git -C <path> rev-list --count --left-right @{upstream}...HEAD`
  - Parse `"<behind>\t<ahead>"` — `CalledProcessError` (no upstream) → both 0
- **modified/untracked**: `git -C <path> status --porcelain`
  - Lines starting with `??` → untracked; everything else → modified

### `remove_worktree(bare_path, worktree_path, force)` — add to `git.py`

```python
def remove_worktree(bare_path: Path, worktree_path: Path, force: bool = False) -> None:
    """Remove a worktree via the bare clone."""
```

Implementation:
```python
args = ["worktree", "remove", str(worktree_path)]
if force:
    args.append("--force")
_git(bare_path, *args)
```

## Safety Check Logic

For each repo in `rose.repos`:

```
worktree_path = workspace_dir / "repos" / repo_name_from_full(full_name)
```

If `worktree_path` does not exist → skip (already removed or never created).

Otherwise call `worktree_status(worktree_path)`. A repo is **blocked** if:
```
status["modified"] > 0 OR status["untracked"] > 0 OR status["ahead"] > 0
```

If any repos are blocked and `--force` is not set:
```
  ✗  Cannot deactivate — repos have uncommitted or unpushed work:
     api-abc    2 modified, 1 untracked
     frontend        1 unpushed commit
  Run with --force to deactivate anyway (changes will be lost).
```
Then exit 1.

## Deactivation Sequence

```
rose workspace deactivate <name>
│
├─ 1. Load config — abort if missing
│
├─ 2. Resolve workspace
│     Walk workspace_path for .code-workspace files
│     Match rose.name == <name>
│     Abort if not found
│
├─ 3. Check rose.status
│     If already "inactive": echo warning and exit 0
│
├─ 4. Safety check (skip if --force)
│     For each repo in rose.repos:
│       worktree_path = workspace_dir / "repos" / repo_short
│       If path missing: skip
│       status = worktree_status(worktree_path)
│       If blocked: accumulate error
│     If any errors: print summary and exit 1
│
├─ 5. Remove worktrees
│     For each repo in rose.repos:
│       worktree_path = workspace_dir / "repos" / repo_short
│       bare_path = git.bare_clone_path(full_name)
│       If worktree_path missing: echo "  ⚠  <repo>  (already removed)"
│       Else:
│         remove_worktree(bare_path, worktree_path, force=--force)
│         echo "  ✓  <repo>  worktree removed"
│     Prune stale worktree entries from each bare clone
│       git -C <bare_path> worktree prune
│
├─ 6. Remove repos/ directory
│     shutil.rmtree(workspace_dir / "repos")
│
├─ 7. Update .code-workspace
│     Set data["rose"]["status"] = "inactive"
│     Write back to ws_file
│     echo "  ✓  Workspace marked inactive"
│
└─ 8. Print summary
      echo "─" * 50
      echo "  ✓  <name> deactivated"
      echo "     Run 'rose workspace reactivate <name>' to restore."
```

## Output Format

```
Deactivating workspace: my-feature

  Checking for uncommitted work...
  ✓  api-abc    clean
  ✓  frontend        clean
  ⚠  api-gateway     (worktree missing — skipping)

  Removing worktrees...
  ✓  api-abc    worktree removed
  ✓  frontend        worktree removed

  ✓  Workspace marked inactive

──────────────────────────────────────────────────
  ✓  my-feature deactivated
     Run 'rose workspace reactivate my-feature' to restore.
```

When `--force` is used and a repo is dirty, add a per-repo warning:
```
  ⚠  api-abc    forced (2 modified, 1 untracked)
```

## Error Cases

| Condition | Behavior |
|---|---|
| Config missing | `✗  No config found. Run 'rose init' first.` → exit 1 |
| Workspace not found | `✗  Workspace '<name>' not found in <path>` → exit 1 |
| Already inactive | `⚠  Workspace '<name>' is already inactive.` → exit 0 |
| Blocked repos (no --force) | List all blocked repos + hint → exit 1 |
| Worktree path missing | Skip silently with `⚠  (already removed)` |
| `git worktree remove` fails | Print error, continue with remaining repos, exit 1 at end |

## `.code-workspace` Status Field

After deactivation the file gains one new key under `rose`:

```json
{
  "rose": {
    "name": "my-feature",
    "created": "2026-06-09",
    "status": "inactive",
    "repos": { ... }
  }
}
```

Active workspaces have either `"status": "active"` or no `status` key (backwards-compatible).

## Click Integration

```python
# rose_cli/commands/workspace/__init__.py
from rose_cli.commands.workspace.deactivate import deactivate
workspace.add_command(deactivate)
```
