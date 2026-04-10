"""Tests for namespace sync."""

from pathlib import Path

import pytest

from nsctl.paths import namespace_sync_dir
from nsctl.sync import sync_namespace


def _create_git_namespace(name: str, root: Path, config_path: Path) -> Path:
    """Create a minimal namespace with git init for sync testing."""
    from nsctl.namespace import create_namespace

    return create_namespace(name, root=root, config_path=config_path)


@pytest.fixture
def nsctl_config(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "nsctl-config.toml"
    cfg_path.write_text(
        'schema_version = 1\ndevice_label = "test-device"\n'
        'default_namespace = ""\nnamespace_root = ""\n'
    )
    return cfg_path


@pytest.mark.slow
def test_sync_writes_log(tmp_path: Path, nsctl_config: Path) -> None:
    _create_git_namespace("sync-ns", tmp_path, nsctl_config)
    entry = sync_namespace("sync-ns", root=tmp_path, config_path=nsctl_config)

    assert entry.device == "test-device"
    assert entry.action == "sync"

    # Check sync log file was created
    sync_dir = namespace_sync_dir("sync-ns", tmp_path)
    log_files = list(sync_dir.glob("*.toml"))
    assert len(log_files) >= 1


@pytest.mark.slow
def test_sync_no_remote(tmp_path: Path, nsctl_config: Path) -> None:
    _create_git_namespace("noremote-ns", tmp_path, nsctl_config)
    entry = sync_namespace("noremote-ns", root=tmp_path, config_path=nsctl_config)
    # Should succeed with a note about no remote
    assert (
        "no remote" in entry.note.lower()
        or "skipped" in entry.note.lower()
        or entry.note == ""
    )
