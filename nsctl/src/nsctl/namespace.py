"""Namespace lifecycle operations: create, remove, list, disable, enable."""

from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from nsctl import gpg, keys
from nsctl.config import load_config
from nsctl.models import (
    KeyHistoryEntry,
    KeyKind,
    KeyLifecycle,
    KeyMetadata,
    KeyPurpose,
    NamespaceConfig,
)
from nsctl.paths import (
    discover_namespaces,
    namespace_bashrc_snippet,
    namespace_devices_dir,
    namespace_gnupghome,
    namespace_gpg_id,
    namespace_keys_dir,
    namespace_repo_dir,
    namespace_ssh_config_snippet,
    namespace_sshdir,
    namespace_sync_dir,
    namespace_toml,
    template_dir,
)


def _force_rmtree(d: Path) -> None:
    """Force-remove a directory tree, handling read-only git pack files."""
    subprocess.run(["rm", "-rf", str(d)], check=True)


def _fill_template(text: str, replacements: dict[str, str]) -> str:
    for key, val in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", val)
    return text


def _copy_template(
    src: Path, dst: Path, replacements: dict[str, str], *, rename_identity: str = ""
) -> None:
    """Copy a template file, filling placeholders. Refuses to overwrite."""
    if dst.exists():
        raise FileExistsError(f"Template target already exists: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    content = src.read_text()
    dst.write_text(_fill_template(content, replacements))


def create_namespace(
    name: str,
    *,
    root: Path | None = None,
    description: str = "",
    prompt_color: str = "green",
    config_path: Path | None = None,
) -> Path:
    """Create a new namespace. Returns the repo directory path.

    Refuses if any target directory already exists.
    """
    cfg = load_config(config_path)
    device = cfg.device_label
    now = datetime.now(UTC)

    repo_dir = namespace_repo_dir(name, root)
    gnupg_dir = namespace_gnupghome(name, root)
    ssh_dir = namespace_sshdir(name, root)

    for d in (repo_dir, gnupg_dir, ssh_dir):
        if d.exists():
            raise FileExistsError(f"Directory already exists: {d}")

    # 1. Create repo and git init
    repo_dir.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "-b", "master"],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )

    # 2. Generate GPG keypair
    gpg.init_gnupghome(gnupg_dir)
    ns_email = f"{name}@nsctl.local"
    fpr = gpg.generate_keypair(gnupg_dir, f"nsctl-{name}", ns_email)

    # 3. Generate SSH keypair
    comment = f"{name}@{device}"
    _, ssh_pub_path, ssh_fingerprint = keys.generate_ssh_keypair(
        ssh_dir, comment=comment
    )

    # 4. Write .gpg-id
    namespace_gpg_id(name, root).write_text(fpr + "\n")

    # 5. Fill and write templates
    tmpl = template_dir()
    replacements = {
        "NAME": name,
        "CREATED_AT": now.isoformat(),
        "DEVICE": device,
        "GPG_FINGERPRINT": fpr,
        "PROMPT_COLOR": prompt_color,
    }

    _copy_template(tmpl / ".gitignore", repo_dir / ".gitignore", replacements)

    # bashrc.d snippet
    tmpl_bashrc = tmpl / "bashrc.d" / "50-id-IDENTITY.sh.tmpl"
    _copy_template(tmpl_bashrc, namespace_bashrc_snippet(name, root), replacements)

    # ssh config.d snippet
    tmpl_ssh = tmpl / "ssh" / "config.d" / "10-id-IDENTITY.conf.tmpl"
    _copy_template(tmpl_ssh, namespace_ssh_config_snippet(name, root), replacements)

    # keys/ skeleton
    keys_dir = namespace_keys_dir(name, root)
    for sub in ("ssh", "gnupg", "gnupg/pubring", "gnupg/revocation"):
        (keys_dir / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmpl / "keys" / ".gitignore", keys_dir / ".gitignore")
    shutil.copy2(tmpl / "keys" / "README.md", keys_dir / "README.md")

    # devices/ skeleton
    devices_dir = namespace_devices_dir(name, root)
    devices_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmpl / "devices" / "README.md", devices_dir / "README.md")

    # sync/ skeleton
    sync_dir = namespace_sync_dir(name, root)
    sync_dir.mkdir(parents=True, exist_ok=True)
    (sync_dir / ".gitkeep").touch()

    # 6. Write namespace.toml via the model
    ns_config = NamespaceConfig(
        name=name,
        description=description,
        created_at=now,
        created_on=device,
        keystone_gpg_fingerprint=fpr,
    )
    ns_config.prompt.color = prompt_color
    ns_config.prompt.marker = name
    ns_config.save(namespace_toml(name, root))

    # 7. Write key metadata
    ssh_meta = KeyMetadata(
        kind=KeyKind.SSH,
        algorithm="ed25519",
        fingerprint_sha256=ssh_fingerprint,
        public_key=ssh_pub_path.read_text().strip(),
        comment=comment,
        lifecycle=KeyLifecycle(created_at=now, created_on=device),
        purpose=KeyPurpose(description=f"SSH key for namespace {name}"),
        history=[
            KeyHistoryEntry(at=now, device=device, action="created", note="nsctl new")
        ],
    )
    ssh_meta.save(keys_dir / "ssh" / "id_ed25519.toml")

    gpg_meta = KeyMetadata(
        kind=KeyKind.GPG_PRIMARY,
        algorithm="ed25519+cv25519",
        fingerprint_sha256=fpr,
        comment=f"nsctl-{name} <{ns_email}>",
        lifecycle=KeyLifecycle(created_at=now, created_on=device),
        purpose=KeyPurpose(
            description=f"GPG primary key for namespace {name}", keystone=True
        ),
        history=[
            KeyHistoryEntry(at=now, device=device, action="created", note="nsctl new")
        ],
    )
    gpg_meta.save(keys_dir / "gnupg" / "keystone.toml")

    # 8. Export device GPG pubkey + SSH pubkey to devices/
    gpg_pub = gpg.export_public_key(gnupg_dir, fpr)
    (devices_dir / f"{device}.gpg-pub").write_text(gpg_pub)
    shutil.copy2(ssh_pub_path, devices_dir / f"{device}.deploy-key.pub")

    # 9. Copy SSH pubkey to keys/ for backup reference
    shutil.copy2(ssh_pub_path, keys_dir / "ssh" / "id_ed25519.pub")

    # 10. Git add and commit
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            f"Initial namespace: {name}",
        ],
        cwd=repo_dir,
        capture_output=True,
        check=True,
    )

    return repo_dir


