"""End-to-end integration tests: new -> switch -> sync -> doctor -> remove."""

from pathlib import Path

import pytest

from nsctl.doctor import CheckStatus, check_namespace
from nsctl.namespace import create_namespace, list_namespaces, remove_namespace
from nsctl.paths import (
    namespace_gnupghome,
    namespace_repo_dir,
    namespace_sshdir,
)
from nsctl.switch import generate_switch_env
from nsctl.sync import sync_namespace


@pytest.fixture
def nsctl_config(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "nsctl-config.toml"
    cfg_path.write_text(
        'schema_version = 1\ndevice_label = "integration-device"\n'
        'default_namespace = ""\nnamespace_root = ""\n'
    )
    return cfg_path


@pytest.mark.integration
@pytest.mark.slow
def test_full_lifecycle(tmp_path: Path, nsctl_config: Path) -> None:
    """Create -> list -> switch -> sync -> doctor -> remove."""
    name = "integ-test"

    # CREATE
    repo = create_namespace(
        name, root=tmp_path, description="integration test", config_path=nsctl_config
    )
    assert repo.exists()
    assert (repo / "namespace.toml").exists()

    # LIST
    namespaces = list_namespaces(tmp_path)
    assert any(ns.name == name for ns in namespaces)

    # SWITCH
    env_output = generate_switch_env(name, root=tmp_path)
    assert f'export DOTFILES_ID="{name}"' in env_output

    # SYNC (local-only, no remote)
    entry = sync_namespace(name, root=tmp_path, config_path=nsctl_config)
    assert entry.action == "sync"

    # DOCTOR
    health = check_namespace(name, tmp_path)
    assert health.worst in (CheckStatus.PASS, CheckStatus.WARN)

    # REMOVE
    remove_namespace(name, root=tmp_path, force=True)
    assert not namespace_repo_dir(name, tmp_path).exists()
    assert not namespace_gnupghome(name, tmp_path).exists()
    assert not namespace_sshdir(name, tmp_path).exists()


@pytest.mark.integration
@pytest.mark.slow
def test_two_namespaces_coexist(tmp_path: Path, nsctl_config: Path) -> None:
    """Create two namespaces, verify they coexist and switch independently."""
    create_namespace(
        "ns-alpha", root=tmp_path, prompt_color="blue", config_path=nsctl_config
    )
    create_namespace(
        "ns-beta", root=tmp_path, prompt_color="red", config_path=nsctl_config
    )

    namespaces = list_namespaces(tmp_path)
    names = [ns.name for ns in namespaces]
    assert "ns-alpha" in names
    assert "ns-beta" in names

    env_a = generate_switch_env("ns-alpha", root=tmp_path)
    env_b = generate_switch_env("ns-beta", root=tmp_path)

    assert 'DOTFILES_ID="ns-alpha"' in env_a
    assert 'DOTFILES_ID="ns-beta"' in env_b
    assert 'NSCTL_PROMPT_COLOR="blue"' in env_a
    assert 'NSCTL_PROMPT_COLOR="red"' in env_b

    # Clean up
    remove_namespace("ns-alpha", root=tmp_path, force=True)
    remove_namespace("ns-beta", root=tmp_path, force=True)
