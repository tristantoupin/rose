# Proposal: edit-workspace-command

## What

Add a `rose workspace edit <name>` subcommand that lets a developer mutate the repo set of an existing active workspace:

1. Resolves the workspace by name from the configured workspace root
2. Opens a fuzzy multi-select picker pre-populated with the workspace's current repos
3. Diffs the selection against the current state to determine **added** and **removed** repos
4. For each **added** repo: ensures a bare clone, creates a new worktree on the existing workspace branch, adds it to the `.code-workspace`
5. For each **removed** repo: safety-checks for uncommitted/unpushed work, removes the worktree, deletes `repos/<short>`, removes it from the `.code-workspace`
6. Opens the updated workspace in Cursor

## Why

After creating a workspace, the set of repos a developer needs to work on often changes — a ticket expands to an adjacent service, or a repo turns out to be unnecessary. Today the only options are to tear down the workspace and recreate it or manually clone worktrees. `workspace edit` closes this gap as the "day two" mutation command for an active workspace.

## Scope

- Single new Click subcommand: `rose workspace edit <name>`
- `--force` flag to skip uncommitted/unpushed safety checks on removed repos
- Workspace resolution: walk workspace root, match `rose.name`; abort on inactive workspace
- Picker: pre-selects current repos; user adds/removes freely
- Added repos: `_ensure_bare_clones` → `_create_worktrees` on existing branch
- Removed repos: safety check (same logic as `deactivate`) → `remove_worktree` → `shutil.rmtree(repos/<short>)` → update `.code-workspace`
- `.code-workspace` updated: `folders` list and `rose.repos` dict kept in sync
- Opens updated workspace in Cursor

## Out of Scope

- Renaming the workspace or changing the branch
- Editing an inactive workspace (use `reactivate` first)
- Bulk editing multiple workspaces at once
- Removing all repos (must keep at least one)
