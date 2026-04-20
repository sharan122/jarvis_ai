"""ask_field node — pauses execution with interrupt() and presents a question."""

from __future__ import annotations

from langgraph.types import interrupt

from agent.state import Agent2State
from agent.tools.options import get_options_for_field


def ask_field(state: Agent2State) -> dict:
    service_id = state["service_id"]
    field = state["current_field"]
    field_meta = state["field_config"][field]
    error = state.get("error")
    help_response = state.get("help_response")

    # Fetch valid options from Redis
    options = get_options_for_field(
        service_id, field, state["field_config"], state["values"]
    )
    preview_response = state.get("preview_response")

    # Build self-contained interrupt payload for the frontend
    payload: dict = {
        "field": field,
        "prompt": field_meta["prompt"],
        "help_text": field_meta.get("help", ""),
        "type": field_meta["type"],
        "required": field_meta.get("required", False),
        "options": options,
        "current_value": state["values"].get(field),
        "error": error,
        "depends_on": None,
        "validation_rules": field_meta.get("validator"),
        "progress": {
            "total_required": len(state.get("missing_fields", []))
            + len(state.get("completed_fields", [])),
            "completed": len(state.get("completed_fields", [])),
            "current_step": len(state.get("completed_fields", [])) + 1,
            "missing": state.get("missing_fields", []),
        },
        "filled_so_far": {
            k: v
            for k, v in state["values"].items()
            if k in state.get("completed_fields", [])
        },
    }

    if field_meta.get("depends_on"):
        payload["depends_on"] = {
            "field": field_meta["depends_on"],
            "value": state["values"].get(field_meta["depends_on"]),
        }

    if help_response:
        payload["help_response"] = help_response
        
    if preview_response:
        payload["preview"] = preview_response

    # ── PAUSE — graph stops here until Command(resume=...) ──
    user_answer = interrupt(payload)

    turn = state.get("turn_count", 0) + 1
    return {
        "last_user_input": user_answer,
        "error": None,
        "help_response": None,
        "preview_response": None,
        "turn_count": turn,
        "messages": [f"[turn {turn}] User input for {field}: {user_answer}"],
    }
