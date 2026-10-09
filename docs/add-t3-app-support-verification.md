## Verification Report: add-t3-app-support

**Date**: 2026-10-09

Artifacts checked: `add-t3-app-support-proposal.md`,
`add-t3-app-support-design.md`, `add-t3-app-support-implementation-plan.md`.
All three dimensions were verified.

### Summary

| Dimension    | Status |
|--------------|--------|
| Completeness | 10/10 plan steps, 5/5 scope items |
| Correctness  | 5/5 scope items implemented, all plan validation scenarios run manually |
| Coherence    | Design followed; 2 deviations, both recorded in the design and plan |

### Completeness

**Plan steps:** 10/10 are marked `[x]`. None are incomplete.

**Proposal scope:**

| Scope item | Evidence |
|---|---|
| Configuration: `t3` supported, Cursor default unchanged | `rose_cli/config.py:8-9` |
| Initialization: `t3` offered; warns without blocking | `rose_cli/commands/init.py:97-102`, `rose_cli/commands/init.py:149` |
| CLI: `rose app set t3` | `rose_cli/commands/app/set.py:13` (Click choice reads `SUPPORTED_APPS`) |
| Launcher: `t3 app <workspace-directory>`, success/failure reported | `rose_cli/commands/workspace/_helpers.py:93-122`, `rose_cli/commands/workspace/_helpers.py:152-154` |
| External folders: Codex symlinking extended to T3, app-neutral names | `rose_cli/commands/workspace/_helpers.py:76-90`, `rose_cli/commands/workspace/_helpers.py:136-137` |
| Documentation: README and Rose skill | `README.md` (intro, requirements, init, docs-vault note, `rose app set`, launch table, agent notes); `.agents/skills/rose/SKILL.md` (prerequisites, config, decision tree, link section, `rose app set`, launch table, "T3 Code project registration", error table) |

### Correctness

- **App set to `t3`:** `open_workspace()` links external folders
  (`_helpers.py:136`), builds `["app", <workspace>]` (`_helpers.py:142-143`),
  and calls `_open_in_t3()` (`_helpers.py:152-154`). That function runs
  `subprocess.run` with `capture_output`, `cwd`, and a 30-second timeout
  (`_helpers.py:101-107`).
- **Failure handling:** a non-zero exit code shows the message after `Error: `
  (`_helpers.py:114-118`). `OSError` and `TimeoutExpired` are caught
  (`_helpers.py:108-109`). The function never raises, and the manual command is
  always printed (`_helpers.py:120-122`).
- **Call sites unchanged:** `create.py:370`, `edit.py:307`, and `list.py:95`
  still call `open_workspace()`.
- **Scenarios covered:** each scenario from plan steps 8–9 was run by hand:
  - `init` and `app set` behavior, including keeping other settings, any letter
    case, invalid values, and a bad saved value
  - `t3` missing from `PATH`
  - success, failure, silent failure, and timeout
  - the real CLI with the desktop app unreachable
  - a live open against T3 Code 0.0.45, with the project reused on reopen
  - the vault `docs` link
  - Cursor and Codex unchanged
- The repository has no automated test suite, so none of these scenarios have
  automated tests (see suggestions).

### Coherence

Design decisions were checked against the code:

| Decision | Status |
|---|---|
| `t3` treated as a directory-based app (`app <workspace-dir>`) | Followed (`_helpers.py:139-144`) |
| Run synchronously and check the exit code, unlike Popen for Cursor/Codex | Followed (`_helpers.py:101-107`; Popen path unchanged at `_helpers.py:157`) |
| No auto-launch, no `npx` fallback, no direct writes to T3 state | Followed. None of these are present. |
| External-folder helpers renamed and messages app-neutral | Followed (`_helpers.py:76`, `:78`, `:81`) |
| `rose init` label | **Deviation, documented.** The label is now the plain `"Development application"`. Click's `Choice` already lists the options, and the old hard-coded label showed them twice. Design and plan step 3 updated. |
| Failure reason parsing | **Deviation, documented.** The real CLI writes errors to stdout with a stack trace, so the reason is now the text after `Error: `, not the last line. Design and plan step 5 updated. |

Code patterns are consistent with the project: `click.echo` with `✓`/`⚠`
prefixes, a module-level constant, and private `_`-prefixed helpers. `list[str]`
is safe on Python 3.9 because `from __future__ import annotations` is in place.

### Issues by Priority

**CRITICAL:** none.

**WARNING:** none.

**SUGGESTION**

1. ~~The design, plan, and proposal referred to the Codex link work as
   "uncommitted".~~ Applied: the wording now says it landed with this change.
2. No automated tests exist for `open_workspace()`. All validation in plan
   steps 8–9 was manual. If a test suite is added later, the `_open_in_t3()`
   branches (success, error-line parsing, timeout, `OSError`) are good first
   candidates. They can be driven by a stand-in `t3` executable.
3. Pre-existing and out of scope: `rose app set` shows a raw traceback when the
   saved `[app].name` is invalid (`rose_cli/config.py` `get_app()` raises
   `ValueError`, which `set_app_cmd` does not catch). Consider catching it in a
   follow-up.

### Final Assessment

No critical issues and no warnings. There are 2 open suggestions (1 applied).
All checks passed. Ready for archive.
