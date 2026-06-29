# Tasks: workspace-edit-use-origin-feature-branch

## Implementation Tasks

- [ ] 1. Update `add_worktree` in `rose_cli/git.py` to drop `from_ref` parameter — use `git worktree add <path> <branch>` (no `-b`) since callers set the branch ref beforehand.
- [ ] 2. Update `_create_worktrees` in `rose_cli/commands/workspace/create.py` to match new `add_worktree` signature (call `set_branch_to_ref` then `add_worktree` without `from_ref`). Depends on `workspace-create-use-origin-feature-branch` task 1–3.
- [ ] 3. Update addition loop in `rose_cli/commands/workspace/edit.py`:
  - Compute `source_ref`: prefer `origin/<branch>` if `remote_branch_exists`, else `origin/<default_br>`.
  - Call `set_branch_to_ref(bare_path, branch, source_ref)` before `add_worktree`.
  - Call `add_worktree(bare_path, worktree_path, branch)` (no `from_ref`).
  - Print `source: <source_ref>` per repo.
- [ ] 4. Manual validation:
  - Case A: create workspace (repo1, repo2) → edit remove repo2 → edit add repo2. Verify re-add succeeds and uses `origin/<branch>` if it exists remotely.
  - Case B: edit add repo that never had a local branch in bare clone. Verify fallback to `origin/<default>`.
  - Case C: attempt to add a repo whose branch is checked out in another active workspace. Verify git refuses with a clear error.
