# Proposal: list-workspaces-command

## What

Add a `rose workspace list` subcommand that:

1. Scans the configured workspace root for existing workspaces
2. Presents a fuzzy-searchable interactive list
3. Lets the user select one workspace to open in Cursor

## Why

`rose workspace create` is the only workspace action today. There's no way to see what workspaces exist or jump back into one. Users must manually `ls` their workspace root and then run `cursor <path>/<name>.code-workspace`. The `list` command closes this gap — it becomes the daily driver for resuming work.

## Scope

- Single new Click subcommand: `rose workspace list`
- Scans `workspace.path` from config for subdirectories containing a `.code-workspace` file
- Reads `rose.name`, `rose.created`, and `rose.repos` metadata from each `.code-workspace` to show rich labels
- InquirerPy fuzzy picker (consistent with `workspace create`) — single-select
- Opens the selected workspace in Cursor using the existing `_open_cursor` helper
- Always opens the selected workspace in Cursor

## Out of Scope

- Deleting or archiving workspaces
- Filtering by repo or branch
- Renaming workspaces
- Sorting options
