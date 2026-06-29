# Design: workspace-create-use-origin-feature-branch

## Goal

When user selects feature branch during `rose workspace create`, each repo should start from latest `origin/<feature-branch>` if it exists. If missing, repo should start from `origin/<default-branch>`.

## Current Gap

- `_check_branch_conflicts` aborts when local branch name already exists in bare clone.
- `_create_worktrees` always seeds from `origin/<default-branch>`.
- Result: existing remote feature branch is not used.

## Target Behavior

For each selected repo during workspace creation:

1. Fetch/prune bare clone (`origin/*` up to date).
2. Resolve source ref:
   - If `origin/<feature>` exists, source ref = `origin/<feature>`.
   - Else source ref = `origin/<default-branch>`.
3. Ensure local branch `<feature>` points at source ref.
4. Add worktree on branch `<feature>`.

## Branch Resolution Table

| Condition | Source ref | Expected outcome |
| --- | --- | --- |
| `origin/<feature>` exists | `origin/<feature>` | Workspace starts from latest feature branch commits |
| `origin/<feature>` missing | `origin/<default>` | Workspace creates new feature branch from default branch |

## Git Helper Changes

Add helper(s) in `rose_cli/git.py`:

- `remote_branch_exists(bare_path, branch_name) -> bool`
  - Implementation: query `refs/remotes/origin/<branch_name>`.
- `branch_exists_local(bare_path, branch_name) -> bool`
  - Existing `branch_exists` already does this; can rename or keep.
- `set_branch_to_ref(bare_path, branch_name, source_ref) -> None`
  - Force local branch ref to source ref before creating worktree.
  - Use non-interactive git plumbing safe for bare repo workflow.

## Create Command Changes

### 1) Remove conflict gate

Delete `_check_branch_conflicts` call in command flow; it blocks valid remote-branch reuse scenario.

### 2) Compute per-repo source refs

In worktree creation loop, derive:

- `feature_ref = f"origin/{branch}"`
- `default_ref = f"origin/{default_branch}"`
- `source_ref = feature_ref if remote_branch_exists(...) else default_ref`

### 3) Normalize local branch ref

Before `git worktree add`, update local branch `<branch>` to `source_ref` so existing stale local branch does not prevent checkout.

### 4) Create worktree from branch

Keep final worktree branch name as user-entered `branch`.

## Logging / UX

Per repo output should make source clear:

- `source: origin/<feature>` when remote feature exists.
- `source: origin/<default>` otherwise.

This gives visible confirmation that workspace uses latest remote feature branch when present.

## Risks and Mitigations

- Risk: Local branch ref gets rewritten.
  - Mitigation: only mutate bare-cache branch refs (`~/.rose/repos/...`), not user working tree.
- Risk: Fetch failure yields stale decision.
  - Mitigation: keep existing hard failure behavior for clone/fetch errors before worktree creation.
