# Proposal: workspace-edit-use-origin-feature-branch

## What

Update `rose workspace edit` repo-addition flow to use the same branch-reuse logic as `workspace create`:

1. When adding a repo to an existing workspace, check whether `origin/<feature-branch>` exists in the bare clone.
2. If remote feature branch exists, set the local branch ref to `origin/<feature-branch>` and create the worktree from there.
3. If remote feature branch does not exist, set the local branch ref to `origin/<default-branch>`.
4. Always set the local branch ref before creating the worktree so stale refs from previous removals are never a blocker.

## Why

`rose workspace edit` fails when re-adding a repo that was previously removed. When a repo is removed, `git worktree remove` deletes the worktree directory but leaves the local branch ref alive in the bare clone. On re-add, `git worktree add -b <branch>` refuses because the branch already exists.

This surfaces as:

```
  ✗  webapp: Preparing worktree (new branch 'subtask/CLIN-20197-...')
```

The fix is identical to what `workspace-create-use-origin-feature-branch` prescribes for `create.py`: resolve `source_ref` (preferring the remote feature branch), force-set the local branch ref, then add the worktree on the existing branch. The shared git helpers from that change are reused here.

## Scope

- `rose_cli/git.py`
  - `add_worktree`: drop `from_ref` parameter — callers now set the branch ref before calling this.
  - Reuse `remote_branch_exists` and `set_branch_to_ref` added by `workspace-create-use-origin-feature-branch`.
- `rose_cli/commands/workspace/edit.py`
  - Replace hardcoded `from_ref = f"origin/{default_br}"` with per-repo source ref resolution.
  - Call `set_branch_to_ref` before `add_worktree` to handle stale local branch refs.
  - Update console output to show which source ref was used per repo.
- `rose_cli/commands/workspace/create.py`
  - Update call site to match new `add_worktree` signature (no `from_ref`).

## Out of Scope

- Behavior of `rose workspace create` branch resolution (covered by `workspace-create-use-origin-feature-branch`).
- Deleting local branch refs on repo removal.
- Changing the workspace branch after creation.
