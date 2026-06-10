# Design: edit-workspace-command

## Architecture

No new modules required. One new command file in the existing `workspace/` group; no new helpers in `git.py` — `remove_worktree` and `worktree_status` will be added by `deactivate-workspace`.

```
rose_cli/
├── commands/
│   └── workspace/
│       ├── __init__.py   # Updated: register `edit` subcommand
│       └── edit.py       # New: workspace edit command
```

> `remove_worktree()` and `worktree_status()` are defined by the `deactivate-workspace` change. This command depends on those helpers existing in `git.py`.

## Command Interface

```
rose workspace edit <name> [--force]
```

- `<name>` — required positional arg; matched against `rose.name` in each `.code-workspace` file
- `--force` — skip uncommitted/unpushed safety checks on repos being removed

## Workspace Resolution

Reuse the same `_find_workspace` helper pattern established in `deactivate-workspace`:

```python
def _find_workspace(workspace_root: Path, name: str) -> tuple[Path, dict]:
    """Return (workspace_dir, code_workspace_data) or abort."""
    for ws_dir in sorted(workspace_root.iterdir()):
        if not ws_dir.is_dir():
            continue
        ws_files = list(ws_dir.glob("*.code-workspace"))
        if not ws_files:
            continue
        data = json.loads(ws_files[0].read_text())
        if data.get("rose", {}).get("name") == name:
            return ws_dir, data
    click.echo(f"  ✗  Workspace '{name}' not found in {workspace_root}")
    raise SystemExit(1)
```

After resolution, guard against inactive workspaces:

```python
if data.get("rose", {}).get("status") == "inactive":
    click.echo(f"  ✗  Workspace '{name}' is inactive. Run 'rose workspace reactivate {name}' first.")
    raise SystemExit(1)
```

## Repo Picker

Pre-select the workspace's current repos in the multi-select fuzzy picker. Reuse `_build_choices` and `_run_search_picker` from `create.py`, but pass current repos as the initial default selection:

```python
def _pick_repos_for_edit(
    all_repos: list[str],
    current_repos: list[str],
    org: str,
) -> list[str]:
    recent = load_history()
    choices = _build_choices(recent, all_repos)

    selected = inquirer.fuzzy(
        message="Select repos (space to mark, enter to confirm):",
        choices=choices,
        multiselect=True,
        default=current_repos,
        validate=lambda result: (
            len([r for r in result if r != _SEARCH_SENTINEL]) > 0
        ),
        invalid_message="Select at least one repo",
    ).execute()

    final: list[str] = []
    needs_search = False
    for item in selected:
        if item == _SEARCH_SENTINEL:
            needs_search = True
        else:
            final.append(item)

    if needs_search:
        extra = _run_search_picker(org)
        for repo in extra:
            if repo not in final:
                final.append(repo)
        merged = list(dict.fromkeys(all_repos + extra))
        save_repo_cache(org, merged)

    return final
```

## Diff Logic

```python
current_set = set(current_repos)
new_set = set(new_repos)
added = [r for r in new_repos if r not in current_set]
removed = [r for r in current_repos if r not in new_set]
```

If both `added` and `removed` are empty → no changes, echo info and exit 0.

## Safety Check for Removals

Same logic as `deactivate-workspace`. For each repo in `removed`:

```python
worktree_path = workspace_dir / "repos" / git.repo_name_from_full(full_name)
```

If `worktree_path` exists, call `git.worktree_status(worktree_path)`. A repo is **blocked** if:
```
status["modified"] > 0 OR status["untracked"] > 0 OR status["ahead"] > 0
```

If any blocked and `--force` not set:
```
  ✗  Cannot remove repos — they have uncommitted or unpushed work:
     api-abc    2 modified, 1 untracked
  Run with --force to remove anyway (changes will be lost).
```
→ exit 1.

## Adding Repos

For each repo in `added`:

