# Rose

CLI for multi-repo development workspaces. Rose creates git worktrees across
selected repos on a shared feature branch, writes a `.code-workspace` file, and
opens Cursor.

## Requirements

- Python 3.9+
- [pipx](https://pipx.pypa.io/)
- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated (`gh auth login`)
- `git`
- `cursor` (optional — used to open workspaces after create/edit/list)

## Install

From a clone of this repository:

```bash
git clone <repo-url> rose
cd rose
pipx install .
```

Verify:

```bash
rose --help
```

## Upgrade

Rose is not published to PyPI (a different `rose` package exists there — do not
run `pipx install rose`).

If you installed from a local clone or git URL, `pipx upgrade rose` re-installs
from that same source after you pull changes:

```bash
cd /path/to/rose
git pull
pipx upgrade rose
```

Or reinstall explicitly:

```bash
cd /path/to/rose
git pull
pipx install . --force
```

## First-time setup

```bash
rose init
```

Interactive setup. Configures:

- Workspace root (default `~/workspaces`)
- Template path (default `~/.rose/templates/default`)
- GitHub organization
- Vault path (optional, blank to skip) — a persistent docs folder (e.g. an
  Obsidian vault) that new workspaces link their docs into, instead of a
  local `docs/` folder. Change it later with `rose vault set <path>`.

Config is stored at `~/.rose/config.toml`. Bare clones live in
`~/.rose/repos/`.

## Install the agent skill

Rose includes a Cursor skill so agents know how to run the CLI correctly
(non-interactive flags, workspace layout, limitations). When working inside a
clone of this repo, Cursor discovers `.cursor/skills/rose/` automatically.

**Install globally** (other projects, without cloning rose):

```bash
npx skills add tristantoupin/rose@rose -g -y
```

**Install into the current project:**

```bash
npx skills add tristantoupin/rose@rose -y
```

**Manual fallback** (local clone, stays in sync with your working tree):

```bash
cd /path/to/rose
mkdir -p ~/.cursor/skills
ln -sf "$(pwd)/.cursor/skills/rose" ~/.cursor/skills/rose
```

Start a new agent session after installing.

## Commands

### `rose create`

Create a new multi-repo workspace.

**Interactive** (prompts for name, branch, and repo picker):

```bash
rose create
```

**Non-interactive** (for scripts and agents — no TTY required):

```bash
rose create \
  --name my-feature \
  --branch my-feature \
  --repo myorg/api \
  --repo myorg/web
```

| Flag | Description |
|------|-------------|
| `--name` | Workspace name (folder name). Alphanumeric, `-`, `_`. |
| `--branch` | Feature branch. Defaults to `--name`. |
| `--repo` | `org/repo`. Repeatable. |
| `--refresh` | Force refresh GitHub repo cache. |

Creates:

```
~/workspaces/my-feature/
├── my-feature.code-workspace
├── docs/                      # only if no vault is configured
└── repos/
    ├── api/
    └── web/
```

If a vault is configured (`rose init` or `rose vault set <path>`), the
workspace has no local `docs/` — the `.code-workspace` file's docs folder
entry instead points at `<vault>/my-feature/`, which persists even after the
workspace is deleted.

### `rose edit`

Add or remove repos on an existing workspace.

**Non-interactive** (for scripts and agents — no TTY required):

```bash
rose edit my-feature --repo myorg/api --repo myorg/web
```

`--repo` is repeatable and must list the **full desired repo set** —
repos already present that aren't re-listed are removed. To keep a repo,
list it again alongside any new ones.

**Interactive** (no `--repo` given) — uses a fuzzy multiselect picker
pre-selected with current repos (requires TTY):

```bash
rose edit my-feature
rose edit                    # infers workspace when run inside one
rose edit my-feature --force # skip uncommitted/unpushed safety checks on removal
```

### `rose list`

List workspaces and open one in Cursor. **Interactive** — fuzzy picker
(requires TTY).

```bash
rose list
```

### Other commands

```bash
rose init              # first-time setup
rose org set <org>     # set GitHub org and rebuild repo cache
rose repos sync        # refresh cached repo list
rose vault set <path>  # set/change the persistent docs vault
rose --help            # full command list
rose <command> --help  # per-command help
```

## Agent-friendly usage

Agents should read `.cursor/skills/rose/SKILL.md` (or the installed copy at
`~/.cursor/skills/rose/SKILL.md`) before running Rose commands.

Key points:

- Use `rose create --name ... --repo ...` and `rose edit <name> --repo ...`
  — never rely on interactive pickers
- `rose list` needs a human or TTY; agents can scan `*.code-workspace` files
  under the workspace root instead
- Ensure `rose init` has been run and `gh auth status` succeeds before creating
  workspaces

## Help

```bash
rose --help
rose create --help
rose edit --help
rose list --help
```
