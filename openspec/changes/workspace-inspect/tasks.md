# Tasks: workspace-inspect

## Implementation Tasks

### Git helper

- [ ] 1. Add `worktree_status(worktree_path: Path) -> dict` to `rose_cli/git.py`
  - `branch` via `git rev-parse --abbrev-ref HEAD`
  - `ahead`/`behind` via `git rev-list --count --left-right @{upstream}...HEAD` (0/0 if no upstream)
  - `modified`/`untracked` counts via `git status --porcelain`

### Command

- [ ] 2. Create `rose_cli/commands/workspace/inspect.py`
  - `_find_workspace(workspace_path, name)` — walk workspace root, match `rose.name`, return `(ws_dir, rose_meta)` or exit 1
  - `_first_heading(md_path)` — extract first `# ` line from a markdown file
  - `inspect` Click command with `<name>` arg and `--no-git` flag
  - Header section (name, path, created)
  - Repos table (repo → branch → ↑↓ → dirty) unless `--no-git`
  - Docs section (`.md` files in `docs/`, first heading)
  - Legend line when any repo has dirty state

- [ ] 3. Register `inspect` in `rose_cli/commands/workspace/__init__.py`

### Smoke tests

- [ ] 4. Manual smoke test: `rose workspace inspect <name>` on a workspace with dirty and clean repos
- [ ] 5. Manual smoke test: `rose workspace inspect <name> --no-git` — verify git rows skipped
- [ ] 6. Manual smoke test: `rose workspace inspect nonexistent` — verify clean error message
