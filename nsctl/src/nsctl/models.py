"""Pydantic models for nsctl configuration and metadata."""

from __future__ import annotations

import tomllib
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import tomli_w
from pydantic import BaseModel, Field


class EncryptionBackendType(StrEnum):
    GPG = "gpg"


class KeyKind(StrEnum):
    SSH = "ssh"
    GPG_SIGN = "gpg-sign"
    GPG_ENCRYPT = "gpg-encrypt"
    GPG_PRIMARY = "gpg-primary"


# --- NamespaceConfig ---


class LifecycleConfig(BaseModel):
    valid_until: str = ""
    rotation_cadence_days: int = 365


class PromptConfig(BaseModel):
    color: str = "green"
    marker: str = ""


class EncryptionConfig(BaseModel):
    backend: EncryptionBackendType = EncryptionBackendType.GPG


class NamespaceConfig(BaseModel):
    schema_version: int = 1
    name: str
    description: str = ""
    created_at: datetime
    created_on: str
    keystone_gpg_fingerprint: str = ""
    disabled: bool = False

    lifecycle: LifecycleConfig = Field(default_factory=LifecycleConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)
    encryption: EncryptionConfig = Field(default_factory=EncryptionConfig)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json", exclude_none=True)
        path.write_text(tomli_w.dumps(data))

    @classmethod
    def load(cls, path: Path) -> NamespaceConfig:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


# --- KeyMetadata ---


class KeyHistoryEntry(BaseModel):
    at: datetime
    device: str
    action: str
    note: str = ""


class KeyPurpose(BaseModel):
    description: str = ""
    hardware_backed: bool = False
    keystone: bool = False


class KeyLifecycle(BaseModel):
    created_at: datetime
    created_on: str
    rotated_at: datetime | None = None
    rotation_cadence_days: int = 365
    expires_at: str = ""


class KeyRegistrations(BaseModel):
    github: list[str] = Field(default_factory=list)
    servers: list[str] = Field(default_factory=list)


class KeyMetadata(BaseModel):
    schema_version: int = 1
    kind: KeyKind
    algorithm: str
    fingerprint_sha256: str = ""
    public_key: str = ""
    comment: str = ""

    lifecycle: KeyLifecycle
    purpose: KeyPurpose = Field(default_factory=KeyPurpose)
    registrations: KeyRegistrations = Field(default_factory=KeyRegistrations)
    history: list[KeyHistoryEntry] = Field(default_factory=list)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json", exclude_none=True)
        path.write_text(tomli_w.dumps(data))

    @classmethod
    def load(cls, path: Path) -> KeyMetadata:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


# --- GlobalConfig ---


class GlobalConfig(BaseModel):
    schema_version: int = 1
    device_label: str = ""
    default_namespace: str = ""
    namespace_root: str = ""

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json", exclude_none=True)
        path.write_text(tomli_w.dumps(data))

    @classmethod
    def load(cls, path: Path) -> GlobalConfig:
        if not path.exists():
            return cls()
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


# --- SyncLogEntry ---


class SyncLogEntry(BaseModel):
    timestamp: datetime
    device: str
    action: str
    commit_before: str = ""
    commit_after: str = ""
    note: str = ""
