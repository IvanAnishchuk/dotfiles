"""Tests for namespace health checks."""

from datetime import UTC, datetime
from pathlib import Path

from nsctl.doctor import CheckStatus, check_namespace
from nsctl.models import NamespaceConfig
from nsctl.paths import (
    namespace_gnupghome,
    namespace_gpg_id,
    namespace_sshdir,
    namespace_toml,
)


def _setup_minimal_ns(name: str, root: Path) -> None:
    """Create a minimal on-disk namespace for doctor checks."""
    repo = root / f"dotfiles-id-{name}"
    repo.mkdir(parents=True)
    (repo / "keys").mkdir()
    (repo / "keys" / "README.md").touch()

    cfg = NamespaceConfig(
        name=name,
        created_at=datetime.now(UTC),
        created_on="test",
        keystone_gpg_fingerprint="AABBCCDD" * 5,
    )
    cfg.save(namespace_toml(name, root))
    namespace_gpg_id(name, root).write_text("AABBCCDD" * 5 + "\n")

    gnupg = namespace_gnupghome(name, root)
    gnupg.mkdir(mode=0o700)

    ssh = namespace_sshdir(name, root)
    ssh.mkdir(mode=0o700)
    (ssh / "id_ed25519.pub").write_text("ssh-ed25519 AAAA test")


def test_healthy_namespace(tmp_path: Path) -> None:
    _setup_minimal_ns("healthy", tmp_path)
    health = check_namespace("healthy", tmp_path)

    assert health.worst == CheckStatus.PASS
    assert all(c.status == CheckStatus.PASS for c in health.checks)


def test_missing_gpg_id(tmp_path: Path) -> None:
    _setup_minimal_ns("no-gpgid", tmp_path)
    namespace_gpg_id("no-gpgid", tmp_path).unlink()

    health = check_namespace("no-gpgid", tmp_path)
    gpg_check = next(c for c in health.checks if c.name == ".gpg-id")
    assert gpg_check.status == CheckStatus.FAIL


def test_missing_gnupghome(tmp_path: Path) -> None:
    _setup_minimal_ns("no-gnupg", tmp_path)
    import shutil

    shutil.rmtree(namespace_gnupghome("no-gnupg", tmp_path))

    health = check_namespace("no-gnupg", tmp_path)
    gnupg_check = next(c for c in health.checks if c.name == "gnupghome")
    assert gnupg_check.status == CheckStatus.FAIL


def test_missing_ssh(tmp_path: Path) -> None:
    _setup_minimal_ns("no-ssh", tmp_path)
    import shutil

    shutil.rmtree(namespace_sshdir("no-ssh", tmp_path))

    health = check_namespace("no-ssh", tmp_path)
    ssh_check = next(c for c in health.checks if c.name == "ssh dir")
    assert ssh_check.status == CheckStatus.WARN


def test_expired_validity(tmp_path: Path) -> None:
    _setup_minimal_ns("expired", tmp_path)
    cfg = NamespaceConfig.load(namespace_toml("expired", tmp_path))
    cfg.lifecycle.valid_until = "2020-01-01T00:00:00+00:00"
    cfg.save(namespace_toml("expired", tmp_path))

    health = check_namespace("expired", tmp_path)
    val_check = next(c for c in health.checks if c.name == "validity")
    assert val_check.status == CheckStatus.WARN
