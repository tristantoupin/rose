# Add T3 Code App Support - Implementation Plan

**Date**: 2026-10-09

## Overview

Add T3 Code as a third supported Rose application (`t3`), alongside Cursor and
Codex. When `[app].name = "t3"`, `rose create`, `rose edit`, and `rose list`
open the Rose workspace root in the running T3 Code desktop app with
`t3 app <workspace-directory>`. The desktop app registers it as a project if
needed and opens a thread. Users who work in T3 Code then get the same
"create and open" workflow that Cursor and Codex users have today.

See `add-t3-app-support-proposal.md` (what and why) and
`add-t3-app-support-design.md` (how).

## Approach

- Reuse the existing app model: add one value to `SUPPORTED_APPS`. The config,
  `rose init`, and `rose app set` validation follow from that tuple.
- Treat T3 as a directory-based app like Codex: same `app <workspace-dir>`
  arguments, same external-folder symlinks.
- Unlike Codex, run `t3 app` synchronously and check its exit code. It is a
  short-lived client, and its failure (usually "desktop app not running") is
  what the user needs to see.
- Keep the scope lean: no auto-launch of the desktop app, no `npx` fallback,
  and no direct writes to T3 state.
- Land it after (or together with) the Codex external-folder work in
  `_helpers.py`, because this change generalizes those helpers.

## Steps

1. [x] **Land the prerequisite Codex external-folder work.** (Folded into this change and landed with it.)
   Commit the Codex external-folder changes to
   `rose_cli/commands/workspace/_helpers.py`, `README.md`, and
   `.agents/skills/rose/SKILL.md` first, or fold them into this change. Either
   way, `_materialize_codex_folders()` must exist before step 4.

2. [x] **Add `t3` to the supported apps** (`rose_cli/config.py`).
   - Set `SUPPORTED_APPS = ("cursor", "codex", "t3")`. `DEFAULT_APP` stays
     `cursor`.
   - Confirm that `write_config()`, `get_app()`, and `set_app()` need no other
     changes.

3. [x] **Update the `rose init` prompt label** (`rose_cli/commands/init.py`).
   - Use the plain label `"Development application"`. Click's `Choice` already
     appends `(cursor, codex, t3)` from `SUPPORTED_APPS`. The old hard-coded
     list made the choices appear twice.
   - Leave the existing `shutil.which(app_name)` warning and summary line as
     they are. They already work for `t3`.

4. [x] **Make the external-folder helpers app-neutral**
   (`rose_cli/commands/workspace/_helpers.py`).
   - Rename `_materialize_codex_folders()` to `_materialize_external_folders()`.
   - Change the output to `✓  Linked folder:   <link> → <target>` and
     `⚠  Could not link <target>: <err>`.
   - Call it when `app_name in ("codex", "t3")`.

5. [x] **Add the T3 launch path** (`rose_cli/commands/workspace/_helpers.py`).
   - Change the argument selection to `cursor` → `[ws_file]` and
     everything else → `["app", workspace_path]`. Build the manual command the
     same way for both.
   - Add `T3_OPEN_TIMEOUT_SECONDS = 30` and `_open_in_t3(app_bin, args,
     workspace_path, manual_command)`:
     - `subprocess.run(..., cwd=workspace_path, capture_output=True,
       text=True, timeout=T3_OPEN_TIMEOUT_SECONDS)`.
     - On exit code 0, print `✓  Opened workspace in t3`.
     - On a non-zero exit code, print `⚠  t3 could not open the workspace:
       <message after "Error: " on the first matching stderr/stdout line>`
       (verified against the real CLI, which logs errors and a stack trace
       to stdout), then
       `Start the T3 Code desktop app, then run:` and the manual command.
     - On `OSError` or `TimeoutExpired`, print the same warning with the
       exception text and the manual command.
     - Never raise or exit non-zero.
   - Keep the existing `Popen` path for Cursor and Codex unchanged.
   - The `create`, `edit`, and `list` call sites need no changes.

