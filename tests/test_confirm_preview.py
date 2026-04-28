"""
Tests for agent.nodes.confirm_preview._classify_intent

Tests the three-tier classification (keyword → fast_path → LLM mapping)
used inside the confirmation interrupt node.
Mocks try_fast_path and llm_classify_input to isolate the logic.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch

from agent.nodes.confirm_preview import _classify_intent, _CONFIRM_KEYWORDS, _CANCEL_KEYWORDS


# ── Minimal state stub ────────────────────────────────────────────────────────

def _state(completed=None, values=None):
    return {
        "completed_fields": completed or ["region", "availability_zone", "environment"],
        "values": values or {"region": "us-east-1"},
        "session_id": "test_session",
        "service_id": "aws_ec2",
    }


# ── 1. Keyword fast exits ─────────────────────────────────────────────────────

class TestConfirmKeywords:

    @pytest.mark.parametrize("kw", list(_CONFIRM_KEYWORDS))
    def test_confirm_keyword_returns_confirm(self, kw):
        result = _classify_intent(kw, _state())
        assert result == {"action": "confirm"}

    @pytest.mark.parametrize("kw", list(_CANCEL_KEYWORDS))
    def test_cancel_keyword_returns_cancel(self, kw):
        result = _classify_intent(kw, _state())
        assert result == {"action": "cancel"}

    def test_save_it_is_confirm_keyword(self):
        result = _classify_intent("save it", _state())
        assert result == {"action": "confirm"}

    def test_apply_is_confirm_keyword(self):
        result = _classify_intent("apply", _state())
        assert result == {"action": "confirm"}

    def test_nope_is_cancel_keyword(self):
        result = _classify_intent("nope", _state())
        assert result == {"action": "cancel"}


# ── 2. Fast path (edit/cancel) ────────────────────────────────────────────────

class TestConfirmFastPath:

    def test_change_x_to_y_routes_to_edit(self):
        """'change region to us-east-2' should be caught by fast_path as edit."""
        result = _classify_intent("change region to us-east-2", _state())
        assert result["action"] == "edit"
        assert result["field"] == "region"
        assert result["value"] == "us-east-2"

    def test_edit_field_no_value(self):
        result = _classify_intent("edit region", _state())
        assert result["action"] == "edit"
        assert result["value"] is None


# ── 3. LLM fallback action mapping ───────────────────────────────────────────

class TestConfirmLLMMapping:

    def _mock_llm(self, return_action: str, **extra):
        return {"action": return_action, **extra}

    def test_llm_edit_passes_through(self):
        with patch("agent.nodes.confirm_preview.llm_classify_input",
                   return_value={"action": "edit", "field": "region", "value": "us-east-2"}):
            result = _classify_intent("i want to update the region to us-east-2", _state())
        assert result["action"] == "edit"

    def test_llm_cancel_passes_through(self):
        with patch("agent.nodes.confirm_preview.llm_classify_input",
                   return_value={"action": "cancel"}):
            result = _classify_intent("i want to cancel everything", _state())
        assert result["action"] == "cancel"

    def test_llm_answer_maps_to_confirm(self):
        """LLM returning 'answer' at confirmation stage → treat as confirm."""
        with patch("agent.nodes.confirm_preview.llm_classify_input",
                   return_value={"action": "answer", "value": "save it"}):
            result = _classify_intent("please save my inputs", _state())
        assert result["action"] == "confirm"

    def test_llm_unclear_stays_unclear(self):
        with patch("agent.nodes.confirm_preview.llm_classify_input",
                   return_value={"action": "unclear"}):
            result = _classify_intent("zzz gibberish zzz", _state())
        assert result["action"] == "unclear"

    def test_llm_preview_maps_to_unclear(self):
        with patch("agent.nodes.confirm_preview.llm_classify_input",
                   return_value={"action": "preview"}):
            result = _classify_intent("show me stuff", _state())
        assert result["action"] == "unclear"
