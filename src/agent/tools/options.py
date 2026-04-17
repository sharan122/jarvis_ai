"""Tool: fetch valid options for a field from Redis."""

from __future__ import annotations

from typing import Any

from agent.tools.redis_client import get_redis_client


def get_options(
    service_id: str,
    field: str,
    options_key: str | None,
    depends_on_field: str | None = None,
    depends_on_value: str | None = None,
) -> list[str]:
    """
    Fetch valid options from Redis for a given field.

    Independent fields:  redis key = "{service_id}:{options_key}" -> list
    Dependent fields:    redis key = "{service_id}:{options_key}" -> dict[parent] -> list
    """
    if options_key is None:
        return []

    client = get_redis_client()
    redis_key = f"{service_id}:{options_key}"
    data: Any = client.get_json(redis_key)

    if data is None:
        return []

    # Dependent field: data is a dict keyed by parent value
    if depends_on_field and isinstance(data, dict):
        if depends_on_value is None:
            return []
        return data.get(depends_on_value, [])

    if isinstance(data, list):
        return data

    return []


def get_options_for_field(
    service_id: str,
    field: str,
    field_config: dict[str, dict],
    values: dict[str, Any],
) -> list[str]:
    """Convenience wrapper that reads field metadata and calls get_options."""
    meta = field_config.get(field, {})
    depends_on = meta.get("depends_on")
    return get_options(
        service_id=service_id,
        field=field,
        options_key=meta.get("options_key"),
        depends_on_field=depends_on,
        depends_on_value=values.get(depends_on) if depends_on else None,
    )
