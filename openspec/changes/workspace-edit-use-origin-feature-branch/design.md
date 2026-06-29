# Design: workspace-edit-use-origin-feature-branch

## Problem

`git worktree remove` leaves local branch refs in the bare clone. When `rose workspace edit` re-adds a repo, `git worktree add -b <branch> <from_ref>` fails because the branch already exists:

```
  ✗  webapp: Preparing worktree (new branch 'subtask/CLIN-20197-...')
```

## Root Cause

```
edit: remove repo
  └─ git worktree remove <path>   → worktree directory deleted
     git worktree prune           → stale registry entry pruned
                                    refs/heads/<branch> SURVIVES in bare clone

edit: add repo (same workspace branch)
  └─ git worktree add -b <branch> origin/main
                      ^^
                      fails: branch already exists
```

## Target Behavior

For each repo added via `rose workspace edit`:

1. After fetch (already done by `_ensure_bare_clones`), resolve source ref:
   - If `origin/<branch>` exists → `source_ref = origin/<branch>`
   - Else → `source_ref = origin/<default_branch>`
2. Force-set local branch to `source_ref` (create or reset).
3. Add worktree on the existing branch (no `-b` flag needed).

## Branch Resolution Table

| Condition | Source ref | Outcome |
| --- | --- | --- |
| `origin/<branch>` exists | `origin/<branch>` | Worktree starts at latest remote feature commits |
| `origin/<branch>` missing | `origin/<default>` | New feature branch created from default branch |
| Stale local branch exists | Either (reset) | Stale ref overwritten; worktree add succeeds |
| Branch checked out elsewhere | — | `git worktree add` refuses natively; error surfaced |

## Git Helper Changes (`rose_cli/git.py`)

### Reused from `workspace-create-use-origin-feature-branch`

- `remote_branch_exists(bare_path, branch_name) -> bool`
- `set_branch_to_ref(bare_path, branch_name, source_ref) -> None`

### Modified

**`add_worktree`** — drop `from_ref` parameter:

```python
# Before
def add_worktree(bare_path, worktree_path, branch, from_ref) -> None:
    _git(bare_path, "worktree", "add", str(worktree_path), "-b", branch, from_ref)

# After
def add_worktree(bare_path, worktree_path, branch) -> None:
    _git(bare_path, "worktree", "add", str(worktree_path), branch)
```

Callers always call `set_branch_to_ref` before `add_worktree`, so the branch is guaranteed to exist at the right commit. The `-b` flag is no longer needed.

## Edit Command Changes (`rose_cli/commands/workspace/edit.py`)

### Addition loop — before

```python
from_ref = f"origin/{default_br}"
git.add_worktree(bare_path, worktree_path, branch, from_ref)
```

### Addition loop — after

```python
feature_ref = f"origin/{branch}"
default_ref = f"origin/{default_br}"
source_ref = feature_ref if git.remote_branch_exists(bare_path, branch) else default_ref
git.set_branch_to_ref(bare_path, branch, source_ref)
git.add_worktree(bare_path, worktree_path, branch)
```

## Create Command Changes (`rose_cli/commands/workspace/create.py`)

`_create_worktrees` call site update only — signature change to `add_worktree`:

```python
# Before
git.add_worktree(bare_path, worktree_path, branch, from_ref)

# After
git.set_branch_to_ref(bare_path, branch, source_ref)   # already computed above
git.add_worktree(bare_path, worktree_path, branch)
```

(The `source_ref` computation in `_create_worktrees` is part of `workspace-create-use-origin-feature-branch`. This change only updates the call signature.)

## Logging / UX

Per-repo output for additions in `edit`:

```
  Adding repos...
  Preparing webapp...
    source: origin/subtask/CLIN-20197-visit-link-header
  ✓  webapp               added → subtask/CLIN-20197-visit-link-header

  Preparing api...
    source: origin/main
  ✓  api                  added → subtask/CLIN-20197-visit-link-header
```

## Risks and Mitigations

- Risk: Force-resetting local branch ref loses commits that existed there.
  - Mitigation: bare clone branches are throw-away cache refs. User work lives in worktree directories. Worktree removal already discards the directory; resetting the bare ref on re-add is consistent.
- Risk: Branch checked out in another worktree gets clobbered.
  - Mitigation: `git worktree add <path> <branch>` (without `-b`) natively refuses if the branch is currently checked out elsewhere. Error propagates to the user unchanged.
- Risk: `set_branch_to_ref` created before `add_worktree` but `add_worktree` fails.
  - Mitigation: bare clone ref is updated but no worktree exists yet; user can retry safely.

## Dependency

This change depends on `workspace-create-use-origin-feature-branch` for `remote_branch_exists` and `set_branch_to_ref`. Both changes can be implemented together; the helpers are created once.
