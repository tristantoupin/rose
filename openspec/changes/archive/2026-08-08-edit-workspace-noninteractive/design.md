## Context

`rose_cli/commands/workspace/edit.py` implements `rose workspace edit <name>` by resolving the workspace, then always calling `_pick_repos_for_edit(all_repos, current_repos, org)` — an InquirerPy fuzzy multiselect pre-selected with `current_repos`. The resulting `new_repos` list is diffed against `current_repos` to compute `added`/`removed`, which drive worktree creation/removal and the `.code-workspace` rewrite.

`rose_cli/commands/workspace/create.py` already has the equivalent one-liner pattern: `repos = list(repo_opt) if repo_opt else _pick_repos(all_repos, org)`. `edit` should follow the same shape, with one difference: `create`'s `--repo` list *is* the repo set (there's no prior state), while `edit`'s `--repo` list must replace `current_repos` as the desired end state — so a caller who wants to keep an existing repo must list it again.

## Goals / Non-Goals

**Goals:**
- Add `--repo <org/repo>` (repeatable) to `rose workspace edit`.
- When given, treat the flag's values as the complete desired repo set — skip the picker entirely, no merge/append behavior.
- Reuse all existing diff, safety-check, worktree, and `.code-workspace` logic unchanged.
- Keep the interactive path (no `--repo`) byte-for-byte identical to today.

**Non-Goals:**
- No `--add-repo`/`--remove-repo` incremental flags — only whole-set replacement, matching `create`'s `--repo` semantics.
- No change to `--force`, workspace resolution, or cwd-inference behavior.
- No validation of `--repo` values against the repo cache (same as `create`: unknown repos are attempted as-is and fail naturally in `_ensure_bare_clones`).
- Not addressing `rose list`'s picker (out of scope, per the proposal).

## Decisions

**`--repo` replaces rather than appends.** The proposal explicitly asks for "full set" semantics so `edit --repo` mirrors `create --repo`'s mental model (a `--repo` list *is* the resulting repo set), rather than introducing a second, additive meaning for the same flag name across two commands. Alternative considered: making `--repo` additive-only with a separate `--remove` flag — rejected because it's a different UX than `create` and adds a second flag surface for one behavior.

**No minimum-one-repo enforcement beyond what already exists.** `edit` has no explicit "must keep ≥1 repo" check today (only `create`'s picker validator enforces "select at least one"). For `--repo`, an empty result (`--repo` never passed) simply falls through to the existing picker; if `--repo` is passed with all current repos omitted and none re-added... that's just a normal `removed`-only diff, already handled by existing removal logic. No new guard needed.

**Implementation shape mirrors `create.py` exactly:**
```python
new_repos = list(repo_opt) if repo_opt else _pick_repos_for_edit(all_repos, current_repos, org)
```
placed where the current unconditional `_pick_repos_for_edit(...)` call is. Everything downstream (`current_set`/`new_set` diff, safety check, removal loop, addition loop, `.code-workspace` rewrite) consumes `new_repos` identically regardless of source — no other line changes.

**Repo cache fetch stays unconditional.** `edit` today always ensures the repo cache before picking, even though `--repo` (like `create`'s) doesn't need it for validation. Leaving this as-is keeps the diff minimal — `all_repos` is still used by the picker branch, and skipping the fetch only in the `--repo` branch would add a conditional for a network call that already tolerates being cached/cheap.

## Risks / Trade-offs

- **[Risk]** A caller passes `--repo` with only the repos they want to *add*, forgetting existing ones, and unintentionally removes everything else → **Mitigation**: this is the explicitly requested behavior (matches `create`'s "one-liner has full set" model) and is documented clearly in the skill/README with an example showing re-listing existing repos. `_check_removal_safety` (unchanged) is the backstop against silent data loss — see next risk.
- **[Risk]** A repo omitted from `--repo` (and thus marked for removal) has uncommitted or unpushed work → **Mitigation**: not a new risk to mitigate, but a hard requirement to preserve: `edit.py` already calls `_check_removal_safety(workspace_dir, removed, force)` before touching any worktree, regardless of whether `removed` came from the picker or `--repo`. It raises the existing "Cannot remove repos — they have uncommitted or unpushed work" error and exits 1 unless `--force` is passed. Because `--repo` feeds into the same `removed` list, this guard applies unchanged — no new code needed, just verify it isn't bypassed when adding the `--repo` branch.
- **[Risk]** Removing all repos via `--repo` omission of everything, without an explicit guard → **Mitigation**: none added, since no such guard exists in the interactive path today either (out of scope per proposal; behavior is unchanged from what removal safety-checks already allow).

## Migration Plan

Additive CLI flag; no data migration. Existing `rose workspace edit <name>` invocations without `--repo` are unaffected.
