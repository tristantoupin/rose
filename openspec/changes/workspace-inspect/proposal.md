# Proposal: workspace-inspect

## What

Add a `rose workspace inspect <name>` subcommand that prints a detailed snapshot of a single workspace:

1. Resolves the workspace by name from the configured workspace root
2. Reads `rose` metadata from the `.code-workspace` file (name, created date, repos map)
3. For each repo worktree: shows current branch, upstream, and dirty state (modified/untracked files)
4. Displays docs folder contents (top-level `.md` files)

## Why

`rose workspace create` and `rose workspace list` cover creation and selection. Once a workspace exists there is no quick way to assess its state without `cd`-ing into each worktree and running `git status` manually. The `inspect` command gives a single-pane view so a developer can re-orient after context switching — which repos are touched, which branches are ahead/behind, what docs were written.

## Scope

- Single new Click subcommand: `rose workspace inspect <name>`
- Accepts workspace name as an argument; errors clearly if not found
- Optional `--no-git` flag to skip per-repo git queries (for speed when only metadata is needed)
- Output sections:
  - **Header**: workspace name + path + created date
  - **Repos**: table of repo → branch → ahead/behind origin → dirty indicator (M/? counts)
  - **Docs**: list of `.md` files in the workspace `docs/` folder (filename + first heading)

## Out of Scope

- Launching/opening the workspace (that's `rose workspace list`)
- Editing or deleting workspaces
- Deep git log or diff output
- Recursive docs scanning (top-level only)
