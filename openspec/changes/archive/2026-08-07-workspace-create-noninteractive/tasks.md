# Tasks: workspace-create-noninteractive

## Implementation Tasks

- [x] 1. Add `--name`, `--branch`, `--repo` (repeatable) options to `rose_cli/commands/workspace/create.py`'s `create` command signature
- [x] 2. Replace the name-prompt block with: use `--name` if given (validate pattern + target-exists, exit 1 on failure, no retry loop); otherwise keep the existing interactive `while` loop
- [x] 3. Replace the branch-prompt line with: use `--branch` if given, else `--name`/prompted name as default, else fall back to `click.prompt` as today
- [x] 4. Replace the repo-selection call with: use `--repo` values (as a list) if any were given, else call the existing `_pick_repos` picker
- [x] 5. Verify no other logic changes are needed — branch conflict check, bare clone ensure, default branch detection, scaffold, worktree creation, `.code-workspace` write, history update, and `open_cursor` all consume `name`/`branch`/`repos` the same way regardless of source
- [x] 6. Manual smoke test: `rose create --name <n> --branch <b> --repo <org/repo>` — verify zero prompts, workspace/worktrees/`.code-workspace` created identically to the interactive flow
- [x] 7. Manual smoke test: `rose create --name <n>` (no `--branch`, no `--repo`) — verify it prompts only for repos and defaults branch to `<n>` without prompting
- [x] 8. Manual smoke test: `rose create --name <n> --repo <bad/repo>` — verify clone failure is reported and exits 1, same as an interactive run with a bad search result