6. [x] **Update `README.md`.**
   - Intro and requirements: add T3 Code (desktop app plus `t3` CLI via
     `npm install -g t3`).
   - `rose init` choices and the `[app]` values (`cursor`, `codex`, `t3`).
   - `rose app set <cursor|codex|t3>` heading and examples.
   - Launch table: `T3: t3 app <workspace-directory>`. The desktop app must be
     running.
   - Docs-vault and `.code-workspace` notes: external-folder links apply to
     Codex and T3.
   - Notes: the application stays global. `rose app set cursor|codex|t3`.

7. [x] **Update `.agents/skills/rose/SKILL.md`** (keep it aligned with the
   README).
   - Description and intro, requirements table row for `t3`, config values,
     command-tree line, and the `rose app set` section.
   - Launch table row and the external-folder link section (Codex and T3).
   - Add a "T3 Code project registration" note next to the Codex one:
     `t3 app <dir>` is the supported way to register and open a workspace, it
     needs the desktop app running and does not work over SSH, and agents
     should not edit `~/.t3` directly.

8. [x] **Validate the config and CLI** (isolated `HOME` or a temporary config).
   - `rose init` selecting `t3` writes `[app] name = "t3"` and warns but does
     not abort when `t3` is missing.
   - `rose app set t3` and `rose app set T3` keep the workspace, template, org,
     and vault values. `rose app set` before `rose init` still refuses.
   - Switching between `cursor`, `codex`, and `t3` changes only `[app]`.

9. [x] **Validate the launch end to end.** (Missing `t3`, success, failure,
   and timeout handling, the vault `docs` link, and the Cursor/Codex regression
   pass with stand-in executables. With the real `t3` CLI (bundled in T3 Code
   0.0.45), the unreachable-desktop failure and a live open both pass. Two
   opens reused one project titled after the directory, and the test project
   was then removed. `rose create`/`edit` call sites are unchanged and were not
   rerun against real repos.)
   - With the desktop app running: `rose create`, `rose edit`, and `rose list`
     open the workspace in T3 Code. The project appears with the workspace
     directory name, and a second open reuses the same project.
   - With the desktop app closed: Rose prints the CLI's reason and
     `t3 app <dir>`, the workspace operation completes, and the exit status is
     0.
   - With `t3` not on `PATH`: Rose prints the "not found" warning and the
     manual command.
   - With the docs vault configured: the `docs` link is created under the
     workspace root for `t3` and is visible in T3.
   - Regression: Cursor and Codex launches behave exactly as before.

10. [x] **Check the docs.** Confirm that `README.md`, the Rose skill, and the
    `rose --help` / `rose app set --help` output agree on app names, commands,
    and requirements.

## Considerations

**Technical constraints**

- `t3 app` needs the T3 Code desktop app running on the same machine. A
  running T3 server (`t3 serve`) is not enough, and the command is refused
  over SSH.
- `t3` is distributed through npm. With nvm, global installs are tied to the
  active Node version, so `t3` may be missing from the `PATH` Rose sees.
- T3 Code is in alpha (verified on 0.0.45). Rose relies only on
  `t3 app <path>` and its exit code, not on the socket protocol.
- The Rose workspace root is not a git repository, so T3 features that expect
  a git root at the project level may be limited. Codex has the same
  limitation.

**Trade-offs**

- A synchronous `t3 app` adds up to a few seconds to `create`, `edit`, and
  `list`, but it turns a silent failure into an actionable message.
- Not auto-launching the desktop app keeps Rose platform-neutral. The cost is
  one extra manual step when T3 Code is closed.
- The app-neutral rename of the Codex link helpers slightly widens the diff,
  but avoids a misleading "Codex folder" message for T3 users.

**Open questions**

1. Should Rose start the T3 Code desktop app when it is not running (for
   example, `open -b com.t3tools.t3code` on macOS) and retry `t3 app`? This is
   out of scope for now and could be a follow-up.
2. ~~Does each `t3 app` call create a new thread?~~ Answered in step 9: no.
   Two opens left one project with zero saved threads. T3 opens an unsaved
   draft, so repeated `rose list` opens do not leave empty threads.
3. Should Rose fall back to `npx t3 app <dir>` when `t3` is not on `PATH`?
   This is out of scope for now. Users can run it by hand.
4. Should deactivating or deleting a workspace also run `t3 project remove`?
   This is out of scope and would need its own proposal.
