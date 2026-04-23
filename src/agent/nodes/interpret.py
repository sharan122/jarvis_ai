"""interpret node — classifies user input (fast path first, LLM fallback)."""

from __future__ import annotations

from agent.interpreter.fast_path import try_fast_path
from agent.interpreter.llm_classify import llm_classify_input
from agent.state import Agent2State
from agent.tools.options import get_options_for_field


def interpret_input(state: Agent2State) -> dict:
    raw = str(state["last_user_input"]).strip()
    field = state["current_field"]
    field_meta = state["field_config"][field]

    options = get_options_for_field(
        state["service_id"], field, state["field_config"], state["values"]
    )

    completed = state.get("completed_fields", [])

    # ── Fast path (no LLM) ──
    fast_result = try_fast_path(raw, field, field_meta, options, completed)
    if fast_result is not None:
        return {
            "interpreted_action": fast_result,
            "messages": [f"Fast path: {fast_result.get('action')} for {field}"],
        }

    # ── Slow path (LLM) ──
    llm_result = llm_classify_input(
        raw_input=raw,
        current_field=field,
        field_meta=field_meta,
        options=options,
        completed_fields=state.get("completed_fields", []),
        values=state.get("values", {}),
        service_id=state.get("service_id", "aws_ec2"),
    )

    result: dict = {
        "interpreted_action": llm_result,
        "messages": [f"LLM path: {llm_result}"],
    }

    # If unclear, set a friendly error so ask_field can display it to the user
    if llm_result.get("action") == "unclear":
        field_type = field_meta.get("type", "text")
        field_label = field_meta.get("prompt", field).replace("Select ", "").replace("Enter ", "")

        if field_type == "select" and options:
            options_str = ", ".join(options)
            msg = (
                f"That doesn't match any of the available options for {field_label}. "
                f"Please choose one of: {options_str}."
            )
        elif field_type == "number":
            rules = field_meta.get("validator") or {}
            min_v = rules.get("min")
            max_v = rules.get("max")
            if min_v is not None and max_v is not None:
                msg = f"Please enter a number between {min_v} and {max_v} for \"{field_label}\"."
            else:
                msg = f"Please enter a valid number for \"{field_label}\"."
        else:
            msg = (
                f"Sorry, I couldn't understand that response for \"{field_label}\". "
                "Could you please try again?"
            )
        result["error"] = msg

    return result
