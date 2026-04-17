"""handle_help node — returns help text without advancing the form."""

from __future__ import annotations

from agent.state import Agent2State


def handle_help(state: Agent2State) -> dict:
    action = state.get("interpreted_action") or {}
    field = action.get("field") or state.get("current_field")
    field_meta = state.get("field_config", {}).get(field, {})

    # Level 1: config-based help (free, instant)
    help_text = field_meta.get("help", "No help available for this field.")

    # Level 2 (future): knowledge box API for deeper questions
    # if is_complex_question(state["last_user_input"]):
    #     help_text += "\n\n" + knowledge_tool(field, state["service_id"], ...)

    return {
        "help_context": field,
        "help_response": help_text,
        "mode": "collect",
        "messages": [f"Help served for {field}: {help_text}"],
    }
