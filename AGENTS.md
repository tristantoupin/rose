# Rose Agent Instructions

## Lean Scope

- Do only what the user asked.
- Do not add out-of-scope changes, refactors, or nice-to-haves.
- Do not introduce premature abstractions or speculative future-proofing.
- If a requirement is unclear or its scope is ambiguous, ask rather than assume.

## CLI Documentation

When adding or changing a `rose` CLI command under `rose_cli/`:

1. Update `.agents/skills/rose/SKILL.md` with the agent-facing command reference, including flags, TTY requirements, and workflows. The same skill is exposed to Cursor through the `.cursor/skills` compatibility alias.
2. Update `README.md` with the corresponding user-facing install, upgrade, skill-installation, and command documentation.

Keep both files aligned with the command surface. Prefer documenting non-interactive flags for agent use.
