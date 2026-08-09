## 1. CLI flag

- [x] 1.1 Add repeatable `--repo` option (`multiple=True`) to the `edit` command signature in `rose_cli/commands/workspace/edit.py`
- [x] 1.2 Replace the unconditional `_pick_repos_for_edit(...)` call with: use `list(repo_opt)` as `new_repos` if `repo_opt` is non-empty, else call `_pick_repos_for_edit(...)` as today
- [x] 1.3 Verify no other logic changes are needed — diff (`added`/`removed`), safety check, removal loop, addition loop, and `.code-workspace` rewrite all consume `new_repos` the same way regardless of source
- [x] 1.4 Confirm `_check_removal_safety(workspace_dir, removed, force)` still runs before any removal when `removed` is derived from `--repo` (i.e. the safety check is not accidentally skipped in the new code path)

## 2. Documentation

- [x] 2.1 Update `.cursor/skills/rose/SKILL.md`: document `--repo` on `rose edit`, mark it agent-friendly when `--repo` is used, and add an example showing that existing repos must be re-listed to be kept
- [x] 2.2 Update `README.md` to reflect the same `--repo` flag and full-set semantics

## 3. Manual verification

- [x] 3.1 Smoke test: `rose workspace edit <name> --repo org/api --repo org/web` where the workspace already has exactly those two repos — verify no prompt, "No changes." output
- [x] 3.2 Smoke test: `rose workspace edit <name> --repo org/api --repo org/new-repo` where the workspace currently has `org/api` and `org/web` — verify `org/web` is removed and `org/new-repo` is added, no prompt shown
- [x] 3.3 Smoke test: `rose workspace edit <name>` with no `--repo` — verify the interactive picker still opens pre-selected with current repos, unchanged from before this change
- [x] 3.4 Smoke test: dirty-worktree block — make an uncommitted change in a repo, run `rose workspace edit <name> --repo <other-repo-only>` (omitting the dirty one) without `--force` — verify it prints the "Cannot remove repos — they have uncommitted or unpushed work" error, exits 1, and leaves the worktree/`.code-workspace` untouched; re-run with `--force` and verify it removes it
