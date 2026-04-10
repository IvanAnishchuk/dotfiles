"""Tests for SSH key generation."""

from pathlib import Path

import pytest

from nsctl.keys import generate_ssh_keypair


def test_generate_ssh_keypair(tmp_path: Path) -> None:
    ssh_dir = tmp_path / ".ssh-test"
    priv, pub, fpr = generate_ssh_keypair(ssh_dir, comment="test@host")

    assert priv.exists()
    assert pub.exists()
    assert fpr.startswith("SHA256:")

    # Check permissions
    assert oct(priv.stat().st_mode)[-3:] == "600"

    # Check public key format
    pub_content = pub.read_text()
    assert pub_content.startswith("ssh-ed25519 ")
    assert "test@host" in pub_content


def test_refuse_overwrite(tmp_path: Path) -> None:
    ssh_dir = tmp_path / ".ssh-test"
    generate_ssh_keypair(ssh_dir)

    with pytest.raises(FileExistsError):
        generate_ssh_keypair(ssh_dir)


def test_custom_filename(tmp_path: Path) -> None:
    ssh_dir = tmp_path / ".ssh-test"
    priv, pub, _ = generate_ssh_keypair(ssh_dir, filename="id_deploy")

    assert priv.name == "id_deploy"
    assert pub.name == "id_deploy.pub"
