## Why

`rose create` already supports a fully non-interactive one-liner (`--name`/`--branch`/`--repo`) so agents and scripts can set up a workspace with no TTY. `rose workspace edit` has no equivalent: changing an existing workspace's repo set always opens an InquirerPy fuzzy multiselect, which requires a TTY and blocks agent/scripted use entirely.

## What Changes

- Add a repeatable `--repo <org/repo>` option to `rose workspace edit <name>`.
- When `--repo` is given (one or more times), `edit` skips the fuzzy picker and treats the full set of `--repo` values as the **desired end state** for the workspace — not an additive list. Repos already in the workspace that are omitted from `--repo` are removed; repos in `--repo` not already present are added; repos in both are left untouched.
- Because the flag expresses the full desired set, the caller must re-specify every repo they want to keep, including ones already in the workspace — matching how `--repo` works for `rose create`.
- Existing diff, safety-check (uncommitted/unpushed guard, `--force`), worktree add/remove, and `.code-workspace` update logic are reused unchanged; only how `new_repos` is obtained changes.
- Without `--repo`, `rose workspace edit` behaves exactly as today (interactive picker, pre-selected with current repos).

## Capabilities

### New Capabilities

- `workspace-edit-noninteractive`: non-interactive repo-set editing for `rose workspace edit` via a repeatable `--repo` flag that specifies the complete desired repo set.

### Modified Capabilities

(none — no existing spec covers `rose workspace edit`; this introduces its non-interactive mode as a new capability rather than modifying a prior spec)

## Impact

- `rose_cli/commands/workspace/edit.py`: new `--repo` option on the `edit` command; branch to skip `_pick_repos_for_edit` when `--repo` is given.
- `.cursor/skills/rose/SKILL.md` and `README.md`: document the new flag and mark `rose edit` as agent-friendly when `--repo` is used.
- No changes to `create.py`, `git.py`, or `.code-workspace` schema.
