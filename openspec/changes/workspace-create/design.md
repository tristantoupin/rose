# Design: workspace-create

## Architecture

### File Layout

```
~/.rose/
├── config.toml                    # Updated: adds [github] section
├── repo-cache.json                # { org, repos, cached_at }
├── history.json                   # { recent_repos: [...] }  max 20
└── repos/
    ├── org__api-abc.git/     # bare clone
    └── org__frontend.git/         # bare clone

~/workspaces/
└── my-feature/
    ├── my-feature.code-workspace  # VSCode/Cursor workspace file
    ├── docs/                      # from template
    ├── .cursor/                   # from template
    └── repos/
        ├── api-abc/          # git worktree on branch "my-feature"
        └── frontend/              # git worktree on branch "my-feature"
```

### Config Schema (`~/.rose/config.toml`)

```toml
[workspace]
path = "/absolute/path/to/workspaces"

[template]
path = "~/.rose/templates/default"

[github]
org = "myorg"
```

### Cache Files

**`~/.rose/repo-cache.json`**
```json
{
  "org": "myorg",
  "repos": ["myorg/api-abc", "myorg/frontend", "..."],
  "cached_at": "2026-06-09T20:00:00"
}
```
Built by `gh repo list <org> --limit 9999 --json nameWithOwner`.
Invalidated when org changes or `rose repos sync` / `--refresh` flag used.

**`~/.rose/history.json`**
```json
{
  "recent_repos": ["myorg/api-abc", "myorg/frontend"]
}
```
Max 20 entries, FIFO. Updated after each successful `workspace create`.

### `.code-workspace` File

Standard VSCode workspace JSON with a `rose` metadata key (ignored by Cursor):

```json
{
  "folders": [
    { "path": "repos/api-abc", "name": "api-abc" },
    { "path": "repos/frontend",     "name": "frontend" },
    { "path": "docs",               "name": "docs" }
  ],
  "settings": {},
  "rose": {
    "name": "my-feature",
    "created": "2026-06-09",
    "repos": {
      "myorg/api-abc": { "branch": "my-feature", "default_branch": "main" },
      "myorg/frontend":     { "branch": "my-feature", "default_branch": "develop" }
    }
  }
}
```

## Command Flow

### `rose workspace create`

```
rose workspace create [--refresh]
│
├─ 1. Load config — abort with guidance if [github].org missing
│
├─ 2. Load repo cache
│     ├─ --refresh flag OR cache missing/stale (>24h) OR org mismatch
│     │   └─ "Fetching repo list for <org>..." spinner
│     │      gh repo list <org> --limit 9999 --json nameWithOwner
│     │      Write ~/.rose/repo-cache.json
│     └─ Cache fresh → load from file
│
├─ 3. Prompt: workspace name
│     No default. Validates:
│     - Non-empty
│     - No path separators or special chars (kebab/snake/alphanumeric only)
│     - Target dir ~/workspaces/<name>/ does not already exist
│
├─ 4. Prompt: branch name
│     Default = workspace name
│     "Feature branch name [my-feature]: "
│
├─ 5. Repo selection — InquirerPy fuzzy multiselect
│     Choices:
│       - Recent repos first (★ prefix, from history.json)
│       - Then remaining cached repos
│       - Always last entry: "🔍 Not there? Search GitHub for..."
│     User types to filter, arrows to navigate, space to select,
│     enter to confirm. Must select at least 1 repo.
│
│     If "Not there?" selected:
│       Prompt: "Search term: "
│       gh search repos "<term> in:name" --owner <org> --limit 20
│       Show results in a second InquirerPy fuzzy prompt
│       Merge selections. Add new repos to cache.
│
├─ 6. Validate branch name uniqueness
│     For each selected repo:
│       Check bare clone at ~/.rose/repos/<bare-name>/
│       If clone exists: git -C <bare> branch --list <branch-name>
│       If branch already exists → abort:
│         "✗  Branch '<name>' already exists in <repo>. Choose a different name."
│
├─ 7. Ensure bare clones + fetch
│     For each repo:
│       Bare path = ~/.rose/repos/<org>__<repo>.git
│       If missing: "Cloning <repo>..." → git clone --bare <ssh-url> <bare-path>
│       If exists:  "Updating <repo>..." → git -C <bare-path> fetch --prune
│
├─ 8. Detect default branches
│     For each repo:
│       gh repo view <full-name> --json defaultBranchRef --jq '.defaultBranchRef.name'
│
├─ 9. Create workspace folder + scaffold template
│     mkdir ~/workspaces/<name>/repos/
│     shutil.copytree(template_path, workspace_path, dirs_exist_ok=True)
│     (copytree skips repos/ — template has no repos/ folder)
│
├─ 10. Create worktrees
│      For each repo:
│        git -C <bare-path> worktree add \
│          <workspace>/repos/<repo-name> \
│          -b <branch-name> \
│          origin/<default-branch>
│        "  ✓  <repo-name> → <branch-name>"
│
├─ 11. Write .code-workspace file
│       JSON: folders + rose metadata (name, created, repos map)
│
├─ 12. Update history.json
│       Prepend selected repos, deduplicate, trim to 20
│
├─ 13. Open in Cursor
│       subprocess: cursor <workspace>/<name>.code-workspace
│       "  ✓  Opening in Cursor..."
│
└─ 14. Summary
       ─────────────────────────────
         ✓  Workspace:  ~/workspaces/my-feature/
         ✓  Branch:     my-feature
         ✓  Repos (2):  api-abc, frontend
         ✓  Opening in Cursor...
```

