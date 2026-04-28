"""
Tests for agent.interpreter.fast_path.try_fast_path

These are pure-logic tests — zero LLM calls, zero Redis calls.
"""

from __future__ import annotations

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agent.interpreter.fast_path import try_fast_path


# ── Fixtures ──────────────────────────────────────────────────────────────────

SELECT_META = {"type": "select"}
NUMBER_META  = {"type": "number"}
TEXT_META    = {"type": "text"}
REGIONS      = ["us-east-1", "us-east-2", "eu-west-1"]
COMPLETED    = ["region", "availability_zone"]


# ── 1. Keyword actions ────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw", ["help", "?", "what is this", "info", "explain"])
def test_help_keywords(raw):
    result = try_fast_path(raw, "region", SELECT_META, REGIONS)
    assert result == {"action": "help", "field": "region"}


@pytest.mark.parametrize("raw", ["preview", "show", "summary", "show me", "review"])
def test_preview_keywords(raw):
    result = try_fast_path(raw, "region", SELECT_META, REGIONS)
    assert result == {"action": "preview"}


@pytest.mark.parametrize("raw", ["cancel", "quit", "stop", "exit", "abort"])
def test_cancel_keywords(raw):
    result = try_fast_path(raw, "region", SELECT_META, REGIONS)
    assert result == {"action": "cancel"}


# ── 2. Select field ───────────────────────────────────────────────────────────

def test_exact_match_case_insensitive():
    result = try_fast_path("US-EAST-1", "region", SELECT_META, REGIONS)
    assert result == {"action": "answer", "value": "us-east-1"}


def test_exact_match_lowercase():
    result = try_fast_path("eu-west-1", "region", SELECT_META, REGIONS)
    assert result == {"action": "answer", "value": "eu-west-1"}


def test_partial_match_unique():
    """'east-2' is a unique substring → should resolve to us-east-2."""
    result = try_fast_path("east-2", "region", SELECT_META, REGIONS)
    assert result == {"action": "answer", "value": "us-east-2"}


def test_partial_match_ambiguous_returns_none():
    """'east' matches both us-east-1 and us-east-2 → cannot resolve."""
    result = try_fast_path("east", "region", SELECT_META, REGIONS)
    assert result is None


def test_no_options_returns_none():
    result = try_fast_path("us-east-1", "region", SELECT_META, [])
    assert result is None


# ── 3. Number field ───────────────────────────────────────────────────────────

def test_number_integer():
    result = try_fast_path("100", "allocated_storage_gb", NUMBER_META, [])
    assert result == {"action": "answer", "value": 100}


def test_number_natural_language_returns_none():
    """Natural language numbers must fall through to LLM."""
    result = try_fast_path("one hundred", "allocated_storage_gb", NUMBER_META, [])
    assert result is None


# ── 4. Text field ─────────────────────────────────────────────────────────────

def test_text_field_accepts_any_non_empty():
    result = try_fast_path("my-app-name", "application_name", TEXT_META, [])
    assert result == {"action": "answer", "value": "my-app-name"}


def test_text_field_empty_returns_none():
    result = try_fast_path("  ", "application_name", TEXT_META, [])
    assert result is None


# ── 5. Edit command ───────────────────────────────────────────────────────────

def test_edit_with_value():
    result = try_fast_path("change region to us-east-2", "environment", SELECT_META, [], COMPLETED)
    assert result == {"action": "edit", "field": "region", "value": "us-east-2"}


def test_edit_without_value():
    result = try_fast_path("edit region", "environment", SELECT_META, [], COMPLETED)
    assert result == {"action": "edit", "field": "region", "value": None}


def test_edit_partial_field_name():
    """'zone' should match 'availability_zone'."""
    result = try_fast_path("change zone to us-east-1a", "environment", SELECT_META, [], COMPLETED)
    assert result == {"action": "edit", "field": "availability_zone", "value": "us-east-1a"}


def test_edit_unknown_field_returns_none():
    """If the target field isn't in completed_fields, fast_path returns None."""
    result = try_fast_path("change ami to ami-123", "environment", SELECT_META, [], COMPLETED)
    # "ami" is not in COMPLETED so no edit match
    assert result is None


def test_edit_with_phrase_starting_with_need_returns_none():
    """'need to change' doesn't match the regex — must fall through to LLM."""
    result = try_fast_path("need to change region to us-east-2", "environment", SELECT_META, [], COMPLETED)
    assert result is None


def test_edit_no_completed_fields_returns_none():
    result = try_fast_path("change region to us-east-1", "environment", SELECT_META, [], [])
    assert result is None
