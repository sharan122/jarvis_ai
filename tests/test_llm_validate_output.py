"""
Tests for agent.interpreter.llm_classify._validate_llm_output

Tests the LLM output validation layer: action guards, same-field reinterpretation,
and the edit-for-completed-field pass-through. Mocks the actual LLM call.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch, MagicMock

# Import the private helper directly for unit testing
from agent.interpreter.llm_classify import _validate_llm_output


COMPLETED = ["region", "availability_zone", "environment"]
OPTIONS    = ["us-east-1", "us-east-2", "eu-west-1"]


# ── Valid actions pass through ─────────────────────────────────────────────────

def test_answer_with_value_passes():
    out = _validate_llm_output({"action": "answer", "value": "us-east-1"}, OPTIONS, COMPLETED, "region")
    assert out["action"] == "answer"
    assert out["value"] == "us-east-1"


def test_cancel_passes():
    out = _validate_llm_output({"action": "cancel"}, OPTIONS, COMPLETED, "region")
    assert out["action"] == "cancel"


def test_help_passes():
    out = _validate_llm_output({"action": "help"}, OPTIONS, COMPLETED, "region")
    assert out["action"] == "help"


# ── Invalid action → unclear ──────────────────────────────────────────────────

def test_invalid_action_becomes_unclear():
    out = _validate_llm_output({"action": "fly"}, OPTIONS, COMPLETED, "region")
    assert out["action"] == "unclear"


def test_answer_without_value_becomes_unclear():
    out = _validate_llm_output({"action": "answer", "value": None}, OPTIONS, COMPLETED, "region")
    assert out["action"] == "unclear"


# ── Edit validation ───────────────────────────────────────────────────────────

def test_edit_completed_field_passes():
    """Editing a field that IS completed → pass through as edit."""
    out = _validate_llm_output(
        {"action": "edit", "field": "region", "value": "us-east-2"},
        OPTIONS, COMPLETED, "environment",
    )
    assert out["action"] == "edit"
    assert out["field"] == "region"


def test_edit_not_completed_field_becomes_unclear():
    """Editing a field not in completed_fields (and not the current field) → unclear."""
    out = _validate_llm_output(
        {"action": "edit", "field": "instance_type", "value": "t3.small"},
        OPTIONS, COMPLETED, "environment",
    )
    assert out["action"] == "unclear"


# ── Same-field edit reinterpretation ──────────────────────────────────────────

def test_edit_for_current_field_with_value_becomes_answer():
    """
    'change region to us-east-1' while BEING ASKED for region →
    LLM returns edit intent, but region is not completed yet.
    Should be reinterpreted as an answer.
    """
    out = _validate_llm_output(
        {"action": "edit", "field": "region", "value": "us-east-1"},
        OPTIONS,
        completed_fields=[],   # region not yet completed
        current_field="region",
    )
    assert out["action"] == "answer"
    assert out["value"] == "us-east-1"


def test_edit_for_current_field_without_value_stays_unclear():
    """If user says 'change region' (no value) while on region → unclear (nothing to set)."""
    out = _validate_llm_output(
        {"action": "edit", "field": "region", "value": None},
        OPTIONS,
        completed_fields=[],
        current_field="region",
    )
    assert out["action"] == "unclear"


def test_edit_for_different_uncompleted_field_stays_unclear():
    """If target field is not current AND not completed → unclear."""
    out = _validate_llm_output(
        {"action": "edit", "field": "instance_type", "value": "t3.small"},
        OPTIONS,
        completed_fields=["region"],
        current_field="availability_zone",
    )
    assert out["action"] == "unclear"