def remove_namespace(
    name: str, *, root: Path | None = None, force: bool = False
) -> None:
    """Remove a namespace and its per-namespace directories."""
    repo_dir = namespace_repo_dir(name, root)
    gnupg_dir = namespace_gnupghome(name, root)
    ssh_dir = namespace_sshdir(name, root)

    if not repo_dir.exists():
        raise FileNotFoundError(f"Namespace not found: {repo_dir}")

    if not force:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir,
            capture_output=True,
            check=True,
        )
        if result.stdout.strip():
            raise RuntimeError(
                f"Namespace {name} has uncommitted changes. Use --force to override."
            )

    for d in (repo_dir, gnupg_dir, ssh_dir):
        if d.exists():
            _force_rmtree(d)


def list_namespaces(root: Path | None = None) -> list[NamespaceConfig]:
    """List all discovered namespaces with their config."""
    result = []
    for name in discover_namespaces(root):
        toml_path = namespace_toml(name, root)
        if toml_path.exists():
            result.append(NamespaceConfig.load(toml_path))
    return result


def disable_namespace(name: str, *, root: Path | None = None) -> None:
    toml_path = namespace_toml(name, root)
    if not toml_path.exists():
        raise FileNotFoundError(f"Namespace not found: {name}")
    cfg = NamespaceConfig.load(toml_path)
    cfg.disabled = True
    cfg.save(toml_path)


def enable_namespace(name: str, *, root: Path | None = None) -> None:
    toml_path = namespace_toml(name, root)
    if not toml_path.exists():
        raise FileNotFoundError(f"Namespace not found: {name}")
    cfg = NamespaceConfig.load(toml_path)
    cfg.disabled = False
    cfg.save(toml_path)
