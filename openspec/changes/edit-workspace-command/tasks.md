# Tasks: edit-workspace-command

## Prerequisites

- `deactivate-workspace` must be implemented first — `git.remove_worktree()` and `git.worktree_status()` are defined there and reused here.

## Implementation Tasks

- [x] 1. Implement `rose_cli/commands/workspace/edit.py` — `_find_workspace` helper (resolve by `rose.name`, abort if inactive), `_pick_repos_for_edit` fuzzy picker pre-selecting current repos, diff logic (`added`/`removed` sets), safety-check loop for removals (reuse `git.worktree_status`), removal loop (`git.remove_worktree` + `shutil.rmtree` + `git worktree prune`), addition loop (`_ensure_bare_clones` + `git.add_worktree`), `.code-workspace` update (rebuild `folders` + `rose.repos`), output format per design
- [x] 2. Register `edit` subcommand in `rose_cli/commands/workspace/__init__.py`
- [ ] 3. Manual smoke test: `rose workspace edit <name>` — add a repo, verify worktree created and `.code-workspace` updated; remove a repo, verify worktree removed; verify `--force` bypasses dirty-repo block on removal
