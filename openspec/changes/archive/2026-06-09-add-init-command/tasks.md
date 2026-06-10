# Tasks: add-init-command

## Implementation Tasks

- [x] 1. Create module structure (`rose_cli/commands/`, `rose_cli/config.py`, `rose_cli/ascii.py`)
- [x] 2. Add Rose ASCII art constant in `rose_cli/ascii.py`
- [x] 3. Implement config read/write helpers in `rose_cli/config.py` (hand-written TOML, `~/.rose/config.toml`)
- [x] 4. Implement `gh` auth check helper (shutil.which + subprocess for `gh auth status`)
- [x] 5. Implement default template scaffolding (create dirs + write docs SKILL.md)
- [x] 6. Implement `rose init` command in `rose_cli/commands/init.py` (greeting → gh check → overwrite check → prompts → scaffold → write config → summary)
- [x] 7. Register init command in `rose_cli/main.py`
- [x] 8. Manual smoke test: `rose init` end-to-end
