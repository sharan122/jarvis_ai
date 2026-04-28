"""Shared pytest fixtures for the jarvis_ai test suite."""

from __future__ import annotations

import pytest


# ── Minimal field configs ─────────────────────────────────────────────────────

@pytest.fixture
def ec2_field_config() -> dict:
    return {
        "region": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "regions", "depends_on": None,
        },
        "availability_zone": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "availability_zones_by_region", "depends_on": "region",
        },
        "instance_type": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "instance_types", "depends_on": None,
        },
        "ami": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "amis_by_region", "depends_on": "region",
        },
        "environment": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "environments", "depends_on": None,
        },
    }


@pytest.fixture
def rds_field_config() -> dict:
    return {
        "region": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "regions", "depends_on": None,
        },
        "availability_zone": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "availability_zones_by_region", "depends_on": "region",
        },
        "db_engine": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "db_engines", "depends_on": None,
        },
        "db_engine_version": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "db_engine_versions_by_engine", "depends_on": "db_engine",
        },
        "db_instance_class": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "db_instance_classes", "depends_on": "db_engine_version",
        },
        "storage_type": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "storage_types", "depends_on": "db_engine",
        },
        "allocated_storage_gb": {
            "type": "number", "required": True, "readonly": False,
            "options_key": None, "depends_on": "storage_type",
            "validator": {"min": 20, "max": 65536},
        },
        "multi_az": {
            "type": "select", "required": True, "readonly": False,
            "options_key": "multi_az_options", "depends_on": "region",
        },
    }


@pytest.fixture
def ec2_field_order() -> list[str]:
    return ["region", "availability_zone", "instance_type", "ami", "environment"]


@pytest.fixture
def rds_field_order() -> list[str]:
    return [
        "region", "availability_zone", "db_engine",
        "db_engine_version", "db_instance_class", "multi_az",
        "storage_type", "allocated_storage_gb",
    ]
