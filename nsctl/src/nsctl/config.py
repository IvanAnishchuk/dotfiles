"""Global nsctl configuration."""

from __future__ import annotations

import socket
from pathlib import Path

from nsctl.models import GlobalConfig
from nsctl.paths import CONFIG_FILE


def load_config(path: Path | None = None) -> GlobalConfig:
    cfg = GlobalConfig.load(path or CONFIG_FILE)
    if not cfg.device_label:
        cfg.device_label = socket.gethostname()
    return cfg
