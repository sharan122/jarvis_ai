"""Load service configuration JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Resolve config directory relative to project root
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

# In-memory cache so we only read from disk once per process
_cache: dict[str, dict[str, Any]] = {}


def load_service_config(service_id: str) -> dict[str, Any]:
    """
    Load and cache a service configuration file.

    Looks for  config/{service_id}.json  relative to the project root.
    """
    if service_id in _cache:
        return _cache[service_id]

    config_path = _CONFIG_DIR / f"{service_id}.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Service config not found: {config_path}"
        )

    with open(config_path) as f:
        config = json.load(f)

    _cache[service_id] = config
    return config


def clear_config_cache() -> None:
    """Clear the config cache (useful in tests)."""
    _cache.clear()
