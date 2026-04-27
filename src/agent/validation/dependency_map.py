
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
    "aws_rds": {
        # region resets all zone/engine-independent fields that are region-scoped
        "region":            ["availability_zone", "db_instance_class", "multi_az", "storage_type", "allocated_storage_gb"],
        # db_engine resets version and everything that depends on engine choice
        "db_engine":         ["db_engine_version", "db_instance_class", "storage_type", "allocated_storage_gb"],
        # db_engine_version constrains which instance classes are valid
        "db_engine_version": ["db_instance_class"],
        # storage_type determines valid allocated_storage ranges
        "storage_type":      ["allocated_storage_gb"],
        # leaf nodes — no children
        "availability_zone":    [],
        "db_instance_class":    [],
        "multi_az":             [],
        "allocated_storage_gb": [],
    },
}


def get_children(service_id: str, field: str) -> list[str]:
    """Return the list of child fields that depend on *field* for the given service."""
    return DEPENDENCY_MAP.get(service_id, {}).get(field, [])


def get_parent(field: str, field_config: dict[str, Any]) -> str | None:
    """Return the parent field name for *field* by reading its 'depends_on' metadata."""
    return field_config.get(field, {}).get("depends_on")
