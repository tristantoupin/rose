# Proposal: workspace-create-use-origin-feature-branch

## What

Update `rose workspace create` branch bootstrap behavior so selected feature branch prefers remote branch state when it exists:

1. Keep prompting for `Feature branch name` as today.
2. For each selected repo, after fetch, check whether `origin/<feature-branch>` exists.
3. If remote feature branch exists, create workspace worktree from `origin/<feature-branch>` so local branch starts from latest remote commits.
4. If remote feature branch does not exist, keep current fallback behavior: create local branch from `origin/<default-branch>`.

## Why

Current flow always seeds from default branch and blocks when branch name already exists locally in bare clone. That prevents common workflow where developer wants to continue an existing remote feature branch and guarantees drift from latest remote work. New behavior aligns workspace creation with real team flow: reuse current remote feature branch when available.

## Scope

- `rose_cli/commands/workspace/create.py`
  - Replace branch-conflict gate with remote-aware branch resolution.
  - Build worktrees from per-repo source ref (`origin/<feature>` or `origin/<default>`).
- `rose_cli/git.py`
  - Add helper(s) to detect remote-tracking branch existence in bare clone.
  - Add helper(s) to create/reset local branch to chosen start point when needed.
- Console output updates to show per-repo source ref used.

## Out of Scope

- Changing workspace branch after creation.
- New interactive prompts for branch policy.
- Automatic push of newly created local branches.
- Behavior changes in `rose workspace edit` (unless needed for shared helper reuse only).
