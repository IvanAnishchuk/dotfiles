"""SSH key generation using the cryptography library."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_ssh_keypair(
    ssh_dir: Path,
    comment: str = "",
    filename: str = "id_ed25519",
) -> tuple[Path, Path, str]:
    """Generate an Ed25519 SSH keypair.

    Returns (private_key_path, public_key_path, sha256_fingerprint).
    Refuses to overwrite existing files.
    """
    private_path = ssh_dir / filename
    public_path = ssh_dir / f"{filename}.pub"

    if private_path.exists():
        raise FileExistsError(f"SSH private key already exists: {private_path}")
    if public_path.exists():
        raise FileExistsError(f"SSH public key already exists: {public_path}")

    ssh_dir.mkdir(parents=True, exist_ok=True)
    ssh_dir.chmod(0o700)

    private_key = Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    public_line = public_bytes.decode()
    if comment:
        public_line = f"{public_line} {comment}"

    private_path.write_bytes(private_bytes)
    private_path.chmod(0o600)
    public_path.write_text(public_line + "\n")
    public_path.chmod(0o644)

    key_data = base64.b64decode(public_bytes.decode().split()[1])
    digest = hashlib.sha256(key_data).digest()
    fingerprint = "SHA256:" + base64.b64encode(digest).rstrip(b"=").decode()

    return private_path, public_path, fingerprint
