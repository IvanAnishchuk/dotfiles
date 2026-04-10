"""Namespace sync: git pull --ff-only + audit log."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import tomli_w

from nsctl.config import load_config
from nsctl.models import SyncLogEntry
from nsctl.paths import namespace_repo_dir, namespace_sync_dir, namespace_toml


def _git_head(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        check=False,
    )
    return result.stdout.decode().strip() if result.returncode == 0 else ""


def sync_namespace(
    name: str,
    *,
    root: Path | None = None,
    config_path: Path | None = None,
) -> SyncLogEntry:
    """Pull latest changes (ff-only) and write a sync log entry."""
    repo_dir = namespace_repo_dir(name, root)
    toml_path = namespace_toml(name, root)

    if not toml_path.exists():
        raise FileNotFoundError(f"Namespace not found: {name}")

    cfg = load_config(config_path)
    now = datetime.now(UTC)
    commit_before = _git_head(repo_dir)

    # Attempt ff-only pull (may fail if no remote or already up to date)
    result = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=repo_dir,
        capture_output=True,
        check=False,
    )
    pull_failed = result.returncode != 0
    pull_note = ""
    if pull_failed:
        stderr = result.stderr.decode(errors="replace").strip()
        if (
            "no remote" in stderr.lower()
            or "no such remote" in stderr.lower()
            or "no tracking" in stderr.lower()
        ):
            pull_note = "no remote configured; skipped pull"
        elif (
            "non-fast-forward" in stderr.lower()
            or "not possible to fast-forward" in stderr.lower()
        ):
            raise RuntimeError(
                f"Non-fast-forward pull refused for {name}. "
                "Resolve manually or use `git pull --rebase` if appropriate."
            )
        else:
            pull_note = f"pull skipped: {stderr}"

    commit_after = _git_head(repo_dir)

    # Write sync log entry
    entry = SyncLogEntry(
        timestamp=now,
        device=cfg.device_label,
        action="sync",
        commit_before=commit_before,
        commit_after=commit_after,
        note=pull_note,
    )

    sync_dir = namespace_sync_dir(name, root)
    sync_dir.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y-%m-%d-%H%M%S")
    log_file = sync_dir / f"{ts}-{cfg.device_label}.toml"
    log_file.write_text(tomli_w.dumps(entry.model_dump(mode="json")))

    # Commit the sync log
    subprocess.run(
        ["git", "add", "sync/"],
        cwd=repo_dir,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            f"sync: {cfg.device_label} at {ts}",
        ],
        cwd=repo_dir,
        capture_output=True,
        check=False,
    )

    return entry
