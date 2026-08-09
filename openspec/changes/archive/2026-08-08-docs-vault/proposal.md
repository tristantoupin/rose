# Proposal: docs-vault

## What

Add an optional, persistent **vault** for workspace documentation: a single
folder (usable as a real Obsidian vault) that outlives any one workspace.
When a vault is configured, `rose create` gives each new workspace a
subfolder inside the vault (`<vault>/<name>/`) instead of a local `docs/`
folder, and links it into the `.code-workspace` file's `folders` array by
absolute path instead of the relative `"docs"` entry used today.

The vault is **opt-in via config**. Users who don't configure `[vault]` keep
today's behavior byte-for-byte: a local `docs/` folder scaffolded from the
template, referenced as a relative `"docs"` entry.

## Why

Today, `rose create` scaffolds a `docs/` folder *inside* the workspace
directory (`create.py:168-172`, `214`). That folder's lifecycle is tied to
the workspace: if the workspace directory is deleted or simply abandoned,
whatever findings/plans/decisions were written there go with it. There's
also no way to search, link, or backlink across the docs of different
workspaces — each one is an island.

Treating documentation as a vault (in the Obsidian sense) decouples notes
from the ephemeral workspace lifecycle: notes persist after a workspace is
torn down, and multiple workspaces' notes live in one place that can be
opened as a single Obsidian vault, searched together, and cross-linked.

## Scope

- New `[vault]` config section (`~/.rose/config.toml`), set via `rose init`
  (optional prompt, blank = skip) or `rose vault set <path>` after the fact
- `rose create`: when a vault is configured, create/reuse `<vault>/<name>/`
  and link it into the `.code-workspace` `folders` array by absolute path
  (folder `name` stays `"docs"` so existing tooling/skills still find it by
  name)
- `rose edit`: stop unconditionally rewriting the docs folder entry to the
  hardcoded relative `"docs"` value — preserve whatever entry already exists
  (fixes a bug that would otherwise silently break vault-linked workspaces,
  and is harmless for existing non-vault workspaces)
- Docs skill content (`DOCS_SKILL_CONTENT` in `init.py`): update the
  "find the docs folder" heuristic, which currently assumes the path ends in
  `/docs`, so it also matches vault-linked folders (path arbitrary, folder
  `name == "docs"`)
- Update `.cursor/skills/rose/SKILL.md` and `README.md` per this repo's
  `cli-docs.mdc` rule

## Backward Compatibility

No vault configured (default, and the state of every existing install until
someone opts in):

- `rose create` output is unchanged — same local `docs/` folder, same
  relative `"docs"` folder entry in the `.code-workspace` file
- `rose edit` output is unchanged for these workspaces (the preserved entry
  is the same relative `"docs"` value it already had)

Vault configured, existing workspaces created before the config existed:

- Untouched. Nothing rewrites a `.code-workspace` file except an explicit
  `rose edit` on that specific workspace, and the `edit.py` fix preserves
  each workspace's existing docs entry rather than resolving it fresh from
  the (now-present) vault config. Old workspaces keep their local `docs/`
  folder indefinitely; only workspaces created *after* the vault is
  configured get the vault treatment.

## Out of Scope

- Migrating existing workspaces' `docs/` folders into the vault (can be done
  by hand: move the folder, edit the `.code-workspace` entry's `path`)
- Any Obsidian-specific scaffolding (`.obsidian/` config, plugins, themes) —
  rose just creates plain folders; Obsidian owns its own config on first open
- Changing vault organization philosophy (tags/flat notes vs. folder-per-workspace)
  — this proposal keeps the folder-per-workspace model already in place today,
  just relocates it
- Deduplicating the per-workspace docs skill copy against the user's global
  `docs` skill (unrelated pre-existing redundancy)
