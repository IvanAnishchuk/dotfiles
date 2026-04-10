"""Tests for switch/deactivate env generation."""

from datetime import UTC, datetime
from pathlib import Path

from nsctl.models import NamespaceConfig
from nsctl.paths import namespace_toml
from nsctl.switch import generate_deactivate_env, generate_switch_env


def _create_minimal_ns(name: str, root: Path) -> None:
    """Create just enough on disk for switch to work (no GPG needed)."""
    repo = root / f"dotfiles-id-{name}"
    repo.mkdir(parents=True)
    cfg = NamespaceConfig(
        name=name,
        created_at=datetime.now(UTC),
        created_on="test",
        keystone_gpg_fingerprint="AABB",
    )
    cfg.prompt.color = "red"
    cfg.prompt.marker = name
    cfg.save(namespace_toml(name, root))


def test_switch_env(tmp_path: Path) -> None:
    _create_minimal_ns("sw-test", tmp_path)
    output = generate_switch_env("sw-test", root=tmp_path)

    assert 'export DOTFILES_ID="sw-test"' in output
    assert f'export GNUPGHOME="{tmp_path}/.gnupg-sw-test"' in output
    assert f'export PASSWORD_STORE_DIR="{tmp_path}/dotfiles-id-sw-test"' in output
    assert 'export NSCTL_PROMPT_COLOR="red"' in output
    assert 'export NSCTL_PROMPT_MARKER="sw-test"' in output


def test_switch_saves_previous(tmp_path: Path, monkeypatch) -> None:
    _create_minimal_ns("prev-test", tmp_path)
    monkeypatch.setenv("GNUPGHOME", "/old/gnupg")
    output = generate_switch_env("prev-test", root=tmp_path)
    assert 'export NSCTL_SAVED_GNUPGHOME="/old/gnupg"' in output


def test_switch_disabled_fails(tmp_path: Path) -> None:
    _create_minimal_ns("dis-test", tmp_path)
    cfg = NamespaceConfig.load(namespace_toml("dis-test", tmp_path))
    cfg.disabled = True
    cfg.save(namespace_toml("dis-test", tmp_path))

    import pytest

    with pytest.raises(RuntimeError, match="disabled"):
        generate_switch_env("dis-test", root=tmp_path)


def test_deactivate_env(monkeypatch) -> None:
    monkeypatch.setenv("NSCTL_SAVED_DOTFILES_ID", "old-ns")
    monkeypatch.setenv("NSCTL_SAVED_GNUPGHOME", "/old/gnupg")
    monkeypatch.setenv("NSCTL_SAVED_PASSWORD_STORE_DIR", "")
    monkeypatch.delenv("NSCTL_SAVED_VIRTUAL_ENV", raising=False)

    output = generate_deactivate_env()
    assert 'export DOTFILES_ID="old-ns"' in output
    assert 'export GNUPGHOME="/old/gnupg"' in output
    assert "unset NSCTL_PROMPT_MARKER" in output
