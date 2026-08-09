# Design: docs-vault

## Architecture

No new subpackages. One new command group (mirrors `org`), small additions
to `config.py`, `init.py`, `create.py`, `edit.py`.

```
rose_cli/
├── commands/
│   ├── vault/
│   │   ├── __init__.py      # New: `vault` group
│   │   └── set.py           # New: `rose vault set <path>`
│   ├── init.py               # Updated: prompt for vault path; tweak skill text
│   └── workspace/
│       ├── create.py         # Updated: resolve docs target (vault or local)
│       └── edit.py           # Updated: preserve existing docs folder entry
└── config.py                 # Updated: get_vault_path/set_vault_path
```

## Config

`~/.rose/config.toml` gains an optional section:

```toml
[workspace]
path = "/absolute/path/to/workspaces"

[template]
path = "/absolute/path/to/template"

[github]
org = "your-org"

[vault]
path = "/absolute/path/to/vault"
```

`config.py` additions, mirroring the existing `get_org`/`set_org` pair:

```python
def get_vault_path() -> Path | None:
    """Return configured vault path, or None if not set."""
    raw = read_config().get("vault", {}).get("path", "")
    return expand_path(raw) if raw else None


def set_vault_path(path: str) -> None:
    """Update [vault] path in config, preserving other sections."""
    config = read_config()
    write_config(
        config.get("workspace", {}).get("path", ""),
        config.get("template", {}).get("path", ""),
        config.get("github", {}).get("org", ""),
        vault_path=path,
    )
```

`write_config` gains an optional `vault_path: str = ""` kwarg; when set, emit
a `[vault]` section. `set_org` (existing) must pass through whatever vault
path is already configured so it isn't dropped on the next `org set` call —
same pattern it already uses for `template`.

## `rose init` — vault prompt

Added after the existing template prompt, blank-skippable:

```
Vault path for persistent docs (blank to skip, docs/ stays local): [ ]
```

- Blank → no `[vault]` section written → `rose create` behaves exactly as
  today (this is the default for **every existing config** until a user
  explicitly runs `rose init` again or `rose vault set`)
- Non-blank → `mkdir -p` the path, write `[vault]` section

## `rose vault set <path>` — new command

Same shape as `rose_cli/commands/org/set.py`:

```python
@click.command()
@click.argument("path")
def set_vault_cmd(path: str) -> None:
    """Set the persistent docs vault path."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)
    vault_path = expand_path(path)
    vault_path.mkdir(parents=True, exist_ok=True)
    set_vault_path(str(vault_path))
    click.echo(f"  ✓  Vault path set to {vault_path}")
```

Registered in `rose_cli/main.py` next to `org`/`repos`.

## `rose create` — resolving the docs target

Today (`create.py:168-172, 214`):

```python
def _scaffold_template(workspace_path: Path, template_path: Path) -> None:
    if not template_path.is_dir():
        return
    shutil.copytree(str(template_path), str(workspace_path), dirs_exist_ok=True)
...
folders.append({"path": "docs", "name": "docs"})
```

The template's *only* current content is `docs/` (see `init.py`'s
`scaffold_template`), but a user could have added other files to their
template, so the docs piece is split out rather than special-cased away:

```python
def _resolve_docs_target(vault_path: Path | None, name: str, workspace_path: Path) -> Path:
    """Vault subfolder if configured, else the local docs/ folder (today's behavior)."""
    if vault_path is not None:
        return vault_path / name
    return workspace_path / "docs"


def _scaffold_docs(template_path: Path, docs_target: Path) -> None:
    """Create docs_target, seeding it from template's docs/ if present."""
    docs_target.mkdir(parents=True, exist_ok=True)
    template_docs = template_path / "docs"
    if template_docs.is_dir():
        shutil.copytree(str(template_docs), str(docs_target), dirs_exist_ok=True)


def _scaffold_template(workspace_path: Path, template_path: Path) -> None:
    """Copy template into workspace folder, excluding docs/ (handled by _scaffold_docs)."""
    if not template_path.is_dir():
        return
    for item in template_path.iterdir():
        if item.name == "docs":
            continue
        dest = workspace_path / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
        else:
            shutil.copy2(str(item), str(dest))
```

`_write_code_workspace`'s docs entry becomes path-aware instead of hardcoded,
shared with `edit.py` (single source of truth — this is the fix for the
duplicate hardcoding that caused the backward-compat bug):

```python
def _docs_folder_entry(docs_target: Path, workspace_path: Path) -> dict:
    """Relative 'docs' entry when local (today's exact output); absolute otherwise."""
    try:
        path_str = str(docs_target.relative_to(workspace_path))
    except ValueError:
        path_str = str(docs_target)
    return {"path": path_str, "name": "docs"}
```

