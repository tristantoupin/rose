```
                       .-""-.
                      / .===. \
                      \/ 6 6 \/
                      ( \___/ )
 _________________ooo__\_____/_____________________
/                                                  \
| Hi! I'm Rose! I keep your workspace tidy          |
| and your worktrees happy. Let's get started!      |
\______________________________ooo_________________/
                      |  |  |
                      |_ | _|
                      |  |  |
                      |__|__|
                      /-'Y'-\
                     (__/ \__)
```

> **Note:** This README is a quick-start reference, not full documentation. Keep it updated as commands change.

---

## Install

**Requirements:** Python 3.9+, [pipx](https://pipx.pypa.io/), [GitHub CLI](https://cli.github.com/) (`gh`)

```bash
pipx install .
```

Installs the `rose` command globally in an isolated environment.

---

## Setup

```bash
rose init
```

Interactive setup. Configures workspace root, template path, and GitHub org. Caches the repo list.

```
$ rose init

                       .-""-.
                      ...

Checking prerequisites...
  ✓  GitHub CLI authenticated

Where should worktrees live? [~/workspaces]:
Workspace template path [~/.rose/templates/default]:
GitHub organization name [MyOrg]:

  ✓  Config saved to ~/.config/rose/config.toml
  ✓  42 repos cached

  All set! Rose is ready to grow! 🌹
```

---

## Commands

### `rose create`

Create a new multi-repo workspace with git worktrees.

```bash
rose create
rose create --refresh   # force repo cache refresh
```

Prompts for workspace name, branch name, and repo selection (fuzzy search). Clones bare repos, creates worktrees, scaffolds the template, and opens the workspace in Cursor.

---

### `rose list`

List existing workspaces and open one in Cursor.

```bash
rose list
```

Shows a fuzzy picker with workspace name, repos, and creation date.

---

### `rose edit [name]`

Add or remove repos from an existing workspace.

```bash
rose edit my-workspace
rose edit                    # infers workspace from cwd
rose edit my-workspace --force  # skip uncommitted-changes check
```

Pre-selects current repos. Adds/removes worktrees and updates the `.code-workspace` file.

---

### `rose org set <orgname>`

Change the GitHub organization and rebuild the repo cache.

```bash
rose org set MyOrg
```

---

### `rose repos sync`

Rebuild the local repo cache from GitHub.

```bash
rose repos sync
```

---

## Help

```bash
rose --help
rose <command> --help
```
