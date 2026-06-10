# Proposal: deactivate-workspace

## What

Add a `rose workspace deactivate <name>` subcommand that tears down the worktrees for an existing workspace while preserving everything needed to reactivate it later:

1. Resolves the workspace by name from the configured workspace root
2. For each repo in the workspace, checks for uncommitted or unpushed work — aborts if any repo is dirty unless `--force` is passed
3. Removes each git worktree via the corresponding bare clone
4. Deletes the `repos/` directory
5. Marks the `.code-workspace` file as `inactive` so the workspace can be reactivated later
6. Leaves the workspace directory, `docs/`, and `.code-workspace` intact

## Why

Workspaces accumulate disk space and mental overhead even when not actively being worked on. A developer context-switching to an unrelated ticket wants to stash away a long-lived feature workspace without losing branch history or docs. Deactivation gives a clean "pause" operation: worktrees gone, disk reclaimed, but the `.code-workspace` file retains all the metadata (repos, branch names, default branches) so a future `rose workspace reactivate <name>` can fully restore the workspace.

## Scope

- Single new Click subcommand: `rose workspace deactivate <name>`
- `--force` flag to skip uncommitted/unpushed safety checks
- Safety check: for each repo, abort if `modified > 0 OR untracked > 0 OR ahead > 0`
- Worktree removal via `git worktree remove` on the bare clone
- Update `.code-workspace` to set `rose.status = "inactive"`
- Remove `repos/` directory after all worktrees are pruned
- Output: per-repo status lines + final summary

## Out of Scope

- `rose workspace reactivate` — analogous command, tracked separately
- Deleting the workspace directory entirely (that would be `rose workspace delete`)
- Stashing or committing uncommitted work before deactivation
- Deactivating multiple workspaces at once
