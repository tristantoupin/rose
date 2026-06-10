# Tasks: list-workspaces-command

## Implementation Tasks

- [x] 1. Extract shared helpers from `create.py` into `rose_cli/commands/workspace/_helpers.py` (`_load_and_validate_config`, `_open_cursor`)
- [x] 2. Update `create.py` to import from `_helpers.py` (remove extracted functions, add imports)
- [x] 3. Implement `rose_cli/commands/workspace/list.py` with `WorkspaceInfo` dataclass, `_scan_workspaces`, `_build_label`, `_pick_workspace`, and `list_cmd`
- [x] 4. Register `list_cmd` in `rose_cli/commands/workspace/__init__.py`
- [x] 5. Manual smoke test: `rose workspace list` end-to-end with at least one existing workspace
