"""
Tests for agent.nodes.validate_and_store.validate_and_store

Mocks validate_field and cascade_invalidate to isolate logic.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch

from agent.nodes.validate_and_store import validate_and_store


# ── State builder ─────────────────────────────────────────────────────────────

def _state(field, action_value, values=None, field_order=None, field_config=None):
    config = field_config or {
        "region": {"type": "select", "required": True, "depends_on": None, "options_key": "regions"},
        "availability_zone": {"type": "select", "required": True, "depends_on": "region", "options_key": "az"},
        "instance_type": {"type": "select", "required": True, "depends_on": None, "options_key": "types"},
    }
    return {
        "current_field": field,
        "field_config": config,
        "interpreted_action": {"action": "answer", "value": action_value},
        "service_id": "aws_ec2",
        "values": values or {},
        "field_sources": {},
        "field_order": field_order or list(config.keys()),
        "retry_count": 0,
    }


# ── Validation failure ────────────────────────────────────────────────────────

class TestValidationFailure:

    def test_invalid_value_returns_error(self):
        with patch("agent.nodes.validate_and_store.validate_field",
                   return_value=(False, None, "Invalid region 'dev'")):
            result = validate_and_store(_state("region", "dev"))

        assert "error" in result
        assert "Invalid region" in result["error"]
        assert result["retry_count"] == 1

    def test_retry_count_increments(self):
        state = _state("region", "dev")
        state["retry_count"] = 2
        with patch("agent.nodes.validate_and_store.validate_field",
                   return_value=(False, None, "error")):
            result = validate_and_store(state)
        assert result["retry_count"] == 3


# ── Successful store ──────────────────────────────────────────────────────────

class TestSuccessfulStore:

    def _mock_success(self, parsed_value, invalidated=None):
        invalidated = invalidated or []
        updated_values = {"region": parsed_value}
        return (
            patch("agent.nodes.validate_and_store.validate_field",
                  return_value=(True, parsed_value, None)),
            patch("agent.nodes.validate_and_store.cascade_invalidate",
                  return_value=(updated_values, invalidated)),
        )

    def test_value_stored_in_values(self):
        p1, p2 = self._mock_success("us-east-1")
        with p1, p2:
            result = validate_and_store(_state("region", "us-east-1"))
        assert result["values"]["region"] == "us-east-1"

    def test_source_set_to_user(self):
        p1, p2 = self._mock_success("us-east-1")
        with p1, p2:
            result = validate_and_store(_state("region", "us-east-1"))
        assert result["field_sources"]["region"] == "user"

    def test_error_cleared_on_success(self):
        p1, p2 = self._mock_success("us-east-1")
        with p1, p2:
            result = validate_and_store(_state("region", "us-east-1"))
        assert result["error"] is None

    def test_retry_count_reset_on_success(self):
        state = _state("region", "us-east-1")
        state["retry_count"] = 3
        p1, p2 = self._mock_success("us-east-1")
        with p1, p2:
            result = validate_and_store(state)
        assert result["retry_count"] == 0


# ── Cascade invalidation ──────────────────────────────────────────────────────

class TestCascadeInvalidation:

    def test_invalidated_children_in_missing(self):
        """When region changes, AZ should be invalidated → appear in missing."""
        with (
            patch("agent.nodes.validate_and_store.validate_field",
                  return_value=(True, "us-east-2", None)),
            patch("agent.nodes.validate_and_store.cascade_invalidate",
                  return_value=(
                      {"region": "us-east-2", "availability_zone": None},
                      ["availability_zone"],
                  )),
        ):
            state = _state(
                "region", "us-east-2",
                values={"region": "us-east-1", "availability_zone": "us-east-1a"},
            )
            result = validate_and_store(state)

        assert "availability_zone" in result["missing_fields"]
        assert "availability_zone" not in result["completed_fields"]
        assert result["invalidated_fields"] == ["availability_zone"]

    def test_no_children_invalidated_when_leaf_field(self):
        """instance_type has no children — nothing should be invalidated."""
        with (
            patch("agent.nodes.validate_and_store.validate_field",
                  return_value=(True, "t3.small", None)),
            patch("agent.nodes.validate_and_store.cascade_invalidate",
                  return_value=({"instance_type": "t3.small"}, [])),
        ):
            result = validate_and_store(_state("instance_type", "t3.small"))

        assert result["invalidated_fields"] == []


# ── Completed / missing recompute ─────────────────────────────────────────────

class TestFieldRecompute:

    def test_completed_and_missing_lists_correct(self):
        config = {
            "region": {"type": "select", "required": True},
            "availability_zone": {"type": "select", "required": True},
            "instance_type": {"type": "select", "required": True},
        }
        state = _state(
            "region", "us-east-1",
            values={},
            field_order=["region", "availability_zone", "instance_type"],
            field_config=config,
        )
        with (
            patch("agent.nodes.validate_and_store.validate_field",
                  return_value=(True, "us-east-1", None)),
            patch("agent.nodes.validate_and_store.cascade_invalidate",
                  return_value=({"region": "us-east-1"}, [])),
        ):
            result = validate_and_store(state)

        assert result["completed_fields"] == ["region"]
        assert set(result["missing_fields"]) == {"availability_zone", "instance_type"}
