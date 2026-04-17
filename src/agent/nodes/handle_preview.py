"""handle_preview node — returns a summary of collected values."""

from __future__ import annotations

from agent.state import Agent2State


def handle_preview(state: Agent2State) -> dict:
    completed = state.get("completed_fields", [])
    missing = state.get("missing_fields", [])
    values = state.get("values", {})
    sources = state.get("field_sources", {})

    preview = {
        "service": state.get("service_id"),
        "completed": {
            f: {"value": values.get(f), "source": sources.get(f, "unknown")}
            for f in completed
        },
        "missing": missing,
        "progress": f"{len(completed)}/{len(completed) + len(missing)}",
    }

    return {
        "mode": "collect",
        "messages": [
            f"Preview: {len(completed)} done, {len(missing)} remaining. "
            f"Data: {preview}"
        ],
    }