### `rose org set <orgname>`

```
rose org set myorg
│
├─ Update [github] org in config.toml
├─ "Fetching repo list for myorg..." spinner
├─ gh repo list myorg --limit 9999 --json nameWithOwner
├─ Write new repo-cache.json
└─ "  ✓  Org set to myorg (623 repos cached)"
```

### `rose repos sync`

```
rose repos sync
│
├─ Read org from config — abort if missing
├─ "Syncing repo list for <org>..." spinner
├─ gh repo list <org> --limit 9999 --json nameWithOwner
├─ Write new repo-cache.json
└─ "  ✓  Repo cache updated (623 repos)"
```

### `rose init` changes

After existing prompts, add:

```
├─ Prompt: GitHub organization
│     "GitHub organization name: "
│     Stored in [github] org
│
└─ Build initial repo cache
      "Fetching repo list for <org>..."
      gh repo list <org> --limit 9999
      Write ~/.rose/repo-cache.json
      "  ✓  623 repos cached"
```

## Implementation Details

### InquirerPy Fuzzy Picker

```python
from InquirerPy import inquirer

# Build choices: recent first (★), then rest
recent = load_history()
cached = load_cache()
rest = [r for r in cached if r not in recent]
choices = [f"★ {r}" for r in recent] + rest + ["🔍 Not there? Search GitHub..."]

selected = inquirer.fuzzy(
    message="Select repos:",
    choices=choices,
    multiselect=True,
    validate=lambda result: len(result) > 0,
    invalid_message="Select at least one repo",
).execute()
```

Strip the `★ ` prefix when storing selections. Handle `"🔍 Not there?..."` as a trigger for live search.

### Bare Clone Naming

`myorg/api-abc` → `~/.rose/repos/myorg__api-abc.git`

Double underscore separates org from repo name. Avoids path nesting.

### SSH vs HTTPS

Use `gh repo view <name> --json sshUrl --jq '.sshUrl'` to get the correct clone URL. Respects user's `gh` auth setup (SSH keys or tokens).

### Worktree creation command

```bash
git -C ~/.rose/repos/myorg__api-abc.git \
    worktree add \
    ~/workspaces/my-feature/repos/api-abc \
    -b my-feature \
    origin/main
```

### Branch conflict check

```bash
git -C <bare-path> branch --list <branch-name>
# empty output = branch doesn't exist = safe to create
```

### `cursor` detection

```python
import shutil
cursor_bin = shutil.which("cursor")
if not cursor_bin:
    click.echo("  ⚠  'cursor' not found in PATH. Open manually:")
    click.echo(f"     cursor {workspace_file}")
    return
subprocess.Popen([cursor_bin, str(workspace_file)])
```

Non-blocking (`Popen` not `run`) — rose exits after launching.

### New Dependencies

- `InquirerPy>=0.3.4` — fuzzy interactive picker

## Code Organization

```
rose_cli/
├── main.py                  # Register workspace + org + repos groups
├── commands/
│   ├── init.py              # Updated: org prompt + cache build
│   ├── workspace/
│   │   ├── __init__.py      # workspace Click group
│   │   └── create.py        # workspace create command
│   ├── org/
│   │   ├── __init__.py      # org Click group
│   │   └── set.py           # org set command
│   └── repos/
│       ├── __init__.py      # repos Click group
│       └── sync.py          # repos sync command
├── config.py                # Updated: read/write [github] section
├── cache.py                 # repo-cache.json + history.json helpers
├── git.py                   # bare clone, fetch, worktree, branch check helpers
├── github.py                # gh CLI wrappers (repo list, repo view, search)
└── ascii.py                 # Rose ASCII art (unchanged)
```
