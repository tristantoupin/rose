# Tasks: workspace-create

## Implementation Tasks

### Infrastructure

- [x] 1. Add `InquirerPy>=0.3.4` to `pyproject.toml` dependencies
- [x] 2. Create `rose_cli/cache.py` — helpers for `repo-cache.json` and `history.json` (load, save, check freshness, update history)
- [x] 3. Create `rose_cli/git.py` — helpers: bare clone path derivation, `git clone --bare`, `git fetch --prune`, `git branch --list`, `git worktree add`, SSH URL fetch via `gh repo view`
- [x] 4. Create `rose_cli/github.py` — `gh` CLI wrappers: `repo_list(org)`, `repo_view(name)`, `search_repos(term, org)`, `default_branch(name)`
- [x] 5. Update `rose_cli/config.py` — add `[github]` section read/write (`get_org`, `set_org`)

### Command scaffolding

- [x] 6. Create `rose_cli/commands/workspace/__init__.py` — `workspace` Click group
- [x] 7. Create `rose_cli/commands/org/__init__.py` — `org` Click group
- [x] 8. Create `rose_cli/commands/repos/__init__.py` — `repos` Click group
- [x] 9. Register all three groups in `rose_cli/main.py`

### `rose org set`

- [x] 10. Implement `rose_cli/commands/org/set.py` — update `[github].org` in config, rebuild cache via `github.repo_list`, print summary

### `rose repos sync`

- [x] 11. Implement `rose_cli/commands/repos/sync.py` — read org from config, rebuild cache via `github.repo_list`, print summary

### `rose init` updates

- [x] 12. Add org prompt to `rose_cli/commands/init.py` after template prompt
- [x] 13. Add initial cache build to `init` after org prompt (calls same logic as `repos sync`)

### `rose workspace create`

- [x] 14. Implement config/cache load + validation (org present, workspace path writable)
- [x] 15. Implement workspace name prompt + validation (non-empty, safe chars, target dir doesn't exist)
- [x] 16. Implement branch name prompt (default = workspace name)
- [x] 17. Implement InquirerPy fuzzy multiselect (★ recent first, "Not there?" as last entry)
- [x] 18. Implement "Not there?" flow — prompt search term, call `github.search_repos`, show secondary picker, merge selections, update cache
- [x] 19. Implement branch conflict check (iterate repos, check bare clone branch list, abort with message if conflict)
- [x] 20. Implement bare clone ensure + fetch (clone if missing, fetch if exists, show per-repo progress)
- [x] 21. Implement default branch detection per repo via `github.default_branch`
- [x] 22. Implement workspace folder creation + template scaffold (`shutil.copytree`)
- [x] 23. Implement `git worktree add` per repo with progress output
- [x] 24. Implement `.code-workspace` file writer (JSON with `rose` metadata key)
- [x] 25. Implement history update (prepend selected repos, dedup, trim to 20)
- [x] 26. Implement Cursor launch (`shutil.which("cursor")` → `subprocess.Popen`, warn if not found)
- [x] 27. Wire all steps into `rose_cli/commands/workspace/create.py` with summary output

### Smoke tests

- [ ] 28. Manual smoke test: `rose init` — verify org prompt + cache build
- [ ] 29. Manual smoke test: `rose org set <org>` — verify config update + cache rebuild
- [ ] 30. Manual smoke test: `rose repos sync` — verify cache file written
- [ ] 31. Manual smoke test: `rose workspace create` — end-to-end with 2 repos, verify folder structure, worktrees, `.code-workspace`, Cursor launch
