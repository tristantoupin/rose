# Proposal: add-t3-app-support

**Date**: 2026-10-09

## Context

Rose creates multi-repo workspaces and opens them in a configurable development
application. The `add-codex-app-support` change made the application a global
setting (`[app].name` in `~/.rose/config.toml`) with two supported values:

| App | Launch command |
| --- | --- |
| `cursor` (default) | `cursor <workspace>.code-workspace` |
| `codex` | `codex app <workspace-directory>` |

The launcher lives in `open_workspace()` in
`rose_cli/commands/workspace/_helpers.py` and is shared by `rose create`,
`rose edit`, and `rose list`. The application is chosen in `rose init` and
changed with `rose app set <cursor|codex>`.

[T3 Code](https://t3.codes) is a desktop GUI for coding agents (Codex, Claude
Code, and others). It organizes work into **projects**, each rooted at a local
directory. Its companion CLI, `t3` (npm package `t3`), has a command that opens
a directory in the running desktop app:

```bash
t3 app [path]   # "Open a project in the running T3 Code desktop app."
```

`t3 app` sends an `open-workspace` request over a local-only socket to the
desktop app. The app registers the directory as a project if it does not exist
yet, then opens a thread in it. This is how Codex Desktop works with
`codex app <dir>`, so it fits Rose's existing directory-based launch model.

## Problem Statement

Users who work in T3 Code have no way to make Rose open workspaces there. After
`rose create`, `rose edit`, or `rose list`, Rose can only start Cursor or Codex.
These users have to add each workspace as a T3 project by hand, which defeats
Rose's "create and open in one step" workflow.

## Proposed Solution

Add T3 Code as a third supported application, `t3`, alongside `cursor` and
`codex`:

1. Accept `t3` as a value for `[app].name`, in the `rose init` prompt, and in
   `rose app set <cursor|codex|t3>`.
2. When T3 is configured, open workspaces with
   `t3 app <workspace-directory>`, which uses the same Rose workspace root as
   Codex.
3. Report whether the open succeeded. `t3 app` only works when the T3 Code
   desktop app is running, so if it fails, Rose prints the reason and the exact
   manual command. The completed workspace operation is kept.
4. Expose external `.code-workspace` folders (for example, the docs-vault
   folder) as symlinks under the workspace root for T3, the same way the
   in-progress Codex change does. Like Codex, T3 opens a directory and does not
   read `.code-workspace`.
5. Update `README.md` and `.agents/skills/rose/SKILL.md` to cover T3 Code.

## Scope

- **Configuration**: add `t3` to `SUPPORTED_APPS`. The default stays `cursor`,
  and existing configs keep working unchanged.
- **Initialization**: list `t3` as a choice in the `rose init` application
  prompt. If `t3` is not on `PATH`, Rose warns but does not block.
- **CLI**: `rose app set t3` works like the existing choices.
- **Launcher**: add a `t3` branch to `open_workspace()` that runs
  `t3 app <workspace-directory>` and reports success or failure.
- **External folders**: apply the existing Codex external-folder symlinking to
  T3 as well, using app-neutral helper names and output.
- **Documentation**: in `README.md` and the Rose skill, cover requirements (the
  T3 Code desktop app plus the `t3` CLI on `PATH`), the `[app]` values,
  `rose app set t3`, launch behavior, the external-folder links, and
  troubleshooting when the desktop app is not running.

## Out of Scope

- Starting the T3 Code desktop app automatically when it is not running.
- Falling back to `npx t3` when `t3` is not on `PATH`.
- T3's web/server mode (`t3 serve`, `npx t3`) and remote or SSH environments.
  `t3 app` refuses to run over SSH.
- Custom T3 homes (`T3CODE_HOME` / `--base-dir`), project titles, or other
  `t3` flags.
- Removing T3 projects when Rose workspaces are deactivated or deleted.
- Per-workspace application overrides. The application stays a global setting.
- Changes to `.code-workspace` generation or Rose workspace metadata.

## Dependencies

- This builds on the Codex external-folder symlink work in
  `rose_cli/commands/workspace/_helpers.py` (`_materialize_codex_folders`).
  That work should land first, or together with this change.
- Users need T3 Code desktop running and a `t3` CLI that supports `t3 app`.
  This was verified against T3 Code (Alpha) 0.0.45.
