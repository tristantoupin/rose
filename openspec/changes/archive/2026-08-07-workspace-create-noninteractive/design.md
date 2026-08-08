# Design: workspace-create-noninteractive

## Architecture

No new modules. One file changes: `rose_cli/commands/workspace/create.py`. All existing helpers (`_ensure_repo_cache`, `_pick_repos`, `_check_branch_conflicts`, `_ensure_bare_clones`, `_get_default_branches`, `_scaffold_template`, `_create_worktrees`, `_write_code_workspace`) are reused unchanged.

```
rose_cli/
└── commands/
    └── workspace/
        └── create.py   # Updated: --name/--branch/--repo options, non-interactive branch
```

## Command Interface

```
rose create [--refresh] [--name NAME] [--branch BRANCH] [--repo ORG/REPO]...
```

- `--name TEXT` — workspace name. If given, skips the name prompt.
- `--branch TEXT` — feature branch name. If given, skips the branch prompt. If omitted while `--name` is given, defaults to `--name` (same default as the interactive prompt).
- `--repo TEXT` — repeatable (`multiple=True`). One or more `org/repo` values to include. If given (non-empty), skips the fuzzy picker entirely.

All three flags are optional and independent — each one that's supplied replaces the corresponding prompt; any not supplied still prompts as today. This keeps `rose create` fully backward compatible: running it with no flags is unchanged.

## Behavior

### Name resolution

```python
if name is None:
    # existing while-loop prompt
else:
    if not _NAME_RE.match(name):
        click.echo("  ✗  Name must contain only letters, numbers, hyphens, underscores.")
        raise SystemExit(1)
    target = workspace_root / name
    if target.exists():
        click.echo(f"  ✗  '{target}' already exists. Choose a different name.")
        raise SystemExit(1)
```

Same validation as the interactive loop, just exits instead of re-prompting since there's no TTY to retry against.

### Branch resolution

```python
branch = branch or name  # click.prompt("Feature branch name", default=name) equivalent
if branch is None:
    branch = click.prompt("Feature branch name", default=name)
```

If `--name` was passed but `--branch` wasn't, branch defaults to `name` with no prompt (matches the existing `default=name` behavior of the prompt, just applied non-interactively).

### Repo resolution

```python
if repo:  # non-empty tuple from multiple=True
    repos = list(repo)
else:
    repos = _pick_repos(all_repos, org)
```

No membership check against `all_repos` — a repo passed via `--repo` that isn't cached is treated like a search-picker result: it flows straight into `_ensure_bare_clones`, which clones it directly from GitHub. `github.ssh_url`/`default_branch` will fail naturally (existing error handling) if the repo doesn't exist or isn't accessible.

### Everything after selection is unchanged

Branch conflict check, bare clone ensure, default branch detection, scaffold, worktree creation, `.code-workspace` write, history update, summary, and `open_cursor` all run exactly as they do today — none of that code depends on how `name`, `branch`, or `repos` were obtained.

## Updated Command Signature

```python
@click.command()
@click.option("--refresh", is_flag=True, help="Force repo cache refresh before selection.")
@click.option("--name", "name_opt", default=None, help="Workspace name (skips prompt).")
@click.option("--branch", "branch_opt", default=None, help="Feature branch name (skips prompt, defaults to --name).")
@click.option("--repo", "repo_opt", multiple=True, help="Repo to include (org/repo). Repeatable; skips the picker.")
def create(refresh: bool, name_opt: str | None, branch_opt: str | None, repo_opt: tuple[str, ...]) -> None:
    ...
```

## Full Non-Interactive Flow

```
rose create --name my-feature --branch my-feature --repo myorg/api-abc --repo myorg/frontend
│
├─ 1. Load config (unchanged)
├─ 2. Ensure repo cache (unchanged — still used to build history/choices even if unused for picking)
├─ 3. Name: validate --name, no prompt
├─ 4. Branch: use --branch (or --name if --branch omitted), no prompt
├─ 5. Repos: use --repo values, no picker
├─ 6. Branch conflict check (unchanged)
├─ 7. Ensure bare clones (unchanged)
├─ 8. Default branch detection (unchanged)
├─ 9. Scaffold + worktrees (unchanged)
├─ 10. Write .code-workspace (unchanged)
├─ 11. Update history (unchanged)
└─ 12. Summary + open Cursor (unchanged)
```

No prompts are shown, no InquirerPy call is made, and the command exits after the summary — safe to run in CI, a script, or piped from another tool with no stdin attached.

## Error Cases (new/changed)

| Condition | Behavior |
|---|---|
| `--name` invalid chars | `✗  Name must contain only letters, numbers, hyphens, underscores.` → exit 1 (no retry prompt) |
| `--name` target already exists | `✗  '<target>' already exists. Choose a different name.` → exit 1 |
| `--repo` given but empty string values | Click rejects via normal option parsing (non-empty required per value) |
| `--repo` not in cache | Accepted; clone attempted directly, existing clone-failure handling applies |
| Only `--branch` or only `--repo` given (no `--name`) | Falls back to prompting for `name`; the given `--branch`/`--repo` still skip their own prompts |

## Click Integration

No changes to `rose_cli/main.py` or `rose_cli/commands/workspace/__init__.py` — `create` is already registered as a top-level `rose create` command.
