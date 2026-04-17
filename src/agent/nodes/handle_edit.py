"""handle_edit node — change a previously filled field value."""

from __future__ import annotations

from agent.state import Agent2State
from agent.validation.dependency import cascade_invalidate
from agent.validation.field_validator import validate_field


def _recompute(field_order, field_config, values):
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


def handle_edit(state: Agent2State) -> dict:
    action = state.get("interpreted_action") or {}
    target_field = action.get("field")
    new_value = action.get("value")

    completed = state.get("completed_fields", [])
    field_config = state.get("field_config", {})

    # Guard: can only edit completed fields
    if target_field not in completed:
        return {
            "error": f"Cannot edit '{target_field}' — it has not been filled yet.",
            "mode": "collect",
            "messages": [f"Edit rejected: {target_field} not in completed"],
        }

    # Guard: readonly fields
    meta = field_config.get(target_field, {})
    if meta.get("readonly"):
        return {
            "error": f"'{target_field}' is auto-filled and cannot be changed.",
            "mode": "collect",
            "messages": [f"Edit rejected: {target_field} is readonly"],
        }

    # If a new value was provided, validate + store immediately
    if new_value is not None:
        ok, parsed, err = validate_field(
            service_id=state["service_id"],
            field=target_field,
            value=new_value,
            field_config=field_config,
            values=state["values"],
        )
        if not ok:
            return {"error": err, "mode": "collect"}

        updated_values = {**state["values"], target_field: parsed}
        updated_values, invalidated = cascade_invalidate(
            state["service_id"], target_field, updated_values, field_config
        )

        comp, miss = _recompute(state["field_order"], field_config, updated_values)

        return {
            "values": updated_values,
            "field_sources": {**state.get("field_sources", {}), target_field: "user"},
            "completed_fields": comp,
            "missing_fields": miss,
            "invalidated_fields": invalidated,
            "error": None,
            "mode": "collect",
            "messages": [f"Edited {target_field}={parsed}. Invalidated: {invalidated}"],
        }

    # No value provided — re-ask the field
    return {
        "current_field": target_field,
        "mode": "collect",
        "messages": [f"Edit mode: will re-ask {target_field}"],
    }
