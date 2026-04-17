"""validate_and_store node — validates interpreted value and persists to state."""

from __future__ import annotations

from agent.state import Agent2State
from agent.validation.dependency import cascade_invalidate
from agent.validation.field_validator import validate_field


def _recompute_fields(field_order: list, field_config: dict, values: dict):
    completed = [
        f for f in field_order
        if field_config.get(f, {}).get("required")
        and f in values and values[f] is not None
    ]
    missing = [
        f for f in field_order
        if field_config.get(f, {}).get("required")
        and (f not in values or values[f] is None)
    ]
    return completed, missing


def validate_and_store(state: Agent2State) -> dict:
    field = state["current_field"]
    field_config = state["field_config"]
    action = state["interpreted_action"]
    value = action["value"]

    # ── Validate ──
    ok, parsed, error = validate_field(
        service_id=state["service_id"],
        field=field,
        value=value,
        field_config=field_config,
        values=state["values"],
    )

    if not ok:
        return {
            "error": error,
            "retry_count": state.get("retry_count", 0) + 1,
            "messages": [f"Validation failed for {field}: {error}"],
        }

    # ── Store ──
    updated_values = {**state["values"], field: parsed}
    updated_sources = {**state.get("field_sources", {}), field: "user"}

    # Cascade-invalidate dependent children
    updated_values, invalidated = cascade_invalidate(
        state["service_id"], field, updated_values, field_config
    )

    completed, missing = _recompute_fields(
        state["field_order"], field_config, updated_values
    )

    return {
        "values": updated_values,
        "field_sources": updated_sources,
        "completed_fields": completed,
        "missing_fields": missing,
        "invalidated_fields": invalidated,
        "error": None,
        "retry_count": 0,
        "messages": [f"Stored {field}={parsed}. Invalidated: {invalidated}"],
    }
