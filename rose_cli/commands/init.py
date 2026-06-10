from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import click

from rose_cli.ascii import ROSE_GREETING
from rose_cli.cache import save_repo_cache
from rose_cli.config import CONFIG_PATH, config_exists, expand_path, write_config
from rose_cli import github

DEFAULT_WORKSPACE = "~/workspaces"
DEFAULT_TEMPLATE = "~/.rose/templates/default"
DEFAULT_GITHUB_ORG = ""

DOCS_SKILL_CONTENT = """\
---
name: docs
description: >
  Document findings, plans, decisions, and investigations in the workspace
  docs folder. Use when the user asks to document something, create docs,
  write findings, or mentions /docs.
---

# Workspace Documentation

Create and maintain documentation in the workspace `docs/` folder.

## Target Location

**Find the workspace docs folder dynamically:**

1. Check the `Workspace Paths` in user_info for a path ending in `/docs`
2. That is your target documentation folder
3. Create all documentation files in that folder

The docs folder is shared across all repos in the workspace.

**Example paths:**
- `/Users/tristan.toupin/accloud-lde/workspaces/<workspace_id>/docs/`

**If no docs path is found in Workspace Paths:**
- Look for a `docs/` directory at the workspace root
- Use Glob to search for `docs/` folders if needed

## When to Use

Use this skill when the user:
- Says "/docs" followed by content to document
- Asks to "document this"
- Requests to create findings, plans, or decision records
- Says "write this down" or "keep track of this"

## Documentation Guidelines

### File Naming
- Use descriptive, kebab-case filenames: `implementation-plan.md`, `findings.md`
- Include topic or ticket reference when relevant: `clin-12345-findings.md`
- Date prefix for time-sensitive docs: `2026-04-02-meeting-notes.md`

### Content Structure

Adapt to the content type, but generally include:

**For findings/investigations:**
```markdown
# [Topic] - Findings

**Date**: YYYY-MM-DD
**Context**: Why this investigation was needed

## Summary
Brief overview of key findings

## Details
[Detailed findings organized by subtopic]

## Conclusions
What we learned and next steps
```

**For decisions:**
```markdown
# [Decision Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded

## Context
What problem or question prompted this decision?

## Decision
What we decided to do

## Rationale
Why we made this choice

## Alternatives Considered
What other options we evaluated and why we didn't choose them
```

**For implementation plans:**
```markdown
# [Feature/Task] - Implementation Plan

**Date**: YYYY-MM-DD

## Overview
What we're building and why

## Approach
High-level strategy

## Steps
1. Step one
2. Step two
...

## Considerations
- Technical constraints
- Trade-offs
- Open questions
```

### Best Practices

1. **Be concise**: Focus on key information
2. **Include context**: Future readers should understand why this exists
3. **Use dates**: Add date/timestamp to time-sensitive content
4. **Update in place**: When information changes, edit the existing file
5. **Link to code**: Reference specific files/functions when relevant
"""


def check_github_cli() -> bool:
    """Check gh CLI installation and auth. Returns True if fully authed."""
    if not shutil.which("gh"):
        click.echo("  ⚠  GitHub CLI not found. Install it: https://cli.github.com")
        return False

    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo("  ⚠  GitHub CLI not authenticated. Run: gh auth login")
        return False

    click.echo("  ✓  GitHub CLI authenticated")
    return True


def scaffold_template(template_path: Path) -> None:
    """Create default workspace template with docs skill."""
    docs_dir = template_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / ".gitkeep").write_text("")

    skill_dir = docs_dir / ".cursor" / "skills" / "docs"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(DOCS_SKILL_CONTENT)


@click.command()
def init() -> None:
    """Initialize Rose environment."""
    click.echo(ROSE_GREETING)

    # GitHub CLI check
    click.echo("Checking prerequisites...")
    gh_ok = check_github_cli()
    click.echo()

    # Existing config check
    if config_exists():
        click.echo(f"  ⚠  Config already exists at {CONFIG_PATH}")
        if not click.confirm("  Overwrite?", default=False):
            click.echo("  Aborted.")
            return
        click.echo()

    # Workspace path
    raw_workspace = click.prompt(
        "Where should worktrees live?",
        default=DEFAULT_WORKSPACE,
    )
    workspace_path = expand_path(raw_workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"  ✓  Workspace directory ready: {workspace_path}")
    click.echo()

    # Template path
    raw_template = click.prompt(
        "Workspace template path",
        default=DEFAULT_TEMPLATE,
    )
    template_path = expand_path(raw_template)
    if template_path.is_dir():
        click.echo(f"  ✓  Using existing template: {template_path}")
    else:
        scaffold_template(template_path)
        click.echo(f"  ✓  Default template created: {template_path}")
    click.echo()

    # GitHub org
    org = click.prompt(
        "GitHub organization name",
        default=DEFAULT_GITHUB_ORG,
    )
    click.echo()

    # Write config
    write_config(str(workspace_path), str(template_path), org)
    click.echo(f"  ✓  Config saved to {CONFIG_PATH}")

    # Build initial repo cache
    click.echo(f"  Fetching repo list for {org}...")
    try:
        repo_names = github.repo_list(org)
        save_repo_cache(org, repo_names)
        click.echo(f"  ✓  {len(repo_names)} repos cached")
    except RuntimeError as exc:
        click.echo(f"  ⚠  Could not fetch repos: {exc}")
        click.echo("     Run 'rose repos sync' later to build the cache.")
    click.echo()

    # Summary
    click.echo("─" * 50)
    click.echo(f"  ✓  Workspace path:  {workspace_path}")
    click.echo(f"  ✓  Template path:   {template_path}")
    click.echo(f"  ✓  GitHub org:      {org}")
    if not gh_ok:
        click.echo("  ⚠  GitHub CLI needs attention (see above)")
    click.echo()
    click.echo("  All set! Rose is ready to grow! 🌹")
