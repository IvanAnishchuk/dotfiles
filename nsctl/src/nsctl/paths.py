"""Path conventions for nsctl namespaces.

All path logic is centralized here so the rest of the codebase
never constructs namespace paths ad-hoc.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_NAMESPACE_ROOT = Path.home()
CONFIG_DIR = Path.home() / ".config" / "nsctl"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def namespace_repo_dir(name: str, root: Path | None = None) -> Path:
    return (root or DEFAULT_NAMESPACE_ROOT) / f"dotfiles-id-{name}"


def namespace_gnupghome(name: str, root: Path | None = None) -> Path:
    return (root or DEFAULT_NAMESPACE_ROOT) / f".gnupg-{name}"


def namespace_sshdir(name: str, root: Path | None = None) -> Path:
    return (root or DEFAULT_NAMESPACE_ROOT) / f".ssh-{name}"


def namespace_toml(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "namespace.toml"


def namespace_gpg_id(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / ".gpg-id"


def namespace_keys_dir(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "keys"


def namespace_devices_dir(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "devices"


def namespace_sync_dir(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "sync"


def namespace_bashrc_snippet(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "bashrc.d" / f"50-id-{name}.sh"


def namespace_ssh_config_snippet(name: str, root: Path | None = None) -> Path:
    return namespace_repo_dir(name, root) / "ssh" / "config.d" / f"10-id-{name}.conf"


def template_dir() -> Path:
    """Locate the template/ directory relative to the source tree."""
    return Path(__file__).resolve().parent.parent.parent / "template"


def discover_namespaces(root: Path | None = None) -> list[str]:
    """Find all dotfiles-id-* directories under root."""
    base = root or DEFAULT_NAMESPACE_ROOT
    if not base.is_dir():
        return []
    names = []
    for d in sorted(base.iterdir()):
        if d.is_dir() and d.name.startswith("dotfiles-id-"):
            name = d.name.removeprefix("dotfiles-id-")
            if name:
                names.append(name)
    return names
