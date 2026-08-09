from __future__ import annotations

import os
from pathlib import Path

ROSE_HOME = Path.home() / ".rose"
CONFIG_PATH = ROSE_HOME / "config.toml"


def config_exists() -> bool:
    return CONFIG_PATH.is_file()


def read_config() -> dict[str, dict[str, str]]:
    """Parse the simple two-section TOML config."""
    if not CONFIG_PATH.is_file():
        return {}

    config: dict[str, dict[str, str]] = {}
    current_section = ""
    for line in CONFIG_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            config[current_section] = {}
        elif "=" in line and current_section:
            key, _, value = line.partition("=")
            value = value.strip().strip('"')
            config[current_section][key.strip()] = value
    return config


def write_config(
    workspace_path: str,
    template_path: str,
    org: str = "",
    vault_path: str = "",
) -> None:
    """Write config as simple TOML."""
    ROSE_HOME.mkdir(parents=True, exist_ok=True)
    content = (
        f'[workspace]\npath = "{workspace_path}"\n\n'
        f'[template]\npath = "{template_path}"\n'
    )
    if org:
        content += f'\n[github]\norg = "{org}"\n'
    if vault_path:
        content += f'\n[vault]\npath = "{vault_path}"\n'
    CONFIG_PATH.write_text(content)


def get_org() -> str:
    """Return configured GitHub org, or empty string if not set."""
    config = read_config()
    return config.get("github", {}).get("org", "")


def set_org(org: str) -> None:
    """Update [github] org in config, preserving other sections."""
    config = read_config()
    workspace_path = config.get("workspace", {}).get("path", "")
    template_path = config.get("template", {}).get("path", "")
    vault_path = config.get("vault", {}).get("path", "")
    write_config(workspace_path, template_path, org, vault_path)


def get_vault_path() -> Path | None:
    """Return configured vault path, or None if no vault is set up."""
    raw = read_config().get("vault", {}).get("path", "")
    return expand_path(raw) if raw else None


def set_vault_path(path: str) -> None:
    """Update [vault] path in config, preserving other sections."""
    config = read_config()
    workspace_path = config.get("workspace", {}).get("path", "")
    template_path = config.get("template", {}).get("path", "")
    org = config.get("github", {}).get("org", "")
    write_config(workspace_path, template_path, org, path)


def expand_path(path: str) -> Path:
    return Path(os.path.expanduser(path))