`create()` flow addition, right after `target.mkdir(parents=True)`:

```python
vault_path = get_vault_path()
docs_target = _resolve_docs_target(vault_path, name, target)
_scaffold_template(target, template_path)   # unchanged call, now docs-exclusive
_scaffold_docs(template_path, docs_target)
```

`_write_code_workspace` takes `docs_target` and `workspace_path` and appends
`_docs_folder_entry(docs_target, workspace_path)` instead of the hardcoded
literal.

When `vault_path is None`, `docs_target == workspace_path / "docs"`, so
`_docs_folder_entry` computes `{"path": "docs", "name": "docs"}` — the exact
same dict written today. Zero behavior change for unconfigured installs.

## `rose edit` — preserve, don't clobber

Current bug (`edit.py:277-282`): folders are rebuilt from scratch every call
and the docs entry is re-hardcoded to `{"path": "docs", "name": "docs"}`,
discarding whatever was actually there. Harmless today (it's always right),
but would silently break any vault-linked workspace's docs link the first
time someone runs `rose edit` on it — reintroducing a `docs/` folder
reference that no longer exists in the workspace directory.

Fix: read the existing entry out of the already-loaded `data` before
rebuilding, and reuse it verbatim instead of resolving it fresh:

```python
_DEFAULT_DOCS_ENTRY = {"path": "docs", "name": "docs"}

existing_docs_entry = next(
    (f for f in data.get("folders", []) if f.get("name") == "docs"),
    _DEFAULT_DOCS_ENTRY,
)
...
data["folders"] = [
    {"path": f"repos/{git.repo_name_from_full(r)}", "name": git.repo_name_from_full(r)}
    for r in final_repos
]
data["folders"].append(existing_docs_entry)
```

This requires no vault-awareness in `edit.py` at all — it just stops
destroying information it didn't need to touch. Fixes the shared root cause
(the hardcoded literal) rather than special-casing vault vs. non-vault here.

## Docs skill text — path heuristic

`DOCS_SKILL_CONTENT` in `init.py` currently tells the agent:

```
1. Check the `Workspace Paths` in user_info for a path ending in `/docs`
```

A vault-linked folder's *path* is `<vault>/<name>` (doesn't end in `/docs`),
but its *name* (shown in `user_info`/Cursor's folder list) is still
`"docs"`. Update the instruction to match by folder name first, path suffix
as fallback:

```
1. Check the `Workspace Paths` in user_info for a folder named `docs`
   (its path may be inside the workspace, e.g. `.../docs`, or point at a
   documentation vault elsewhere, e.g. `.../vault/<workspace-name>`)
2. That is your target documentation folder
```

## Command Flow (new workspace, vault configured)

```
rose create --name my-feature --repo org/api
│
├─ load_and_validate_config()          # workspace_root, template_path, org
├─ get_vault_path()                    # ~/vault  (or None)
├─ ... repo selection, bare clones, default branches (unchanged) ...
├─ target.mkdir()                      # ~/workspaces/my-feature/
├─ docs_target = _resolve_docs_target(vault_path, "my-feature", target)
│     → ~/vault/my-feature             (vault case)
│     → ~/workspaces/my-feature/docs   (no-vault case, unchanged)
├─ _scaffold_template(target, template_path)   # non-docs template files only
├─ _scaffold_docs(template_path, docs_target)  # mkdir + seed skill file
├─ _create_worktrees(...)              # unchanged
├─ _write_code_workspace(..., docs_target, target)
│     folders += _docs_folder_entry(docs_target, target)
│     → {"path": "/Users/x/vault/my-feature", "name": "docs"}   (vault)
│     → {"path": "docs", "name": "docs"}                        (no-vault)
└─ open_cursor(ws_file)
```

## Error Cases

| Condition | Behavior |
|---|---|
| `[vault]` not configured | Identical to current behavior — local `docs/` |
| Vault path configured but not creatable (permissions) | `mkdir` raises; let it propagate as today's uncaught errors do elsewhere in `create.py` (no new error handling needed — consistent with existing style) |
| Vault subfolder already exists (name reuse after a torn-down workspace) | Reused as-is — same continuity model the user described ("refer to the folder in the vault we created for this workspace"); no special handling needed since `mkdir(exist_ok=True)` + `copytree(dirs_exist_ok=True)` are both idempotent |
| `rose vault set` before `rose init` | `✗  No config found. Run 'rose init' first.` (matches `org set`) |
