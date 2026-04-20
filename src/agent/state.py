"""Agent 2 state definition — single source of truth for the entire session."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class Agent2State(TypedDict, total=False):
    # ── Identity ──
    session_id: str
    service_id: str
    service_version: str
    user_id: str

    # ── Configuration (loaded once at bootstrap) ──
    field_order: list[str]
    field_config: dict[str, dict]
    default_json: dict[str, Any]
    user_enrichment: dict[str, Any]

    # ── Collection state ──
    values: dict[str, Any]
    field_sources: dict[str, str]       # field -> "user" | "enrichment" | "default"
    missing_fields: list[str]
    completed_fields: list[str]

    # ── Current turn ──
    current_field: str | None
    mode: str                           # collect | edit | help | preview | confirm | done
    last_user_input: str | None
    interpreted_action: dict | None

    # ── Error state ──
    error: str | None
    retry_count: int

    # ── Edit state ──
    edit_target: str | None
    invalidated_fields: list[str]

    # ── Help state ──
    help_context: str | None
    help_response: str | None

    # ── Preview state ──
    preview_response: dict | None

    # ── Output ──
    agent_json: dict[str, Any] | None
    final_json: dict[str, Any] | None

    # ── Audit ──
    messages: Annotated[list[str], operator.add]
    turn_count: int
