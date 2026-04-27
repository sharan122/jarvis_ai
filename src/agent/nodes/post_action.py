"""post_action node — convergence point that decides loop vs confirm_preview."""

from __future__ import annotations

from typing import Literal

from langgraph.types import Command

from agent.state import Agent2State


def post_action(state: Agent2State) -> Command[Literal["ask_field", "confirm_preview"]]:
    missing = state.get("missing_fields", [])

    if missing:
        return Command(
            update={"current_field": missing[0], "mode": "collect"},
            goto="ask_field",
        )

    # All fields complete — show preview and wait for explicit confirmation
    # before the graph is allowed to finalize.
    return Command(
        update={"current_field": None, "mode": "confirm"},
        goto="confirm_preview",
    )