1. `_ensure_bare_clones([full_name])` — clone or fetch
2. Get default branch via `github.default_branch(full_name)`
3. Get workspace branch from `data["rose"]["repos"]` (any existing repo's `"branch"` value)
4. Create worktree: `git.add_worktree(bare_path, worktree_path, branch, from_ref)`
5. Append to `data["rose"]["repos"]` and `data["folders"]`

```python
branch = next(iter(data["rose"]["repos"].values()))["branch"]
```

## Removing Repos

For each repo in `removed`:

1. `worktree_path = workspace_dir / "repos" / git.repo_name_from_full(full_name)`
2. If path exists: `git.remove_worktree(bare_path, worktree_path, force=force)`, then `shutil.rmtree(worktree_path, ignore_errors=True)`
3. `git -C bare_path worktree prune`
4. Remove from `data["rose"]["repos"]` and from `data["folders"]`

## `.code-workspace` Update

After all mutations, rewrite the file:

```python
data["folders"] = [
    {"path": f"repos/{git.repo_name_from_full(r)}", "name": git.repo_name_from_full(r)}
    for r in final_repos
]
data["folders"].append({"path": "docs", "name": "docs"})
ws_file.write_text(json.dumps(data, indent=2))
```

`final_repos` is the ordered list preserving existing repos first, then appending new ones.

## Edit Sequence

```
rose workspace edit <name>
│
├─ 1. Load config — abort if missing
│
├─ 2. Resolve workspace
│     Walk workspace_root for .code-workspace files
│     Match rose.name == <name>
│     Abort if not found or status == "inactive"
│
├─ 3. Load repo cache + open fuzzy picker
│     Pre-select current repos
│     User adds/removes freely
│
├─ 4. Diff: compute added / removed
│     If no changes: echo info and exit 0
│
├─ 5. Safety check on removed repos (skip if --force)
│     For each removed repo:
│       If worktree_path exists: worktree_status()
│       If blocked: accumulate error
│     If any errors: print summary and exit 1
│
├─ 6. Process removals
│     For each removed repo:
│       remove_worktree(bare_path, worktree_path, force)
│       shutil.rmtree(worktree_path)
│       git worktree prune on bare
│       echo "  ✓  <repo>  removed"
│
├─ 7. Process additions
│     _ensure_bare_clones(added)
│     For each added repo:
│       get default branch
│       add_worktree(bare_path, worktree_path, branch, from_ref)
│       echo "  ✓  <repo>  added → <branch>"
│
├─ 8. Update .code-workspace
│     Rebuild folders list + update rose.repos dict
│     Write back to ws_file
│
├─ 9. Summary + open Cursor
│     echo summary
│     open_cursor(ws_file)
```

## Output Format

```
Editing workspace: my-feature

  Current repos: api-abc, frontend
  Select updated repo set...

  No changes.          ← if user selects same set

  Removing repos...
  ✓  frontend          removed

  Adding repos...
  ✓  api-gateway       added → my-feature

──────────────────────────────────────────────────
  ✓  my-feature updated
     Repos (2): api-abc, api-gateway
```

## Error Cases

| Condition | Behavior |
|---|---|
| Config missing | `✗  No config found. Run 'rose init' first.` → exit 1 |
| Workspace not found | `✗  Workspace '<name>' not found in <path>` → exit 1 |
| Workspace inactive | `✗  Workspace '<name>' is inactive. Run 'rose workspace reactivate <name>' first.` → exit 1 |
| No changes selected | `  No changes.` → exit 0 |
| Blocked removals (no --force) | List all blocked repos + hint → exit 1 |
| Worktree already missing | Skip with `⚠  (already removed)` |
| `git worktree remove` fails | Print error, continue, exit 1 at end |
| Branch conflict on add | `✗  Branch '<branch>' already exists in <repo>` → exit 1 |

## Click Integration

```python
# rose_cli/commands/workspace/__init__.py
from rose_cli.commands.workspace.edit import edit
workspace.add_command(edit)
```
