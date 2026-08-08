---
name: rose
description: >
  Manage multi-repo Rose workspaces with the rose CLI. Use when the user asks
  to create, edit, or list workspaces, set up a feature branch across repos,
  open a Cursor workspace, or run rose commands.
---

# Rose CLI

Rose sets up multi-repo development workspaces: bare clones, git worktrees on a
shared feature branch, a `.code-workspace` file, and optional Cursor launch.

**Prefer non-interactive flags** whenever driving `rose` from an agent. Several
commands use InquirerPy pickers that require a TTY.

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.9+ | Runtime |
| [pipx](https://pipx.pypa.io/) | Isolated global install |
| [GitHub CLI](https://cli.github.com/) (`gh`) | Repo list, search, default branch |
| `git` | Bare clones and worktrees |
| `cursor` (optional) | Auto-open workspace after create/edit/list |

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

Config file: `~/.rose/config.toml`

```toml
[workspace]
path = "/absolute/path/to/workspaces"

[template]
path = "/absolute/path/to/template"

[github]
org = "your-org"
```

If init was skipped or org changed later:

```bash
rose org set <orgname>
```

Refresh cached repo list (24h TTL):

```bash
rose repos sync
```

## Agent decision tree

```
Need a new multi-repo workspace?
  └─ rose create --name ... --branch ... --repo org/repo [--repo ...]

Need to add/remove repos on an existing workspace?
  └─ rose edit <name>   # interactive picker — needs TTY

Need to find/open an existing workspace?
  └─ rose list          # interactive picker — needs TTY

Config missing?
  └─ Tell user to run rose init (interactive)

Repo cache stale or empty?
  └─ rose repos sync
```

## Commands

### `rose create` — create workspace (agent-friendly)

Creates a workspace folder, bare clones (or updates them), worktrees on a
feature branch, `.code-workspace` metadata, and opens Cursor.

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

**Result layout:**

```
<workspace_root>/<name>/
├── <name>.code-workspace    # Cursor/VS Code workspace + rose metadata
├── docs/                    # from template (shared docs folder)
└── repos/
    ├── api/                 # worktree on feature branch
    └── web/
```

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

### `rose edit <name>` — add or remove repos (interactive)

Modifies repos on an active workspace. Pre-selects current repos in a fuzzy
multiselect.

```bash
rose edit my-feature
rose edit              # infers name when cwd is inside a workspace
rose edit my-feature --force   # skip safety checks on removals
```

**Not agent-friendly:** no flags to add/remove repos non-interactively. Requires
TTY. If an agent needs this, ask the user to run it or use a pseudo-TTY.

**Safety:** refuses to remove repos with modified, untracked, or unpushed
work unless `--force`.

**Inactive workspaces:** fails with message to reactivate first (reactivate not
yet implemented in all versions — check `rose --help`).

### `rose list` — list and open workspace (interactive)

Scans workspace root, shows fuzzy picker sorted by `rose.created`, opens
selection in Cursor.

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

### `rose init` — first-time setup (interactive)

One-time machine setup. Not for agents unless user is present.

### `rose org set <orgname>` — change GitHub org

Updates config and rebuilds repo cache.

### `rose repos sync` — refresh repo cache

Fetches all repos for the configured org from GitHub.

## Common agent workflows

**Create a workspace for a ticket:**

```bash
rose create \
  --name clin-12345-feature \
  --branch clin-12345-feature \
  --repo myorg/api.clinical \
  --repo myorg/web
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

## Install the Rose skill

Inside a rose clone, Cursor auto-discovers `.cursor/skills/rose/`. Elsewhere:

```bash
npx skills add tristantoupin/rose@rose -g -y   # global (~/.cursor/skills/)
npx skills add tristantoupin/rose@rose -y      # current project
```

Manual fallback from a local clone:

```bash
ln -sf "$(pwd)/.cursor/skills/rose" ~/.cursor/skills/rose
```

Restart Cursor or start a new agent session so the skill is picked up.
