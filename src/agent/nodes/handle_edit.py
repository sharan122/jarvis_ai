"""handle_edit node — change a previously filled field value with full dependency awareness."""

from __future__ import annotations

from agent.interpreter.fast_path import try_fast_path
from agent.interpreter.llm_classify import llm_classify_input
from agent.state import Agent2State
from agent.tools.options import get_options_for_field
from agent.validation.dependency import cascade_invalidate, reset_children
from agent.validation.dependency_map import get_children, get_parent
from agent.validation.field_validator import validate_field


# ── Helpers ──────────────────────────────────────────────────────────────────

def _recompute(field_order: list, field_config: dict, values: dict) -> tuple[list, list]:
    """Derive completed and missing required-field lists from current values."""
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


def _is_parent_field(service_id: str, field: str) -> bool:
    """Return True if *field* has at least one child dependent in the dependency map."""
    return bool(get_children(service_id, field))


def _normalise_value(
    new_value: str,
    target_field: str,
    field_meta: dict,
    options: list[str],
    completed: list[str],
    state: Agent2State,
) -> tuple[str | None, str | None]:
    """
    Run new_value through fast-path then LLM classification to normalise it.

    Returns (normalised_value, error_message).  Exactly one will be non-None.
    """
    # Fast path — no LLM tokens
    fast_result = try_fast_path(new_value, target_field, field_meta, options, completed)
    if fast_result is not None and fast_result.get("action") == "answer":
        return fast_result["value"], None

    # Slow path — LLM classification.
    # Exclude the field being edited from completed_fields so the LLM treats
    # the input as a fresh "answer" rather than another "edit" intent.
    llm_completed = [f for f in completed if f != target_field]
    llm_result = llm_classify_input(
        raw_input=new_value,
        current_field=target_field,
        field_meta=field_meta,
        options=options,
        completed_fields=llm_completed,
        values=state.get("values", {}),
        session_id=state.get("session_id"),
        service_id=state.get("service_id", "aws_ec2"),
    )
    if llm_result.get("action") == "answer":
        return llm_result["value"], None

    msg = llm_result.get(
        "message",
        f"Could not understand '{new_value}' for field '{target_field}'.",
    )
    if options:
        msg += f" Valid options: {options}"
    return None, msg


# ── Node ─────────────────────────────────────────────────────────────────────

