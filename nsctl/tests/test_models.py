"""Tests for pydantic models — TOML round-trip."""

from datetime import UTC, datetime
from pathlib import Path

from nsctl.models import (
    GlobalConfig,
    KeyHistoryEntry,
    KeyKind,
    KeyLifecycle,
    KeyMetadata,
    NamespaceConfig,
)


def test_namespace_config_roundtrip(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    cfg = NamespaceConfig(
        name="test-ns",
        description="A test",
        created_at=now,
        created_on="test-device",
        keystone_gpg_fingerprint="ABCD1234",
    )
    cfg.prompt.color = "blue"
    cfg.prompt.marker = "test-ns"

    path = tmp_path / "namespace.toml"
    cfg.save(path)

    loaded = NamespaceConfig.load(path)
    assert loaded.name == "test-ns"
    assert loaded.description == "A test"
    assert loaded.keystone_gpg_fingerprint == "ABCD1234"
    assert loaded.prompt.color == "blue"
    assert loaded.encryption.backend == "gpg"
    assert loaded.disabled is False


def test_namespace_config_disabled(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    cfg = NamespaceConfig(name="x", created_at=now, created_on="d")
    cfg.disabled = True
    path = tmp_path / "ns.toml"
    cfg.save(path)
    loaded = NamespaceConfig.load(path)
    assert loaded.disabled is True


def test_key_metadata_roundtrip(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    meta = KeyMetadata(
        kind=KeyKind.SSH,
        algorithm="ed25519",
        fingerprint_sha256="SHA256:abc",
        public_key="ssh-ed25519 AAAA test",
        comment="test@device",
        lifecycle=KeyLifecycle(created_at=now, created_on="device"),
        history=[
            KeyHistoryEntry(at=now, device="device", action="created", note="test"),
        ],
    )
    path = tmp_path / "key.toml"
    meta.save(path)

    loaded = KeyMetadata.load(path)
    assert loaded.kind == KeyKind.SSH
    assert loaded.algorithm == "ed25519"
    assert loaded.fingerprint_sha256 == "SHA256:abc"
    assert len(loaded.history) == 1
    assert loaded.history[0].action == "created"


def test_global_config_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    cfg = GlobalConfig.load(path)  # file doesn't exist
    assert cfg.device_label == ""
    assert cfg.default_namespace == ""


def test_global_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    cfg = GlobalConfig(device_label="myhost", default_namespace="personal")
    cfg.save(path)
    loaded = GlobalConfig.load(path)
    assert loaded.device_label == "myhost"
    assert loaded.default_namespace == "personal"
