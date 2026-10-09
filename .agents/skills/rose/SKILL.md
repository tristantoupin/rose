---
name: rose
description: >
  Manage multi-repo Rose workspaces with the rose CLI. Use when the user asks
  to create, edit, or list workspaces, set up a feature branch across repos,
  open a workspace in the configured app, or run rose commands.
---

# Rose CLI

Rose sets up multi-repo development workspaces: bare clones, git worktrees on a
shared feature branch, a `.code-workspace` file, and an optional launch in
Cursor, Codex Desktop, or T3 Code.

**Prefer non-interactive flags** whenever driving `rose` from an agent. Several
commands use InquirerPy pickers that require a TTY.

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.9+ | Runtime |
| [pipx](https://pipx.pypa.io/) | Isolated global install |
| [GitHub CLI](https://cli.github.com/) (`gh`) | Repo list, search, default branch |
| `git` | Bare clones and worktrees |
| `cursor` (optional) | Auto-open `.code-workspace` after create/edit/list |
| `codex` (optional) | Auto-open workspace directory after create/edit/list |
| `t3` (optional) | Open workspace directory in the running T3 Code desktop app after create/edit/list (`npm install -g t3`) |

Verify before first use:

```bash
rose --help
gh auth status
```

## First-time setup (human, interactive)

Run once on the machine:

```bash
rose init
```

Configures:

- Workspace root (default `~/workspaces`) — where workspace folders live
- Template path (default `~/.rose/templates/default`) — copied into new workspaces
- GitHub org — used for repo discovery
- Vault path (optional, blank to skip) — persistent docs vault (e.g. an
  Obsidian vault); if set, new workspaces link their docs folder into
  `<vault>/<name>/` instead of a local `docs/` folder
- Development application (`cursor`, `codex`, or `t3`, default `cursor`) —
  controls how workspaces are opened

Config file: `~/.rose/config.toml`

```toml
[workspace]
path = "/absolute/path/to/workspaces"

[template]
path = "/absolute/path/to/template"

[github]
org = "your-org"

[vault]
path = "/absolute/path/to/vault"

[app]
name = "cursor"
```

Legacy configs without `[app]` use Cursor. The next config rewrite materializes
`[app] name = "cursor"`.

If init was skipped or org changed later:

```bash
rose org set <orgname>
```

If a docs vault wasn't configured at init time, or the path changed:

```bash
rose vault set <path>
```

No `[vault]` section = no change in behavior — new workspaces keep getting
a local `docs/` folder exactly as before.

Refresh cached repo list (24h TTL):

```bash
rose repos sync
```

## Agent decision tree

```
Need a new multi-repo workspace?
  └─ rose create --name ... --branch ... --repo org/repo [--repo ...]

Need to add/remove repos on an existing workspace?
  └─ rose edit <name> --repo org/repo [--repo ...]   # non-interactive, full desired repo set
  └─ rose edit <name>   # interactive picker — needs TTY (no --repo given)

Need to find/open an existing workspace?
  └─ rose list          # interactive picker — needs TTY

Config missing?
  └─ Tell user to run rose init (interactive)

Repo cache stale or empty?
  └─ rose repos sync

Need to set/change the persistent docs vault?
  └─ rose vault set <path>

Need to change the workspace application?
  └─ rose app set cursor|codex|t3
```

## Commands

### `rose create` — create workspace (agent-friendly)

Creates a workspace folder, bare clones (or updates them), worktrees on a
feature branch, `.code-workspace` metadata, and opens the configured app.

**Non-interactive (use this from agents):**

```bash
rose create \
  --name my-feature \
  --branch my-feature \
  --repo myorg/api \
  --repo myorg/web
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name` | Yes (non-interactive) | Workspace folder name. Letters, numbers, `-`, `_` only. |
| `--repo` | Yes (non-interactive) | `org/repo`. Repeat for multiple repos. |
| `--branch` | No | Feature branch name. Defaults to `--name`. |
| `--refresh` | No | Force refresh GitHub repo cache before run. |

**Validation rules:**

- Workspace dir must not already exist under the configured workspace root
- Branch must not already exist in any selected repo's bare clone
- At least one repo required

**Without `--name` and `--repo`:** prompts for name, branch, and an InquirerPy
fuzzy multiselect — not suitable for agents.

**Result layout (no vault configured — default):**

```
<workspace_root>/<name>/
├── <name>.code-workspace    # Rose metadata; Cursor consumes it directly
├── docs/                    # from template (shared docs folder)
└── repos/
    ├── api/                 # worktree on feature branch
    └── web/
```

**Result layout (vault configured via `rose vault set <path>` or `rose init`):**

```
<workspace_root>/<name>/
├── <name>.code-workspace    # folders entry for docs points at the vault (absolute path)
└── repos/
    ├── api/
    └── web/

<vault_path>/<name>/         # persists after the workspace is torn down
```

When Codex or T3 Code is the configured app, Rose also creates a `docs`
symlink inside the workspace root:

```
<workspace_root>/<name>/docs -> <vault_path>/<name>/
```

Codex and T3 Code open the workspace directory and do not read
`.code-workspace`, so Rose exposes external folder entries this way. The link
is not a copy: edits made through either app remain in the configured vault.
Existing paths are never overwritten; Rose reports a warning if a link name is
already in use.

Either way, the `.code-workspace` `folders` entry for docs is always named
`"docs"` (its `path` differs) — agents and skills should match by folder
name, not by path suffix.

Bare clones (shared, not inside workspace): `~/.rose/repos/<org>__<repo>.git`

**`.code-workspace` rose block** (for reading workspace state):

```json
{
  "rose": {
    "name": "my-feature",
    "created": "2026-08-07",
    "repos": {
      "myorg/api": { "branch": "my-feature", "default_branch": "main" }
    }
  }
}
```

### `rose edit <name>` — add or remove repos

Modifies repos on an active workspace.

**Non-interactive (use this from agents):**

```bash
rose edit my-feature --repo myorg/api --repo myorg/web
```

`--repo` is repeatable and specifies the **complete desired repo set** — not
an additive list. Any current repo you omit is removed; any new repo you add
is added; repos listed that are already present are left untouched. To keep
an existing repo, list it again — the same "one-liner has the full set"
model as `rose create --repo`.

Example — workspace currently has `myorg/api` and `myorg/web`; keep `api`,
drop `web`, add `myorg/gateway`:

```bash
rose edit my-feature --repo myorg/api --repo myorg/gateway
```

**Interactive (no `--repo` given):** opens a fuzzy multiselect pre-selected
with current repos. Requires TTY — not agent-friendly.

```bash
rose edit my-feature
rose edit              # infers name when cwd is inside a workspace
rose edit my-feature --force                        # skip safety checks on removals
rose edit my-feature --repo myorg/api --force        # same, non-interactive
```

**Safety:** refuses to remove repos with modified, untracked, or unpushed
work unless `--force` — applies identically whether the removal came from
`--repo` or the interactive picker.

**Inactive workspaces:** fails with message to reactivate first (reactivate not
yet implemented in all versions — check `rose --help`).

### `rose list` — list and open workspace (interactive)

Scans workspace root, shows fuzzy picker sorted by `rose.created`, and opens
the selection in the configured app.

```bash
rose list
```

**Not agent-friendly:** no JSON or name filter flags. To list workspaces
without the picker, read directories under the workspace root and parse
`*.code-workspace` files.

**Agent workaround — enumerate workspaces:**

```bash
# workspace root from config
WORKSPACE_ROOT=$(grep '^path' ~/.rose/config.toml | cut -d'"' -f2)
find "$WORKSPACE_ROOT" -maxdepth 2 -name '*.code-workspace'
```

### `rose app set <cursor|codex|t3>` — change the application

Requires an existing config and preserves all other settings:

```bash
rose app set codex
rose app set cursor
rose app set t3
```

The argument is case-insensitive. Rose warns if the selected executable is not
available but still saves the configuration. This command does not open a
workspace.

### `rose init` — first-time setup (interactive)

One-time machine setup. Not for agents unless user is present.

The application prompt defaults to Cursor. Missing `cursor`, `codex`, or `t3`
does not abort initialization; Rose warns and continues.

## Application launch behavior

The configured application is global and applies to create, edit, and list:

| Application | Launch command |
|-------------|----------------|
| Cursor | `cursor <workspace>.code-workspace` |
| Codex Desktop | `codex app <workspace-directory>` |
| T3 Code | `t3 app <workspace-directory>` |

Cursor and Codex launches are non-blocking. The T3 launch waits up to 30
seconds for `t3 app` to report whether the desktop app opened the workspace. If
the executable is unavailable or the T3 launch fails, Rose prints the exact
manual command. `.code-workspace` remains Rose's workspace metadata and Cursor
workspace file; Codex and T3 Code open its containing workspace directory and
ignore the file.

### Codex project registration

When Codex is the configured application, `rose create`, `rose edit`, and
`rose list` use `codex app <workspace-directory>`. Codex Desktop registers and
opens that directory as a local project, so this is the supported way to add a
Rose workspace to the Codex project list.

To register an existing workspace manually:

```bash
codex app /absolute/path/to/workspace
```

Do not use `codex exec` for project registration. `codex exec` starts a CLI
agent session and requires a prompt; it is not the Codex Desktop project
creation path.

### T3 Code project registration

When T3 Code is the configured application, `rose create`, `rose edit`, and
`rose list` run `t3 app <workspace-directory>`. The `t3` CLI asks the running
T3 Code desktop app to add that directory as a project (or reuse the existing
one) and open it, so this is the supported way to add a Rose workspace to the
T3 Code project list.

To register an existing workspace manually:

```bash
t3 app /absolute/path/to/workspace
```

Requirements and limits:

- The T3 Code desktop app must already be running on the same machine. A
  running `t3 serve` server is not enough.
- `t3 app` refuses to run over SSH (`SSH_CONNECTION` or `SSH_TTY` set).
- Do not edit T3 Code state under `~/.t3` directly.

### `rose org set <orgname>` — change GitHub org

Updates config and rebuilds repo cache.

### `rose repos sync` — refresh repo cache

Fetches all repos for the configured org from GitHub.

### `rose vault set <path>` — set/change the persistent docs vault

```bash
rose vault set ~/vault
```

Creates the directory if missing and writes `[vault]` to config. From then
on, `rose create` links new workspaces' docs folder into `<vault>/<name>/`
instead of a local `docs/` folder. Existing workspaces are unaffected —
this only changes what happens on the *next* `rose create`.

## Common agent workflows

**Create a workspace for a ticket:**

```bash
rose create \
  --name clin-12345-feature \
  --branch clin-12345-feature \
  --repo myorg/api.clinical \
  --repo myorg/web
```

**Add a repo to an existing workspace (keep all current repos, add one):**

```bash
rose edit clin-12345-feature \
  --repo myorg/api.clinical \
  --repo myorg/web \
  --repo myorg/gateway
```

**Check whether rose is configured:**

```bash
test -f ~/.rose/config.toml && rose repos sync
```

**Upgrade rose** (not on PyPI — never `pipx install rose`):

```bash
cd /path/to/rose && git pull && pipx upgrade rose
# or: pipx install . --force
```

## Error messages

| Message | Action |
|---------|--------|
| `No config found. Run 'rose init' first.` | User must run `rose init` |
| `No GitHub org configured` | `rose org set <org>` |
| `Branch 'X' already exists in org/repo` | Pick a different `--name`/`--branch` |
| `'path' already exists` | Pick a different `--name` or remove old workspace |
| `Workspace 'X' not found` | Check name; list workspaces via `.code-workspace` scan |
| `inactive` | Workspace was deactivated; user must reactivate |
| `t3 could not open the workspace` | Start the T3 Code desktop app, then run the printed `t3 app <dir>` command |

## Install the Rose skill

Inside a rose clone, compatible agents discover the canonical
`.agents/skills/rose/`. Cursor also discovers the same files through the
`.cursor/skills` compatibility alias. Elsewhere:

```bash
npx skills add tristantoupin/rose@rose -g -y   # global (~/.cursor/skills/)
npx skills add tristantoupin/rose@rose -y      # current project
```

Manual fallback from a local clone:

```bash
ln -sf "$(pwd)/.agents/skills/rose" ~/.cursor/skills/rose
```

Restart Cursor or start a new agent session so the skill is picked up.
