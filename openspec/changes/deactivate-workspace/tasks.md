# Tasks: deactivate-workspace

## Implementation Tasks

- [ ] 1. Add `worktree_status(worktree_path)` to `rose_cli/git.py` — returns `{branch, ahead, behind, modified, untracked}` using `rev-parse`, `rev-list --left-right @{upstream}...HEAD`, and `status --porcelain`
- [ ] 2. Add `remove_worktree(bare_path, worktree_path, force)` to `rose_cli/git.py` — calls `git worktree remove [--force] <path>` via `_git(bare_path, ...)`; follow with `git worktree prune` on the bare clone
- [ ] 3. Implement `rose_cli/commands/workspace/deactivate.py` — `_find_workspace` helper, safety-check loop (abort if any repo dirty and not `--force`), worktree removal loop, `shutil.rmtree(repos/)`, `.code-workspace` status update to `"inactive"`, output format per design
- [ ] 4. Register `deactivate` subcommand in `rose_cli/commands/workspace/__init__.py`
- [ ] 5. Manual smoke test: `rose workspace deactivate <name>` end-to-end on a clean workspace; verify `--force` bypasses dirty-repo block and `rose.status` is set to `"inactive"` in `.code-workspace`
