"""post_action node — convergence point that decides loop vs finalize."""

from __future__ import annotations

from typing import Literal

from langgraph.types import Command

from agent.state import Agent2State


def post_action(state: Agent2State) -> Command[Literal["ask_field", "finalize"]]:
    missing = state.get("missing_fields", [])

    if missing:
        return Command(
            update={"current_field": missing[0], "mode": "collect"},
            goto="ask_field",
        )

    return Command(
        update={"current_field": None},
        goto="finalize",
    )
