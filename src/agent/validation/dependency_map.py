
from __future__ import annotations

from typing import Any

DEPENDENCY_MAP: dict[str, dict[str, list[str]]] = {
    "aws_ec2": {
        "region": ["availability_zone", "ami"],
        "availability_zone": [],
        "ami": [],
    },
    "azure_vm": {
        "region": ["availability_zone", "image"],
        "availability_zone": [],
        "image": [],
    },
}


def get_children(service_id: str, field: str) -> list[str]:
    """Return the list of child fields that depend on *field* for the given service."""
    return DEPENDENCY_MAP.get(service_id, {}).get(field, [])


def get_parent(field: str, field_config: dict[str, Any]) -> str | None:
    """Return the parent field name for *field* by reading its 'depends_on' metadata."""
    return field_config.get(field, {}).get("depends_on")
