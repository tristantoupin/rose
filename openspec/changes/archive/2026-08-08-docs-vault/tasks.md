# Tasks: docs-vault

## Config

- [x] 1. `rose_cli/config.py`
  - Add `vault_path: str = ""` kwarg to `write_config`, emit `[vault]` section when non-empty
  - Add `get_vault_path() -> Path | None`
  - Add `set_vault_path(path: str) -> None` (mirrors `set_org`, preserves `workspace`/`template`/`github` sections)
  - Update `set_org` to pass through the existing vault path so it isn't dropped on the next `org set`

## `rose init`

- [x] 2. `rose_cli/commands/init.py`
  - Add blank-skippable prompt: "Vault path for persistent docs (blank to skip, docs/ stays local)"
  - If non-blank: `mkdir -p`, pass to `write_config`
  - Add vault path (or "not configured") to the summary output
  - ~~Update `DOCS_SKILL_CONTENT`'s folder-resolution instructions~~ — n/a,
    that skill content block had already been removed from `init.py` before
    this task ran (no per-workspace skill file is scaffolded anymore)

## `rose vault set`

- [x] 3. Create `rose_cli/commands/vault/__init__.py` — `vault` Click group
- [x] 4. Create `rose_cli/commands/vault/set.py` — `set_vault_cmd(path)`, mirrors `org/set.py`
- [x] 5. Register `vault` group in `rose_cli/main.py`

## `rose create`

- [x] 6. `rose_cli/commands/workspace/create.py`
  - Add `_resolve_docs_target(vault_path, name, workspace_path) -> Path`
  - Add `_scaffold_docs(template_path, docs_target) -> None`
  - Change `_scaffold_template` to skip `docs/` when copying template into the workspace (now handled by `_scaffold_docs`)
  - Add `_docs_folder_entry(docs_target, workspace_path) -> dict` (relative `"docs"` when local, absolute path otherwise)
  - Wire `get_vault_path()` + the new helpers into `create()`; pass `docs_target`/`workspace_path` into `_write_code_workspace` and use `_docs_folder_entry` instead of the hardcoded literal
  - Print the resolved docs target path in the create summary (vault vs. local)

## `rose edit`

- [x] 7. `rose_cli/commands/workspace/edit.py`
  - Before rebuilding `data["folders"]`, capture the existing docs entry: `next((f for f in data.get("folders", []) if f.get("name") == "docs"), {"path": "docs", "name": "docs"})`
  - Append the captured entry instead of the hardcoded literal

## Docs

- [x] 8. Update `.cursor/skills/rose/SKILL.md` — document `rose vault set`, vault-aware `rose create` result layout, `[vault]` config block
- [x] 9. Update `README.md` — same, per `cli-docs.mdc`

## Smoke tests

- [x] 10. No vault configured: verified via direct call to `_resolve_docs_target`/`_scaffold_template`/`_scaffold_docs`/`_docs_folder_entry` — folders entry is byte-identical to pre-change output (`{"path": "docs", "name": "docs"}`), local `docs/` folder created, non-docs template content still copied to workspace root. **Not run end-to-end through the real `rose create`** (needs `gh auth` + live repos, unavailable in this environment)
- [x] 11. Vault configured: verified via the same helpers with a vault path — vault subfolder created and seeded, no local `docs/` in the workspace, folders entry has the absolute vault path with `name: "docs"`. **Not run end-to-end**
- [x] 12. Verified the `edit.py` preserve logic in isolation against a vault-style folders list — existing absolute-path entry is kept as-is. **Not run through real `rose edit`**
- [x] 13. Verified the same logic against a local-style (`"docs"`) folders list — unchanged, matches pre-change behavior. **Not run through real `rose edit`**
- [x] 14. Verified idempotency: `_scaffold_docs` uses `mkdir(exist_ok=True)` + `copytree(dirs_exist_ok=True)`, so re-running against an already-populated vault subfolder does not wipe existing files. **Not run through real `rose create` against a live vault**
