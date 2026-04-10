"""GPG encryption backend."""

from __future__ import annotations

from pathlib import Path

from nsctl import gpg as gpg_ops


class GpgBackend:
    def __init__(self, gnupghome: Path) -> None:
        self.gnupghome = gnupghome

    def encrypt(self, plaintext: bytes, recipients: list[str]) -> bytes:
        return gpg_ops.encrypt_to_recipients(self.gnupghome, recipients, plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        return gpg_ops.decrypt(self.gnupghome, ciphertext)

    def list_recipients(self) -> list[str]:
        keys = gpg_ops.list_keys(self.gnupghome)
        return [k.fingerprint for k in keys]
