"""Encryption backend protocol for nsctl."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EncryptionBackend(Protocol):
    def encrypt(self, plaintext: bytes, recipients: list[str]) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> bytes: ...
    def list_recipients(self) -> list[str]: ...
