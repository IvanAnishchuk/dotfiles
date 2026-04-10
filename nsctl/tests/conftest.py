"""Shared test fixtures for nsctl."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    """Root directory simulating $HOME for namespace operations."""
    return tmp_path


@pytest.fixture
def tmp_gnupghome(tmp_path: Path) -> Path:
    d = tmp_path / ".gnupg-test"
    d.mkdir(mode=0o700)
    return d


@pytest.fixture
def tmp_sshdir(tmp_path: Path) -> Path:
    d = tmp_path / ".ssh-test"
    d.mkdir(mode=0o700)
    return d


@pytest.fixture
def device_label() -> str:
    return socket.gethostname()


@pytest.fixture
def template_dir_fixture() -> Path:
    return Path(__file__).resolve().parent.parent / "template"
