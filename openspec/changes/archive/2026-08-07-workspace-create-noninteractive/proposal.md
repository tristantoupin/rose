# Proposal: workspace-create-noninteractive

## What

Add flags to `rose create` so the whole flow can run without any prompts or interactive pickers:

- `--name <name>` — workspace name (skips the name prompt)
- `--branch <branch>` — feature branch name (skips the branch prompt, still defaults to `--name` if omitted)
- `--repo <org/repo>` — repo to include; repeatable, at least one required to go non-interactive

When `--name` and at least one `--repo` are provided, `rose create` skips the name prompt, the branch prompt, and the InquirerPy fuzzy picker entirely, validates the given values with the same rules as today, and runs straight through cloning/fetching, worktree creation, `.code-workspace` writing, history update, and the Cursor launch — a single command with no TTY interaction.

## Why

The interactive picker is the right default for exploring available repos, but it blocks any scripted or automated use of `rose create` (e.g. from another tool, a Makefile target, or a batch of workspace setups) since InquirerPy's fuzzy prompt requires a TTY. Accepting the same inputs as flags lets `rose create` be driven by one non-interactive command while keeping the existing interactive flow as the default when the flags aren't given.

## Scope

- New options on the existing `rose create` command: `--name`, `--branch`, `--repo` (repeatable)
- Non-interactive branch: triggered when `--name` is set and `--repo` is given at least once
- Reuses existing validation (name pattern, target dir collision, branch conflict check) and existing helpers (`_ensure_bare_clones`, `_get_default_branches`, `_create_worktrees`, `_write_code_workspace`, `update_history`, `open_cursor`)
- `--repo` values not present in the repo cache are accepted as-is (same as search-picker results today) rather than validated against the cache
- Mixed/partial flags (e.g. `--name` without `--repo`) fall back to prompting only for the missing pieces, so the command still works as a partially-filled interactive flow

## Out of Scope

- Removing or changing the interactive picker path
- A `--yes`/`--force` flag to skip the branch-conflict abort
- Reading repo lists from a file or stdin
- Non-interactive mode for `rose edit`
