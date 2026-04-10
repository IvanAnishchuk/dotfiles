"""Health checks for nsctl namespaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from nsctl.models import NamespaceConfig
from nsctl.paths import (
    discover_namespaces,
    namespace_gnupghome,
    namespace_gpg_id,
    namespace_keys_dir,
    namespace_sshdir,
    namespace_toml,
)


class CheckStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str


@dataclass
class NamespaceHealth:
    namespace: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def worst(self) -> CheckStatus:
        if any(c.status == CheckStatus.FAIL for c in self.checks):
            return CheckStatus.FAIL
        if any(c.status == CheckStatus.WARN for c in self.checks):
            return CheckStatus.WARN
        return CheckStatus.PASS


def _check_namespace_toml(name: str, root: Path | None) -> CheckResult:
    path = namespace_toml(name, root)
    if not path.exists():
        return CheckResult("namespace.toml", CheckStatus.FAIL, "missing")
    try:
        NamespaceConfig.load(path)
        return CheckResult("namespace.toml", CheckStatus.PASS, "valid")
    except Exception as e:
        return CheckResult("namespace.toml", CheckStatus.FAIL, f"parse error: {e}")


def _check_gpg_id(name: str, root: Path | None) -> CheckResult:
    path = namespace_gpg_id(name, root)
    if not path.exists():
        return CheckResult(".gpg-id", CheckStatus.FAIL, "missing")
    fpr = path.read_text().strip()
    if not fpr:
        return CheckResult(".gpg-id", CheckStatus.FAIL, "empty")
    return CheckResult(".gpg-id", CheckStatus.PASS, f"fingerprint: {fpr[:16]}...")


def _check_gnupghome(name: str, root: Path | None) -> CheckResult:
    path = namespace_gnupghome(name, root)
    if not path.exists():
        return CheckResult("gnupghome", CheckStatus.FAIL, f"missing: {path}")
    if not path.is_dir():
        return CheckResult("gnupghome", CheckStatus.FAIL, f"not a directory: {path}")
    return CheckResult("gnupghome", CheckStatus.PASS, str(path))


def _check_sshdir(name: str, root: Path | None) -> CheckResult:
    path = namespace_sshdir(name, root)
    if not path.exists():
        return CheckResult("ssh dir", CheckStatus.WARN, f"missing: {path}")
    pub = path / "id_ed25519.pub"
    if not pub.exists():
        return CheckResult("ssh dir", CheckStatus.WARN, "no id_ed25519.pub")
    return CheckResult("ssh dir", CheckStatus.PASS, str(path))


def _check_keys_dir(name: str, root: Path | None) -> CheckResult:
    path = namespace_keys_dir(name, root)
    if not path.exists():
        return CheckResult("keys/", CheckStatus.WARN, "missing")
    # Check for plaintext private keys
    for f in path.rglob("*"):
        if (
            f.is_file()
            and f.suffix not in (".gpg", ".pub", ".toml", ".asc", ".md")
            and f.name not in (".gitignore", ".gitkeep")
        ):
            return CheckResult("keys/", CheckStatus.WARN, f"unexpected file: {f.name}")
    return CheckResult("keys/", CheckStatus.PASS, "clean")


def _check_validity(name: str, root: Path | None) -> CheckResult:
    path = namespace_toml(name, root)
    if not path.exists():
        return CheckResult("validity", CheckStatus.FAIL, "no namespace.toml")
    cfg = NamespaceConfig.load(path)
    if cfg.lifecycle.valid_until:
        try:
            expiry = datetime.fromisoformat(cfg.lifecycle.valid_until)
            if expiry < datetime.now(UTC):
                return CheckResult(
                    "validity",
                    CheckStatus.WARN,
                    f"expired: {cfg.lifecycle.valid_until}",
                )
        except ValueError:
            return CheckResult(
                "validity",
                CheckStatus.WARN,
                f"invalid date: {cfg.lifecycle.valid_until}",
            )
    return CheckResult("validity", CheckStatus.PASS, "ok")


def check_namespace(name: str, root: Path | None = None) -> NamespaceHealth:
    health = NamespaceHealth(namespace=name)
    health.checks.append(_check_namespace_toml(name, root))
    health.checks.append(_check_gpg_id(name, root))
    health.checks.append(_check_gnupghome(name, root))
    health.checks.append(_check_sshdir(name, root))
    health.checks.append(_check_keys_dir(name, root))
    health.checks.append(_check_validity(name, root))
    return health


def run_doctor(root: Path | None = None) -> list[NamespaceHealth]:
    results = []
    for name in discover_namespaces(root):
        toml_path = namespace_toml(name, root)
        if toml_path.exists():
            cfg = NamespaceConfig.load(toml_path)
            if not cfg.disabled:
                results.append(check_namespace(name, root))
    return results
