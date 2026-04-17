"""Quality enrichment and final payload validation — deterministic Python, no LLM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.tools.options import get_options_for_field


def quality_enrichment(payload: dict[str, Any], state: dict) -> dict[str, Any]:
    """
    Deterministic enrichment applied after all values are collected.
    Adds derived fields, normalises values, attaches metadata.
    """
    enriched = dict(payload)

    # Derive resource name
    app = enriched.get("application_name", "app")
    env = enriched.get("environment", "env")
    region = enriched.get("region", "region")
    enriched["resource_name"] = f"{app}-{env}-{region}".lower()

    # Metadata
    enriched["provisioned_at"] = datetime.now(timezone.utc).isoformat()
    enriched["session_id"] = state.get("session_id", "unknown")
    enriched["provisioned_by"] = state.get("user_id", "unknown")
    enriched["validated"] = True

    # Normalise environment to uppercase
    if "environment" in enriched:
        enriched["environment"] = enriched["environment"].upper()

    return enriched


def final_payload_validation(
    payload: dict[str, Any],
    field_config: dict[str, dict],
    field_order: list[str],
    service_id: str,
) -> list[str]:
    """
    Run final cross-field validation.
    Returns list of error strings.  Empty list == valid.
    """
    errors: list[str] = []

    # Completeness check
    for field in field_order:
        meta = field_config.get(field, {})
        if meta.get("required") and field not in payload:
            errors.append(f"Missing required field: {field}")

    # Cross-field dependency consistency
    for field, meta in field_config.items():
        parent = meta.get("depends_on")
        if not parent:
            continue
        if field in payload and parent in payload:
            valid_opts = get_options_for_field(
                service_id, field, field_config, payload
            )
            if payload[field] not in valid_opts:
                errors.append(
                    f"{field}='{payload[field]}' is invalid for "
                    f"{parent}='{payload[parent]}'"
                )

    return errors
