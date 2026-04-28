"""
Tests for agent.validation.dependency_map

Pure data tests — no IO, no mocking needed.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from agent.validation.dependency_map import get_children, get_parent


# ── get_children ──────────────────────────────────────────────────────────────

class TestGetChildren:

    # aws_ec2
    def test_ec2_region_children(self):
        children = get_children("aws_ec2", "region")
        assert "availability_zone" in children
        assert "ami" in children

    def test_ec2_leaf_has_no_children(self):
        assert get_children("aws_ec2", "ami") == []
        assert get_children("aws_ec2", "availability_zone") == []

    # aws_rds
    def test_rds_region_resets_zone_and_compute(self):
        children = get_children("aws_rds", "region")
        assert "availability_zone" in children
        assert "db_instance_class" in children
        assert "multi_az" in children
        assert "storage_type" in children
        assert "allocated_storage_gb" in children

    def test_rds_engine_resets_version_and_storage(self):
        children = get_children("aws_rds", "db_engine")
        assert "db_engine_version" in children
        assert "db_instance_class" in children
        assert "storage_type" in children
        assert "allocated_storage_gb" in children

    def test_rds_engine_version_resets_instance_class(self):
        assert "db_instance_class" in get_children("aws_rds", "db_engine_version")

    def test_rds_storage_type_resets_allocated_storage(self):
        assert "allocated_storage_gb" in get_children("aws_rds", "storage_type")

    def test_rds_leaf_nodes_have_no_children(self):
        for leaf in ["availability_zone", "db_instance_class", "multi_az", "allocated_storage_gb"]:
            assert get_children("aws_rds", leaf) == []

    # azure_vm
    def test_azure_region_children(self):
        children = get_children("azure_vm", "region")
        assert "availability_zone" in children
        assert "image" in children

    # Unknown service / field
    def test_unknown_service_returns_empty(self):
        assert get_children("aws_lambda", "region") == []

    def test_unknown_field_returns_empty(self):
        assert get_children("aws_ec2", "nonexistent_field") == []


# ── get_parent ────────────────────────────────────────────────────────────────

class TestGetParent:

    def test_ec2_az_parent_is_region(self, ec2_field_config):
        assert get_parent("availability_zone", ec2_field_config) == "region"

    def test_ec2_region_has_no_parent(self, ec2_field_config):
        assert get_parent("region", ec2_field_config) is None

    def test_rds_engine_version_parent_is_engine(self, rds_field_config):
        assert get_parent("db_engine_version", rds_field_config) == "db_engine"

    def test_rds_storage_type_parent_is_engine(self, rds_field_config):
        assert get_parent("storage_type", rds_field_config) == "db_engine"

    def test_rds_allocated_storage_parent_is_storage_type(self, rds_field_config):
        assert get_parent("allocated_storage_gb", rds_field_config) == "storage_type"

    def test_rds_multi_az_parent_is_region(self, rds_field_config):
        assert get_parent("multi_az", rds_field_config) == "region"

    def test_unknown_field_returns_none(self, ec2_field_config):
        assert get_parent("nonexistent", ec2_field_config) is None
