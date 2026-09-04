# Proposal: add-codex-app-support

## What

Make Rose support Codex Desktop alongside Cursor as a configurable workspace application:

1. Add an `[app]` configuration section whose `name` is either `cursor` or `codex`.
2. Prompt for the application during `rose init`, defaulting to Cursor for backward compatibility.
3. Add `rose app set <cursor|codex>` so users can change the global application later.
4. Replace the Cursor-only workspace launcher with an application-aware launcher:
   - Cursor: `cursor <workspace>.code-workspace`
   - Codex: `codex app <workspace-directory>`
5. Keep `.code-workspace` as Rose's workspace metadata and Cursor workspace file. Codex opens the containing workspace directory and ignores the file.
6. Make `.agents/skills` the canonical repository skill directory and expose it to Cursor through a `.cursor/skills` alias.
7. Consolidate durable agent instructions in `AGENTS.md` and remove the redundant `.cursor/rules` files.
8. Update user-facing and agent-facing documentation for both applications.

## Why

Rose currently assumes every user works in Cursor. Workspace creation, editing, and selection always invoke the `cursor` executable; configuration cannot express another application; and the repository's skills and durable instructions are stored under Cursor-specific paths.

Codex Desktop can open the Rose workspace directory directly, which gives it access to the shared docs and every repository worktree. Supporting it as a first-class application lets users keep the same Rose workspace workflow while choosing Cursor or Codex during initialization and changing that choice later.

Moving shared skills and instructions to `.agents` and `AGENTS.md` also makes the agent guidance reusable by Codex, Cursor, Claude, and other compatible tools without maintaining divergent copies.

## Scope

- Configuration:
  - Add `[app].name` with valid values `cursor` and `codex`.
  - Treat a missing `[app]` section as `cursor`.
  - Materialize `[app] name = "cursor"` the next time a legacy configuration is rewritten.
  - Preserve the application when organization or vault settings change.
- Initialization:
  - Prompt for Cursor or Codex, with Cursor as the default.
  - Warn without blocking when the selected executable is unavailable.
  - Include the selected application in the initialization summary.
- CLI:
  - Add `rose app set <cursor|codex>`.
  - Require an existing Rose configuration before changing the application.
  - Warn without blocking when the selected executable is unavailable.
- Workspace workflows:
  - Continue automatically opening workspaces after `rose create`, `rose edit`, and `rose list`.
  - Open Cursor with the `.code-workspace` file.
  - Open Codex Desktop with the Rose workspace root.
  - Print the exact manual launch command when the configured executable is unavailable.
- Agent integration:
  - Move all repository skills from `.cursor/skills` to canonical `.agents/skills`.
  - Make `.cursor/skills` an alias to `.agents/skills`.
  - Merge the existing Cursor rule content into `AGENTS.md` and remove `.cursor/rules`.
- Documentation:
  - Update `README.md` and the Rose skill with application setup, switching, requirements, launch behavior, paths, and agent workflows.

## Out of Scope

- Codex terminal/TUI launching.
- Per-workspace application overrides; the application remains a global Rose setting.
- Replacing `.code-workspace` with a new app-neutral workspace manifest.
- Generating Codex-specific `AGENTS.md` files inside created workspaces.
- Installing the Rose skill automatically during `rose init`.
- Custom executable paths or arbitrary launch command templates.
- Changing the existing automatic-open behavior or adding a `--no-open` flag.
