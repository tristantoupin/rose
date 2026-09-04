# Tasks: add-codex-app-support

## Implementation Tasks

- [x] 1. Extend `rose_cli/config.py` with supported/default application constants, `[app]` serialization, `get_app()`, and `set_app()`.
  - Treat a missing `[app]` section as Cursor.
  - Reject unsupported persisted values with a clear error.
  - Ensure `set_org()` and `set_vault_path()` preserve the effective application.
  - Ensure every subsequent config rewrite materializes `[app] name = "cursor"` for legacy configs.

- [x] 2. Update `rose init` to configure the workspace application.
  - Prompt with a case-insensitive `cursor|codex` choice and default to Cursor.
  - Warn without aborting when the selected executable is unavailable.
  - Persist the selected application and include it in the final summary.

- [x] 3. Add the `rose app set <cursor|codex>` command group and register it in `rose_cli/main.py`.
  - Require an existing config and direct uninitialized users to `rose init`.
  - Preserve every unrelated config value.
  - Warn without aborting when the selected executable is unavailable.
  - Print the selected application and config path.

- [x] 4. Replace `open_cursor` with an application-aware `open_workspace(workspace_path, ws_file)` helper.
  - Cursor command: `cursor <workspace-file>`.
  - Codex command: `codex app <workspace-directory>`.
  - Keep both launches non-blocking with argument arrays and no shell interpolation.
  - Print the exact manual command when the selected executable is unavailable.
  - Report process-launch failures without undoing the completed workspace operation.

- [x] 5. Update workspace command call sites and language.
  - `rose create` passes its target directory and generated `.code-workspace` file.
  - `rose edit` passes the resolved workspace directory and `.code-workspace` file.
  - `rose list` passes the selected `WorkspaceInfo` paths.
  - Replace Cursor-specific help text, comments, and output with configured-app wording.
  - Keep `.code-workspace` generation, scanning, and metadata unchanged.

- [x] 6. Make agent integration paths application-neutral.
  - Move the complete `.cursor/skills` tree to canonical `.agents/skills`.
  - Add `.cursor/skills` as an alias to `../.agents/skills`.
  - Update the Rose skill to cover Cursor and Codex Desktop, the new app command, config behavior, launch behavior, and canonical paths.
  - Consolidate `.cursor/rules/project.mdc` and `.cursor/rules/cli-docs.mdc` into root `AGENTS.md`.
  - Remove `.cursor/rules` after verifying all durable instructions are represented in `AGENTS.md`.

- [x] 7. Update `README.md` to document both applications.
  - Requirements and installation prerequisites.
  - `rose init` application selection and default.
  - `[app]` config schema and legacy fallback.
  - `rose app set cursor|codex` usage.
  - Cursor and Codex launch behavior for create/edit/list.
  - Continued `.code-workspace` metadata usage.
  - Canonical `.agents/skills` discovery/installation and Cursor compatibility alias.

## Validation Tasks

- [x] 8. Run focused CLI validation with an isolated home/config location or controlled temporary config.
  - New init selecting Cursor writes `[app] name = "cursor"`.
  - New init selecting Codex writes `[app] name = "codex"`.
  - Missing executable warnings do not abort init or `rose app set`.
  - `rose app set` refuses to run before initialization.
  - `rose app set` preserves workspace, template, organization, and vault values.
  - Updating organization or vault on a legacy config materializes Cursor without changing effective behavior.
  - Invalid application arguments and invalid persisted values fail clearly.

- [x] 9. Manually validate launcher dispatch without changing workspace metadata.
  - Cursor selection launches `cursor <workspace-file>` after create, edit, and list.
  - Codex selection launches `codex app <workspace-directory>` after create, edit, and list.
  - Missing executables print the correct manual command.
  - Existing workspaces created before this change still list, edit, and open in Cursor by default.
  - Switching the global application changes how an existing workspace opens.

- [x] 10. Verify agent integration and documentation.
  - Codex and other compatible agents discover skills under `.agents/skills`.
  - Cursor discovers the same skills through `.cursor/skills`.
  - Cursor and Codex consume the root `AGENTS.md` instructions.
  - `README.md`, `AGENTS.md`, and the Rose skill agree on command names, paths, defaults, and launch behavior.
