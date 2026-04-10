"""GPG subprocess wrapper.

Every function takes a gnupghome parameter so operations are always
scoped to a specific keyring directory, never touching ~/.gnupg.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GpgError(Exception):
    def __init__(self, message: str, returncode: int = 1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class GpgKeyInfo:
    fingerprint: str
    uid: str


def _run_gpg(
    args: list[str],
    gnupghome: Path,
    *,
    input_data: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    cmd = [
        "gpg",
        "--homedir",
        str(gnupghome),
        "--batch",
        "--yes",
        "--no-tty",
        *args,
    ]
    result = subprocess.run(cmd, input=input_data, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise GpgError(
            f"gpg failed: {result.stderr.decode(errors='replace')}",
            result.returncode,
            result.stderr.decode(errors="replace"),
        )
    return result


def init_gnupghome(gnupghome: Path) -> None:
    gnupghome.mkdir(parents=True, exist_ok=True)
    gnupghome.chmod(0o700)


def generate_keypair(
    gnupghome: Path,
    real_name: str,
    email: str,
    *,
    passphrase: str = "",
) -> str:
    """Generate ed25519 primary + cv25519 encryption subkey.

    Returns the fingerprint of the primary key.
    """
    lines = []
    if not passphrase:
        lines.append("%no-protection")
    else:
        lines.append(f"Passphrase: {passphrase}")
    lines.extend(
        [
            "Key-Type: eddsa",
            "Key-Curve: ed25519",
            "Key-Usage: sign",
            "Subkey-Type: ecdh",
            "Subkey-Curve: cv25519",
            "Subkey-Usage: encrypt",
            f"Name-Real: {real_name}",
            f"Name-Email: {email}",
            "%commit",
        ]
    )
    _run_gpg(["--gen-key"], gnupghome, input_data=("\n".join(lines) + "\n").encode())
    return get_fingerprint(gnupghome, email)


def get_fingerprint(gnupghome: Path, uid_pattern: str) -> str:
    result = _run_gpg(["--with-colons", "--fingerprint", uid_pattern], gnupghome)
    for line in result.stdout.decode().splitlines():
        if line.startswith("fpr:"):
            return line.split(":")[9]
    raise GpgError(f"No fingerprint found for {uid_pattern}")


def list_keys(gnupghome: Path, *, secret: bool = False) -> list[GpgKeyInfo]:
    flag = "--list-secret-keys" if secret else "--list-keys"
    result = _run_gpg(["--with-colons", flag], gnupghome, check=False)
    keys: list[GpgKeyInfo] = []
    current_fpr = ""
    for line in result.stdout.decode().splitlines():
        fields = line.split(":")
        if fields[0] == "fpr":
            current_fpr = fields[9]
        elif fields[0] == "uid" and current_fpr:
            keys.append(GpgKeyInfo(fingerprint=current_fpr, uid=fields[9]))
    return keys


def export_public_key(gnupghome: Path, fingerprint: str) -> str:
    result = _run_gpg(["--armor", "--export", fingerprint], gnupghome)
    return result.stdout.decode()


def import_key(gnupghome: Path, key_data: str) -> None:
    _run_gpg(["--import"], gnupghome, input_data=key_data.encode())


def encrypt_to_recipients(
    gnupghome: Path, recipients: list[str], plaintext: bytes
) -> bytes:
    args = ["--armor", "--encrypt", "--trust-model", "always"]
    for r in recipients:
        args.extend(["--recipient", r])
    result = _run_gpg(args, gnupghome, input_data=plaintext)
    return result.stdout


def decrypt(gnupghome: Path, ciphertext: bytes) -> bytes:
    result = _run_gpg(["--decrypt"], gnupghome, input_data=ciphertext)
    return result.stdout
