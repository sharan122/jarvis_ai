"""Bootstrap node — loads config, merges enrichment, computes initial state."""

from __future__ import annotations

from typing import Literal

from langgraph.types import Command

from agent.state import Agent2State
from agent.tools.config_loader import load_service_config


def bootstrap(state: Agent2State) -> Command[Literal["ask_field", "finalize"]]:
    service_id = state["service_id"]
    config = load_service_config(service_id)

    # ── Three-layer merge ──
    merged_values: dict = {}
    merged_sources: dict = {}

    # Layer 1: defaults from config
    for k, v in config.get("default_json", {}).items():
        merged_values[k] = v
        merged_sources[k] = "default"

    # Layer 2: user enrichment (overrides defaults)
    for k, v in config.get("user_enrichment", {}).items():
        if v is not None and v != "":
            merged_values[k] = v
            merged_sources[k] = "enrichment"

    # Layer 3: values passed in (from Agent 1 or a previous session)
    for k, v in (state.get("values") or {}).items():
        if v is not None and v != "":
            merged_values[k] = v
            merged_sources[k] = "user"

    # ── Compute missing / completed ──
    field_order: list[str] = config["field_order"]
    fields_meta: dict = config["fields"]

    completed: list[str] = []
    missing: list[str] = []
    for f in field_order:
        meta = fields_meta.get(f, {})
        if not meta.get("required", False):
            continue
        if f in merged_values and merged_values[f] is not None:
            completed.append(f)
        else:
            missing.append(f)

    updates: dict = {
        "field_order": field_order,
        "field_config": fields_meta,
        "default_json": config.get("default_json", {}),
        "user_enrichment": config.get("user_enrichment", {}),
        "values": merged_values,
        "field_sources": merged_sources,
        "missing_fields": missing,
        "completed_fields": completed,
        "service_version": config["version"],
        "mode": "collect",
        "turn_count": 0,
        "retry_count": 0,
        "error": None,
        "help_response": None,
        "invalidated_fields": [],
        "messages": [
            f"Session started for {service_id} v{config['version']}. "
            f"Pre-filled {len(completed)} fields. "
            f"Need {len(missing)} more: {missing}"
        ],
    }

    if missing:
        updates["current_field"] = missing[0]
        return Command(update=updates, goto="ask_field")

    updates["current_field"] = None
    return Command(update=updates, goto="finalize")
