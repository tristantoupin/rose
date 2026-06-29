# Tasks: workspace-create-use-origin-feature-branch

## Implementation Tasks

- [ ] 1. Add git helper(s) in `rose_cli/git.py` to detect `origin/<branch>` existence and set/reset local branch ref to a chosen source ref.
- [ ] 2. Update `rose_cli/commands/workspace/create.py` to remove local branch conflict abort and resolve per-repo source ref with rule: prefer `origin/<feature>` else `origin/<default>`.
- [ ] 3. Update worktree creation flow to ensure local branch points at resolved source ref before adding worktree.
- [ ] 4. Update CLI output in workspace create to print chosen source ref per repo.
- [ ] 5. Manual validation:
  - Case A: remote feature branch exists; verify workspace branch starts at `origin/<feature>`.
  - Case B: remote feature branch missing; verify workspace branch starts at `origin/<default>`.
  - Case C: stale local branch ref exists in bare clone; verify workspace still bootstraps from latest remote source ref.
