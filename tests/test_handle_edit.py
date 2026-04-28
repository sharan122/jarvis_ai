"""
Tests for agent.nodes.handle_edit.handle_edit

Mocks Redis (get_options_for_field) and validate_field so tests run
without a live Redis instance.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch

from agent.nodes.handle_edit import handle_edit


# ── State builder ─────────────────────────────────────────────────────────────

def _state(field, value, field_config, values=None, completed=None, field_order=None):
    completed = completed or list((values or {}).keys())
    return {
        "interpreted_action": {"action": "edit", "field": field, "value": value},
        "completed_fields": completed,
        "field_config": field_config,
        "service_id": "aws_ec2",
        "values": values or {},
        "field_sources": {f: "user" for f in (values or {})},
        "field_order": field_order or list(field_config.keys()),
    }


EC2_CONFIG = {
    "region": {"type": "select", "readonly": False, "required": True, "depends_on": None, "options_key": "regions"},
    "availability_zone": {"type": "select", "readonly": False, "required": True, "depends_on": "region", "options_key": "az"},
    "ami": {"type": "select", "readonly": False, "required": True, "depends_on": "region", "options_key": "amis"},
    "instance_type": {"type": "select", "readonly": False, "required": True, "depends_on": None, "options_key": "types"},
}

FILLED_VALUES = {
    "region": "us-east-1",
    "availability_zone": "us-east-1a",
    "ami": "ami-ubuntu-2204-use1",
    "instance_type": "t3.small",
}


# ── Guard 1: field not in completed ──────────────────────────────────────────

def test_guard1_field_not_completed():
    state = _state("region", "us-east-2", EC2_CONFIG, {}, completed=[])
    result = handle_edit(state)
    assert "error" in result
    assert "not been filled" in result["error"]
    assert result["mode"] == "collect"


# ── Guard 2: readonly field ───────────────────────────────────────────────────

def test_guard2_readonly_field():
    config = {**EC2_CONFIG, "app_id": {"type": "text", "readonly": True, "required": True, "depends_on": None, "options_key": None}}
    state = _state("app_id", "NEW_ID", config, {"app_id": "OLD_ID"}, completed=["app_id"])
    result = handle_edit(state)
    assert "error" in result
    assert "auto-filled" in result["error"]


# ── Same value check ──────────────────────────────────────────────────────────

def test_same_value_rejected():
    """Editing region to its current value should return an error."""
    state = _state("region", "us-east-1", EC2_CONFIG, FILLED_VALUES,
                   completed=list(FILLED_VALUES.keys()))
    result = handle_edit(state)
    assert "error" in result
    assert "already set" in result["error"]


def test_same_value_case_insensitive():
    """'US-EAST-1' vs 'us-east-1' should be treated as same value."""
    state = _state("region", "US-EAST-1", EC2_CONFIG, FILLED_VALUES,
                   completed=list(FILLED_VALUES.keys()))
    result = handle_edit(state)
    assert "error" in result
    assert "already set" in result["error"]


# ── Successful edit with cascade ──────────────────────────────────────────────

def test_successful_edit_resets_children():
    """
    Changing region should invalidate availability_zone and ami
    (children of region in aws_ec2 dependency map).
    """
    with (
        patch("agent.nodes.handle_edit.get_options_for_field", return_value=["us-east-1", "us-east-2"]),
        patch("agent.nodes.handle_edit.validate_field", return_value=(True, "us-east-2", None)),
        patch("agent.nodes.handle_edit.cascade_invalidate", return_value=(
            {**FILLED_VALUES, "region": "us-east-2", "availability_zone": None, "ami": None},
            ["availability_zone", "ami"],
        )),
        patch("agent.nodes.handle_edit._recompute", return_value=(
            ["region", "instance_type"],
            ["availability_zone", "ami"],
        )),
        patch("agent.nodes.handle_edit.get_children", return_value=["availability_zone", "ami"]),
    ):
        state = _state("region", "us-east-2", EC2_CONFIG, FILLED_VALUES,
                       completed=list(FILLED_VALUES.keys()))
        result = handle_edit(state)

    assert result.get("error") is None
    assert "us-east-2" in str(result.get("values", {}).get("region", ""))
    assert "availability_zone" in result.get("missing_fields", [])


# ── No value provided — re-ask flow ──────────────────────────────────────────

def test_no_value_nulls_field_and_recomputes():
    """
    When no value is given, the target field should be nulled so that
    post_action correctly routes to ask_field for that field.
    """
    state = _state("availability_zone", None, EC2_CONFIG, FILLED_VALUES,
                   completed=list(FILLED_VALUES.keys()),
                   field_order=list(EC2_CONFIG.keys()))
    result = handle_edit(state)

    assert result["values"]["availability_zone"] is None
    assert "availability_zone" in result["missing_fields"]
    # availability_zone should be the first missing (earliest in field_order after region)
    assert result["missing_fields"][0] == "availability_zone"
    assert result["current_field"] == "availability_zone"
    assert result["mode"] == "collect"
    assert result["error"] is None
