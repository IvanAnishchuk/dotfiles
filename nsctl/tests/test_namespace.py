"""Tests for namespace lifecycle operations."""

from pathlib import Path

import pytest

from nsctl.models import NamespaceConfig
from nsctl.namespace import (
    create_namespace,
    disable_namespace,
    enable_namespace,
    list_namespaces,
    remove_namespace,
)
from nsctl.paths import (
    namespace_gnupghome,
    namespace_repo_dir,
    namespace_sshdir,
    namespace_toml,
)


@pytest.fixture
def nsctl_config(tmp_path: Path) -> Path:
    """Write a minimal global config for tests."""
    cfg_path = tmp_path / "nsctl-config.toml"
    cfg_path.write_text(
        'schema_version = 1\ndevice_label = "test-device"\n'
        'default_namespace = ""\nnamespace_root = ""\n'
    )
    return cfg_path


@pytest.mark.slow
def test_create_namespace(tmp_path: Path, nsctl_config: Path) -> None:
    repo = create_namespace(
        "test-ns", root=tmp_path, prompt_color="blue", config_path=nsctl_config
    )

    assert repo.exists()
    assert (repo / "namespace.toml").exists()
    assert (repo / ".gpg-id").exists()
    assert (repo / "bashrc.d" / "50-id-test-ns.sh").exists()
    assert (repo / "ssh" / "config.d" / "10-id-test-ns.conf").exists()
    assert (repo / "keys" / "ssh" / "id_ed25519.toml").exists()
    assert (repo / "keys" / "gnupg" / "keystone.toml").exists()
    assert (repo / "devices" / "test-device.gpg-pub").exists()
    assert (repo / "devices" / "test-device.deploy-key.pub").exists()

    # Verify GNUPGHOME and SSH dir were created
    assert namespace_gnupghome("test-ns", tmp_path).exists()
    assert namespace_sshdir("test-ns", tmp_path).exists()

    # Verify namespace.toml content
    cfg = NamespaceConfig.load(namespace_toml("test-ns", tmp_path))
    assert cfg.name == "test-ns"
    assert cfg.prompt.color == "blue"
    assert len(cfg.keystone_gpg_fingerprint) == 40


@pytest.mark.slow
def test_create_refuses_existing(tmp_path: Path, nsctl_config: Path) -> None:
    create_namespace("dup-ns", root=tmp_path, config_path=nsctl_config)
    with pytest.raises(FileExistsError):
        create_namespace("dup-ns", root=tmp_path, config_path=nsctl_config)


@pytest.mark.slow
def test_remove_namespace(tmp_path: Path, nsctl_config: Path) -> None:
    create_namespace("rm-ns", root=tmp_path, config_path=nsctl_config)
    assert namespace_repo_dir("rm-ns", tmp_path).exists()

    remove_namespace("rm-ns", root=tmp_path)

    assert not namespace_repo_dir("rm-ns", tmp_path).exists()
    assert not namespace_gnupghome("rm-ns", tmp_path).exists()
    assert not namespace_sshdir("rm-ns", tmp_path).exists()


@pytest.mark.slow
def test_remove_refuses_dirty(tmp_path: Path, nsctl_config: Path) -> None:
    create_namespace("dirty-ns", root=tmp_path, config_path=nsctl_config)
    repo = namespace_repo_dir("dirty-ns", tmp_path)
    (repo / "newfile.txt").write_text("uncommitted")

    with pytest.raises(RuntimeError, match="uncommitted"):
        remove_namespace("dirty-ns", root=tmp_path)

    # Force should work
    remove_namespace("dirty-ns", root=tmp_path, force=True)
    assert not repo.exists()


@pytest.mark.slow
def test_list_namespaces(tmp_path: Path, nsctl_config: Path) -> None:
    create_namespace("ns-a", root=tmp_path, config_path=nsctl_config)
    create_namespace("ns-b", root=tmp_path, config_path=nsctl_config)

    namespaces = list_namespaces(tmp_path)
    names = [ns.name for ns in namespaces]
    assert "ns-a" in names
    assert "ns-b" in names


@pytest.mark.slow
def test_disable_enable(tmp_path: Path, nsctl_config: Path) -> None:
    create_namespace("toggle-ns", root=tmp_path, config_path=nsctl_config)

    disable_namespace("toggle-ns", root=tmp_path)
    cfg = NamespaceConfig.load(namespace_toml("toggle-ns", tmp_path))
    assert cfg.disabled is True

    enable_namespace("toggle-ns", root=tmp_path)
    cfg = NamespaceConfig.load(namespace_toml("toggle-ns", tmp_path))
    assert cfg.disabled is False
