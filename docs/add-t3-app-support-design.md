# Design: add-t3-app-support

**Date**: 2026-10-09

## Current State

The application is a global setting, resolved in `rose_cli/config.py`:

- `SUPPORTED_APPS = ("cursor", "codex")`, `DEFAULT_APP = "cursor"`
- `get_app()` / `set_app()` / `write_config()` validate against `SUPPORTED_APPS`

`open_workspace(workspace_path, ws_file)` in
`rose_cli/commands/workspace/_helpers.py` sends the workspace to the app:

| App | Arguments | Process model |
| --- | --- | --- |
| `cursor` | `<ws_file>` | `subprocess.Popen`, fire-and-forget |
| `codex` | `app <workspace_path>` | `subprocess.Popen`, fire-and-forget |

For Codex, the external-folder work landed with this change also calls
`_materialize_codex_folders()`
before launching. That function symlinks `.code-workspace` folders that live
outside the workspace root (such as the docs vault) into the root, because
Codex reads the directory and not the `.code-workspace` file.

`rose init` prompts with a hard-coded label, `Development application (cursor,
codex)`, but validates against `SUPPORTED_APPS`. `rose app set` takes its
choices from `SUPPORTED_APPS` directly.

## How T3 Code Opens a Directory

Inspecting T3 Code (Alpha) 0.0.45 showed that:

- The desktop app (bundle id `com.t3tools.t3code`) does **not** open folders
  passed as launch arguments or `open-file` events. Its argv and `t3code://`
  URL handling only covers provider/OAuth sign-in handoff.
- The `t3` CLI (npm package `t3`, installed with `npm install -g t3`) provides:

  ```text
  t3 app [path]    Open a project in the running T3 Code desktop app.
                   path: Project directory. Default: current directory.
  ```

- `t3 app` resolves `path` to an absolute directory and sends a version 1
  `open-workspace` request over a local-only socket
  (`$TMPDIR/t3code-<uid>/<hash>.sock` on macOS and Linux, a named pipe on
  Windows) to the running desktop app. The response is either
  `{ok: true, projectId, threadId}` or `{ok: false, code, message}`. The error
  codes include `project-create-failed` and `thread-open-failed`, so the
  desktop app registers the directory as a project if needed and then opens a
  thread in it.
- Failure modes Rose has to handle:
  - The desktop app is not running, so the socket is unreachable: *"Could not
    reach the T3 Code desktop app. Start or update the desktop app on this
    machine, then run `t3 app` again."*
  - The command runs over SSH (`SSH_CONNECTION` / `SSH_TTY` set): `t3 app`
    refuses.
  - The desktop app does not answer within the CLI's 17-second timeout.

T3 is therefore a directory-based app like Codex: `<bin> app <workspace_dir>`.
The difference is that `t3 app` is a short request/response client, not a
long-running GUI process, and its exit status is the only way to tell whether
the workspace opened.

## Target Model

```
~/.rose/config.toml
        │
        └─ [app].name
              ├─ cursor ──> cursor <name>.code-workspace                    (Popen)
              ├─ codex  ──> [link external folders] codex app <workspace-dir> (Popen)
              └─ t3     ──> [link external folders] t3 app <workspace-dir>    (run, check exit)
                               │
                               └─ local socket ──> T3 Code desktop
                                                   (create/reuse project, open thread)
```

## Data Models

### Rose configuration

The schema keeps its shape. `[app].name` gains one allowed value:

```toml
[app]
name = "t3"   # one of: cursor, codex, t3
```

| Configuration state | Effective application |
| --- | --- |
| `name = "cursor"` / no `[app]` | Cursor (unchanged) |
| `name = "codex"` | Codex (unchanged) |
| `name = "t3"` | T3 Code |
| Unknown value | Clear configuration error (unchanged) |

`config.py` change: `SUPPORTED_APPS = ("cursor", "codex", "t3")`. Validation in
`write_config()`, `get_app()`, `set_app()`, and the `rose app set` Click choice
all read this tuple, so they pick up `t3` automatically.

**Downgrade note:** an older Rose that reads `name = "t3"` stops with its
existing "Unsupported application" error. This is the same behavior Codex
configs have on pre-Codex builds.

### T3 Code state

Rose does not read or write T3's state (`~/.t3/userdata`). T3 owns project
records. Opening the same workspace again reuses its existing project, keyed by
absolute workspace root.

### Workspace metadata

No change. `.code-workspace` is still Rose's metadata and Cursor's workspace
file. T3 ignores it, the same way Codex does.

## API Changes

### CLI surface

| Command | Change |
| --- | --- |
| `rose init` | The application prompt lists `cursor, codex, t3`. The label drops its hard-coded list because Click's `Choice` already shows `SUPPORTED_APPS` (the old label showed the choices twice). |
| `rose app set <cursor\|codex\|t3>` | Accepts `t3` (no code change beyond `SUPPORTED_APPS`). |
| `rose create` / `rose edit` / `rose list` | No signature change. They open the workspace through `open_workspace()`. |

Missing-executable warnings in `init` and `app set` already use
`shutil.which(app_name)`. The executable is named `t3`, so they work without
changes.

### `open_workspace()` changes

