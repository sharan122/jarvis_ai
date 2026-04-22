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

    # If unclear, set an error so ask_field can display it to the user
    if llm_result.get("action") == "unclear":
        msg = llm_result.get("message", "Could not understand your input.")
        if options:
            msg += f" Valid options: {options}"
        result["error"] = msg

    return result
