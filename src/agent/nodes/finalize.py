"""finalize node — builds Agent Json, merges with Default Json, validates."""

from __future__ import annotations

from agent.state import Agent2State
from agent.validation.enrichment import final_payload_validation, quality_enrichment


def finalize(state: Agent2State) -> dict:
    values = state["values"]
    field_order = state["field_order"]

    # ── Agent Json (collected values only) ──
    agent_json = {
        f: values[f]
        for f in field_order
        if f in values and values[f] is not None
    }

    # ── Merge: Default Json + Agent Json ──
    final: dict = {}
    final.update(state.get("default_json", {}))
    final.update(agent_json)

    # ── Quality enrichment (deterministic) ──
    final = quality_enrichment(final, state)

    # ── Final cross-field validation ──
    errors = final_payload_validation(
        final, state["field_config"], field_order, state["service_id"]
    )
    if errors:
        return {
            "error": f"Final validation failed: {errors}",
            "mode": "collect",
            "messages": [f"Finalize blocked: {errors}"],
        }

    return {
        "agent_json": agent_json,
        "final_json": final,
        "mode": "done",
        "messages": ["Form complete. Final JSON generated and validated."],
    }
