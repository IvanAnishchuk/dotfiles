"""Environment variable generation for namespace switching."""

from __future__ import annotations

import os
from pathlib import Path

from nsctl.models import NamespaceConfig
from nsctl.paths import namespace_gnupghome, namespace_repo_dir, namespace_toml


def generate_switch_env(name: str, *, root: Path | None = None) -> str:
    """Generate shell export lines for switching to a namespace.

    Output is meant to be eval'd by the shell wrapper.
    """
    toml_path = namespace_toml(name, root)
    if not toml_path.exists():
        raise FileNotFoundError(f"Namespace not found: {name}")
    cfg = NamespaceConfig.load(toml_path)
    if cfg.disabled:
        raise RuntimeError(
            f"Namespace {name} is disabled. Run `nsctl enable {name}` first."
        )

    repo = namespace_repo_dir(name, root)
    gnupg = namespace_gnupghome(name, root)

    lines = []

    # Save current values for deactivate
    for var in ("DOTFILES_ID", "GNUPGHOME", "PASSWORD_STORE_DIR", "VIRTUAL_ENV"):
        old = os.environ.get(var, "")
        lines.append(f'export NSCTL_SAVED_{var}="{old}"')

    lines.append(f'export DOTFILES_ID="{name}"')
    lines.append(f'export GNUPGHOME="{gnupg}"')
    lines.append(f'export PASSWORD_STORE_DIR="{repo}"')
    lines.append(f'export NSCTL_PROMPT_MARKER="{cfg.prompt.marker or name}"')
    lines.append(f'export NSCTL_PROMPT_COLOR="{cfg.prompt.color}"')

    return "\n".join(lines)


def generate_deactivate_env() -> str:
    """Generate shell lines to restore the pre-switch environment."""
    lines = []
    for var in ("DOTFILES_ID", "GNUPGHOME", "PASSWORD_STORE_DIR", "VIRTUAL_ENV"):
        saved = os.environ.get(f"NSCTL_SAVED_{var}", "")
        if saved:
            lines.append(f'export {var}="{saved}"')
        else:
            lines.append(f"unset {var}")
        lines.append(f"unset NSCTL_SAVED_{var}")

    lines.append("unset NSCTL_PROMPT_MARKER")
    lines.append("unset NSCTL_PROMPT_COLOR")
    return "\n".join(lines)
