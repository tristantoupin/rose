# Design: add-codex-app-support

## Current State

Rose has three Cursor-specific integration points:

1. `open_cursor(ws_file)` always resolves and launches the `cursor` executable.
2. `rose create`, `rose edit`, and `rose list` pass only a `.code-workspace` path to that launcher.
3. Repository skills and durable instructions live under `.cursor`, even when their content is not Cursor-specific.

The `.code-workspace` file is also Rose's persisted workspace metadata. Commands scan it to discover workspaces and read its `rose` block when editing or inspecting state.

## Target Model

```
~/.rose/config.toml
        │
        └─ [app].name
              ├─ cursor ──> cursor <name>.code-workspace
              └─ codex  ──> codex app <workspace-directory>
```

Application selection is global. Every existing and future workspace opens with the currently configured application. Workspace metadata remains unchanged and continues to live in `.code-workspace`.

## Configuration

### Schema

```toml
[workspace]
path = "/absolute/path/to/workspaces"

[template]
path = "/absolute/path/to/template"

[github]
org = "example-org"

[vault]
path = "/absolute/path/to/vault"

[app]
name = "cursor"
```

`[app].name` accepts exactly `cursor` or `codex`.

### Compatibility Rules

| Configuration state | Effective application | Next config rewrite |
| --- | --- | --- |
| `[app] name = "cursor"` | Cursor | Preserve Cursor |
| `[app] name = "codex"` | Codex | Preserve Codex |
| No `[app]` section | Cursor | Write explicit Cursor value |
| Unknown application value | Reject with a clear configuration error | Do not launch |

The missing-section fallback preserves the behavior of every existing Rose installation. `set_org` and `set_vault_path` must read and pass through the effective application so their whole-file rewrite does not reset a Codex selection.

### Config Helpers

Add application constants and helpers in `rose_cli/config.py`:

- `SUPPORTED_APPS = ("cursor", "codex")`
- `DEFAULT_APP = "cursor"`
- `get_app() -> str`
- `set_app(app_name: str) -> None`

`write_config(...)` gains an application argument that defaults to `DEFAULT_APP` and always emits `[app]`. `get_app()` returns `DEFAULT_APP` when the section is absent and rejects unsupported persisted values rather than silently launching an unexpected command.

## Initialization

`rose init` adds an application prompt after the workspace/template configuration and before writing the config:

```text
Development application (cursor, codex) [cursor]:
```

The prompt uses a case-insensitive Click choice and stores the normalized lowercase value. Cursor remains the default.

Initialization checks the selected executable with `shutil.which`. A missing executable produces a warning but does not prevent directory scaffolding, configuration, or repository-cache setup. The final summary includes the selected application.

## App Command

Add a Click command group and setter:

```text
rose app set cursor
rose app set codex
```

Behavior:

1. Refuse with the existing `Run 'rose init' first` guidance when no config exists.
2. Validate the argument through `click.Choice(SUPPORTED_APPS, case_sensitive=False)`.
3. Persist the normalized application while preserving workspace, template, organization, and vault values.
4. Warn if the corresponding executable is not currently available.
5. Print the saved application and config path.

The command only changes configuration; it does not open a workspace.

## Application-Aware Launcher

Replace `open_cursor(ws_file)` with a helper that receives both workspace paths:

```python
open_workspace(workspace_path: Path, ws_file: Path) -> None
```

The helper reads the configured application and builds one of two fixed command arrays:

| Application | Executable | Arguments | Working model |
| --- | --- | --- | --- |
| Cursor | `cursor` | `<workspace-file>` | Cursor multi-root workspace |
| Codex | `codex` | `app <workspace-directory>` | Codex project rooted at the Rose workspace |

Both launchers use `subprocess.Popen` and remain non-blocking. No shell interpolation or configurable command template is introduced.

When the executable is missing, Rose prints an application-specific warning and the exact manual command:

```text
  ⚠  'codex' not found in PATH. Open manually:
     codex app /path/to/workspace
```

Unexpected process-launch errors are reported with the selected application and leave the completed workspace operation intact.

### Call Sites

- `rose create`: pass the newly created workspace directory and workspace file.
- `rose edit`: pass the resolved workspace directory and workspace file.
- `rose list`: use `WorkspaceInfo.workspace_path` and `WorkspaceInfo.ws_file`.

Command help text and comments use application-neutral language such as “open the workspace in the configured app.”

## Workspace Metadata

Rose continues creating `<name>.code-workspace` for both applications. Its responsibilities remain:

- Cursor multi-root folder configuration.
- Rose workspace identity, creation date, repo branches, and default branches.
- Workspace discovery for `list`, `edit`, and related commands.

Codex does not receive the file as its project path. It opens the containing directory, whose layout is:

```text
<workspace_root>/<name>/
├── <name>.code-workspace
├── docs/ or template content
└── repos/
    ├── repo-a/
    └── repo-b/
```

This keeps all worktrees and shared docs beneath the Codex project root without introducing a metadata migration.

## Agent Integration Layout

Target repository layout:

```text
AGENTS.md                         # canonical durable repository instructions
.agents/
└── skills/                      # canonical skills for compatible agents
    ├── rose/
    └── openspec-*/
.cursor/
└── skills -> ../.agents/skills  # Cursor compatibility alias
```

All existing skills move together so ownership is consistent. The Rose skill becomes application-neutral and documents both launchers while retaining agent-friendly, non-interactive Rose workflows.

The lean-scope and CLI-documentation rules currently stored in `.cursor/rules` are consolidated into `AGENTS.md`. The Cursor rule files are then removed because Cursor can consume the canonical `AGENTS.md` guidance directly.

Skill installation remains separate from `rose init`. Repository-local discovery uses the layout above; global installation continues through the documented skill installer.

## Documentation

`README.md` must describe:

- Cursor or Codex Desktop as optional application dependencies.
- The application prompt in `rose init`.
- The `[app]` configuration section and Cursor fallback for legacy configs.
- `rose app set cursor|codex`.
- Application-specific launch commands.
- `.code-workspace` as shared Rose metadata that Cursor consumes directly and Codex ignores.
- Canonical `.agents/skills` installation/discovery and Cursor compatibility.

The Rose skill must mirror the command surface, flags, TTY requirements, configuration, workspace layout, and both application workflows.

## Risks and Mitigations

- Risk: Adding a new config field is lost when another setter rewrites the file.
  - Mitigation: every config-writing path reads and preserves the effective application; `write_config` always emits `[app]`.
- Risk: Existing users see a behavior change without opting in.
  - Mitigation: absent application configuration resolves to Cursor, exactly matching current behavior.
- Risk: Codex opens only one repository instead of the complete Rose workspace.
  - Mitigation: always pass the Rose workspace root to `codex app`.
- Risk: Skills or instructions drift between agent-specific directories.
  - Mitigation: keep one canonical `.agents/skills` tree and one canonical `AGENTS.md`; Cursor paths only alias shared content.
- Risk: Selected application is not installed yet.
  - Mitigation: warn during init/configuration and print the exact manual launch command at open time without blocking other Rose work.
- Risk: Moving all skills disrupts repository discovery.
  - Mitigation: preserve Cursor's expected `.cursor/skills` path as an alias and manually verify skill discovery in both Cursor and Codex.