def handle_edit(state: Agent2State) -> dict:
    """
    Edit handler node — validates intent, enforces dependency rules, and
    updates state while keeping field relationships consistent.
    """
    action = state.get("interpreted_action") or {}
    target_field = action.get("field")
    new_value = action.get("value")

    completed: list[str] = state.get("completed_fields", [])
    field_config: dict = state.get("field_config", {})
    service_id: str = state.get("service_id", "aws_ec2")
    values: dict = state.get("values", {})

    # ── Guard 1: field must have been filled already ──────────────────────────
    if target_field not in completed:
        return {
            "error": (
                f"❌ Cannot edit '{target_field}' — it has not been filled yet. "
                f"Please complete it in the normal flow first."
            ),
            "mode": "collect",
            "messages": [f"Edit rejected: '{target_field}' not in completed fields"],
        }

    # ── Guard 2: readonly (auto-filled) fields cannot be changed ─────────────
    meta = field_config.get(target_field, {})
    if meta.get("readonly"):
        return {
            "error": f"❌ '{target_field}' is auto-filled and cannot be changed.",
            "mode": "collect",
            "messages": [f"Edit rejected: '{target_field}' is readonly"],
        }

    # ── Guard 3: child-field cross-dependency check ───────────────────────────
    # If the user is trying to set a child field to a value that is invalid
    # for the currently selected parent, reject it immediately with clear options.
    parent_field = get_parent(target_field, field_config)
    if parent_field and new_value is not None:
        parent_value = values.get(parent_field)
        if parent_value is None:
            return {
                "error": (
                    f"❌ Cannot set '{target_field}' — its parent field "
                    f"'{parent_field}' has not been selected yet."
                ),
                "mode": "collect",
                "messages": [f"Edit rejected: parent '{parent_field}' not set"],
            }

        # Fetch valid options for the child given the current parent value
        valid_child_options = get_options_for_field(
            service_id, target_field, field_config, values
        )
        # Check the raw new_value against valid options (case-insensitive)
        raw_lower = new_value.strip().lower()
        matched = next(
            (o for o in valid_child_options if o.lower() == raw_lower), None
        )
        if valid_child_options and matched is None:
            return {
                "error": (
                    f"❌ '{new_value}' is not a valid {target_field} for "
                    f"{parent_field} '{parent_value}'. "
                    f"Valid options: {valid_child_options}"
                ),
                "mode": "collect",
                "messages": [
                    f"Edit rejected: '{new_value}' invalid for "
                    f"{parent_field}='{parent_value}'"
                ],
            }

    # ── Value provided — normalise → validate → apply ─────────────────────────
    if new_value is not None:
        # Guard 4: reject if submitted value is identical to the current saved value.
        current = values.get(target_field)
        if current is not None and str(new_value).strip().lower() == str(current).strip().lower():
            return {
                "error": (
                    f"'{target_field}' is already set to '{current}'. "
                    "Please provide a different value to update it."
                ),
                "mode": "collect",
                "messages": [f"Same-value rejected: {target_field}='{current}' unchanged."],
            }

        field_meta = field_config.get(target_field, {})
        options = get_options_for_field(service_id, target_field, field_config, values)

        normalised, err = _normalise_value(
            new_value, target_field, field_meta, options, completed, state
        )
        if err:
            return {"error": err, "mode": "collect"}

        ok, parsed, validation_err = validate_field(
            service_id=service_id,
            field=target_field,
            value=normalised,
            field_config=field_config,
            values=values,
        )
        if not ok:
            return {"error": validation_err, "mode": "collect"}

        updated_values = {**values, target_field: parsed}

        # ── Dependency cascade ────────────────────────────────────────────────
        # Parent field edited → unconditionally reset all children so the user
        # is prompted to re-enter them with the new parent context.
        # Independent / child field → use conditional cascade_invalidate (no-op
        # when the field has no children of its own).
        if _is_parent_field(service_id, target_field):
            updated_values, invalidated = reset_children(
                service_id, target_field, updated_values, field_config
            )
            success_msg = (
                f"✅ '{target_field}' updated to '{parsed}'. "
                f"Dependent fields reset and must be re-entered: {invalidated}"
                if invalidated
                else f"✅ '{target_field}' updated to '{parsed}'."
            )
        else:
            updated_values, invalidated = cascade_invalidate(
                service_id, target_field, updated_values, field_config
            )
            success_msg = f"✅ '{target_field}' updated to '{parsed}'."

        comp, miss = _recompute(state["field_order"], field_config, updated_values)

        return {
            "values": updated_values,
            "field_sources": {**state.get("field_sources", {}), target_field: "user"},
            "completed_fields": comp,
            "missing_fields": miss,
            "invalidated_fields": invalidated,
            "error": None,
            "mode": "collect",
            "messages": [
                f"Edited {target_field}={parsed}. "
                f"Reset: {invalidated}. "
                f"Missing after edit: {miss}"
            ],
            # Surface to frontend via next ask_field payload
            "_edit_success_message": success_msg,
        }

    # ── No value provided — null the field so post_action routes to it ───────
    # Setting only current_field is not enough: post_action reads missing_fields
    # and uses missing[0] as current_field, overriding whatever we set here.
    # Nulling the target field ensures _recompute places it first in missing
    # (it was the earliest completed field in field_order, so it becomes the
    # earliest missing), and post_action will correctly route ask_field to it.
    updated_values = {**values, target_field: None}
    updated_sources = {k: v for k, v in state.get("field_sources", {}).items()
                       if k != target_field}
    comp, miss = _recompute(state["field_order"], field_config, updated_values)

    return {
        "values": updated_values,
        "field_sources": updated_sources,
        "completed_fields": comp,
        "missing_fields": miss,
        "current_field": target_field,
        "mode": "collect",
        "error": None,
        "messages": [f"Edit mode: re-asking '{target_field}'"],
    }
