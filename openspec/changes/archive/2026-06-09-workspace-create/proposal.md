# Proposal: workspace-create

## What

Add a `rose workspace create` command that sets up a full multi-repo development workspace in one step. The command:

1. Prompts for a workspace name (becomes the folder name and default branch name)
2. Lets the user select repos via an interactive fuzzy autocomplete picker (sourced from a local cache built from the configured GitHub org)
3. Prompts for a feature branch name (defaults to workspace name)
4. Ensures bare clones exist in `~/.rose/repos/` for each selected repo (clones if missing, fetches if stale)
5. Creates a worktree for each repo branching off the repo's default branch
6. Scaffolds the workspace folder from the configured template
7. Writes a `<name>.code-workspace` file with folder paths and rose metadata
8. Opens the workspace in Cursor

Also adds:
- `rose org set <orgname>` — update GitHub org in config and rebuild repo cache
- `rose repos sync` — rebuild the repo cache from the configured org
- Org prompt added to `rose init` + initial cache build during init

## Why

The core value of Rose is eliminating the manual overhead of setting up multi-repo feature environments. Today a developer must manually clone repos, create branches, wire up a Cursor workspace file, and copy shared config. This command collapses that to a single interactive flow taking under a minute.

## Scope

- New Click group: `rose workspace` with subcommand `create`
- New Click group: `rose org` with subcommand `set`
- New Click command: `rose repos sync`
- Updated `rose init`: adds org prompt + initial cache build
- Updated config schema: new `[github]` section with `org` key
- New cache files: `~/.rose/repo-cache.json`, `~/.rose/history.json`
- New bare clone pool: `~/.rose/repos/`
- New dependency: `InquirerPy` (fuzzy interactive picker)

## Out of Scope

- Per-repo branch overrides (all repos share one branch name)
- `rose workspace list`, `rose workspace delete` (future)
- Non-GitHub repo sources
- Windows support (bare clone + worktree paths assume POSIX)