```python
def open_workspace(workspace_path: Path, ws_file: Path) -> None:
    ...
    if app_name in ("codex", "t3"):
        _materialize_external_folders(workspace_path, ws_file)

    app_bin = shutil.which(app_name)
    if app_name == "cursor":
        args = [str(ws_file)]
    else:  # codex, t3
        args = ["app", str(workspace_path)]
    manual_command = ...  # unchanged format: "<app> <args>"

    if not app_bin:
        ...  # unchanged: warn + print manual command
        return

    if app_name == "t3":
        _open_in_t3(app_bin, args, workspace_path, manual_command)
        return

    ...  # unchanged Popen path for cursor / codex
```

The new `_open_in_t3()` helper:

1. Runs `subprocess.run([app_bin, *args], cwd=workspace_path,
   capture_output=True, text=True, timeout=T3_OPEN_TIMEOUT_SECONDS)` with
   `T3_OPEN_TIMEOUT_SECONDS = 30`. That is longer than the CLI's own 17-second
   timeout, so the CLI normally reports its own error first.
2. On exit code 0, prints `  ✓  Opened workspace in t3`.
3. On a non-zero exit code, prints the reason, followed by a hint and the
   manual command. The real CLI writes errors to **stdout** as
   `<time> ERROR (#n): SomeError: <message>` followed by a stack trace, so Rose
   scans stderr and then stdout for the first line containing `Error: ` and
   shows the text after it. If there is no such line, Rose shows the first
   non-empty line, or `exit code <n>` when there is no output:

   ```text
     ⚠  t3 could not open the workspace: Could not reach the T3 Code desktop app. ...
        Start the T3 Code desktop app, then run:
        t3 app /path/to/workspace
   ```

4. On `OSError` or `subprocess.TimeoutExpired`, prints the same warning with
   the exception text and the manual command.
5. Never raises. The completed `create`, `edit`, or `list` operation is not
   undone, matching how Cursor and Codex launch failures are handled.

The command is a fixed argument array with no shell interpolation. Using
`cwd=workspace_path` follows the Codex external-folder change. `t3 app` also
defaults to the current directory, but Rose always passes the path explicitly.

### External-folder links

The Codex external-folder helpers become app-neutral but keep their behavior:

| Before | After |
| --- | --- |
| `_materialize_codex_folders()` | `_materialize_external_folders()` |
| `✓  Codex folder:    <link> → <target>` | `✓  Linked folder:   <link> → <target>` |
| `⚠  Could not expose <target> in Codex: <err>` | `⚠  Could not link <target>: <err>` |

They are called when the app is `codex` or `t3`. Cursor still uses the
`.code-workspace` folder entries directly and gets no links.

## Documentation Changes

Per `AGENTS.md`, `README.md` and `.agents/skills/rose/SKILL.md` must stay
aligned:

- Intro and requirements: add T3 Code, with both prerequisites. Users need the
  desktop app and `t3` on `PATH` (`npm install -g t3`).
- `rose init` application choices and the `[app]` values.
- `rose app set <cursor|codex|t3>`.
- Launch table: `T3: t3 app <workspace-directory>`. The desktop app must
  already be running.
- External-folder links apply to Codex **and** T3.
- A short "T3 Code project registration" note in the skill, next to the Codex
  one: `t3 app <dir>` is the supported way to register and open a workspace.
  Agents should not edit T3 state directly.

## Alternatives Considered

| Alternative | Why not |
| --- | --- |
| `open -a "T3 Code (Alpha)" <dir>` | The desktop app ignores folder arguments and `open-file` events. The bundle name includes `(Alpha)` and will change. |
| `t3code://` deep link | The scheme only routes sign-in handoff and `/welcome` / `/settings` return URLs. It has no open-project route. |
| `t3 project add <dir>` | It registers a project but does not open or focus the app. When the desktop app is not running, it writes to T3's state store offline. `t3 app` creates and opens in one supported step. |
| `npx t3 app <dir>` fallback | No global install is needed, but the first run is slow and needs the network, and the CLI version can drift from the desktop app. Kept out of scope. Users can run it by hand. |
| Fire-and-forget `Popen` (like Codex) | `t3 app` exits in about a second, so the exit code is the only signal that the desktop app was reachable. With `Popen`, failures would be lost or print after Rose had already exited. |
| Start the desktop app automatically, then retry | Platform-specific, depends on an unstable bundle name, and needs polling for socket readiness. Deferred (see open questions in the implementation plan). |
| A new app-neutral manifest instead of `.code-workspace` | Out of scope, for the same reasons as in the Codex change. |

## Risks and Mitigations

- **The desktop app is not running when Rose opens a workspace.** Rose reports
  the CLI's reason and the exact manual command. The workspace operation still
  succeeds.
- **`t3` is not on `PATH`.** This is common with nvm-scoped global npm
  installs. Rose warns in `init` and `app set`, and at open time prints the
  manual command. The README documents `npm install -g t3`.
- **The `t3 app` contract changes, since T3 Code is in alpha.** Rose depends
  only on the documented CLI surface (`t3 app <path>` plus the exit code), not
  on the socket protocol. Failures show up as warnings, not crashes.
- **T3 expects git-rooted projects.** The Rose workspace root is not a git
  repository, because repos live under `repos/`. T3 features that need git at
  the project root (branch toolbar, worktree-mode threads) may be unavailable.
  Codex has the same limitation. Documented, not mitigated.
- **The CLI and desktop app use different T3 homes.** `t3 app` uses
  `T3CODE_HOME` / its default. Custom homes are out of scope. If one is set,
  the inherited environment applies.
