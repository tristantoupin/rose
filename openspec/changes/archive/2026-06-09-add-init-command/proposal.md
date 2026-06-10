# Proposal: add-init-command

## What

Add a `rose init` command that bootstraps a new Rose environment on the user's machine. The command:

1. Prints a Rose ASCII art greeting
2. Verifies GitHub CLI (`gh`) authentication
3. Prompts for workspace path (where worktrees will be created) and creates it
4. Prompts for template path (folder copied into every new workspace) and scaffolds a default template if the path doesn't exist
5. Persists all answers to `~/.rose/config.toml`

## Why

Rose has no setup flow. Users need a way to configure where worktrees live and what starter files (rules, skills, docs) each workspace gets. Without `init`, every other workspace-related command would need to ask these questions or fail with missing config.

## Scope

- Single new Click command: `rose init`
- Config file: `~/.rose/config.toml`
- Default template scaffold: `~/.rose/templates/default/` with docs skill + empty docs folder
- GitHub CLI auth check (warn, don't block)
- Re-run behavior: warn if config exists, allow overwrite

## Out of Scope

- Workspace creation commands (future)
- Config editing commands (`rose config set`, etc.)
- Multiple template support
- Any other CLI commands
