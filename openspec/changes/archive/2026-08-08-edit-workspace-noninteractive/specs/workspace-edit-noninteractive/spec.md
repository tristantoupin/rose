## ADDED Requirements

### Requirement: Non-interactive repo-set editing via `--repo`
`rose workspace edit <name>` SHALL accept a repeatable `--repo <org/repo>` option. When one or more `--repo` values are given, the command SHALL skip the interactive fuzzy picker and use the given values as the complete desired repo set for the workspace, diffing them against the workspace's current repos to compute additions and removals exactly as it does with picker output today.

#### Scenario: Full repo set given via `--repo`, no changes
- **WHEN** `rose workspace edit my-feature --repo org/api --repo org/web` is run and the workspace already contains exactly `org/api` and `org/web`
- **THEN** the command reports no changes and exits 0 without prompting

#### Scenario: `--repo` set adds a repo
- **WHEN** the workspace currently contains `org/api` and the command is run with `--repo org/api --repo org/web`
- **THEN** `org/web` is added (bare clone ensured, worktree created on the workspace's existing branch) and `org/api` is left untouched, with no interactive prompt shown

#### Scenario: `--repo` set omits an existing repo
- **WHEN** the workspace currently contains `org/api` and `org/web`, and the command is run with `--repo org/api` only
- **THEN** `org/web` is treated as removed (subject to the existing uncommitted/unpushed safety check and `--force` behavior) and `org/api` is left untouched

### Requirement: Removal via `--repo` is blocked by uncommitted or unpushed work
When a repo omitted from `--repo` (and therefore marked for removal) has uncommitted, untracked, or unpushed changes in its worktree, the command SHALL raise an error and exit non-zero without removing that repo's worktree, exactly as the interactive removal path does today. The command SHALL only proceed with that removal if `--force` is given.

#### Scenario: Omitted repo has uncommitted changes, no `--force`
- **WHEN** the workspace currently contains `org/api` and `org/web`, `org/web`'s worktree has modified or untracked files, and the command is run with `--repo org/api` only (omitting `org/web`) without `--force`
- **THEN** the command prints the existing "Cannot remove repos — they have uncommitted or unpushed work" error listing `org/web` and exits 1, leaving `org/web`'s worktree and the `.code-workspace` file unchanged

#### Scenario: Omitted repo has uncommitted changes, with `--force`
- **WHEN** the same setup as above is run with `--repo org/api --force`
- **THEN** `org/web` is removed anyway (worktree deleted, dropped from `.code-workspace`), matching the existing `--force` behavior for interactive removals

#### Scenario: No `--repo` given
- **WHEN** `rose workspace edit my-feature` is run without any `--repo` option
- **THEN** the command behaves exactly as before: it opens the interactive fuzzy picker pre-selected with the workspace's current repos

#### Scenario: `--repo` value not in the cached repo list
- **WHEN** a `--repo` value is given that does not appear in the cached repo list for the configured org
- **THEN** the command accepts it as-is (no membership validation) and attempts to clone/add it via the existing addition flow, surfacing the existing clone-failure error and exiting 1 if it cannot be cloned
