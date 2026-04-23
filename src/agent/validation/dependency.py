"""Field dependency management — cascade invalidation and child resets."""

from __future__ import annotations

from typing import Any

from agent.tools.options import get_options_for_field
from agent.validation.dependency_map import get_children


def cascade_invalidate(
    service_id: str,
    changed_field: str,
    values: dict[str, Any],
    field_config: dict[str, dict],
) -> tuple[dict[str, Any], list[str]]:
    """
    After a field value changes, invalidate dependent children whose
    current value is no longer in the valid options.

    Returns (updated_values, list_of_invalidated_field_names).
    """
    updated = dict(values)
    invalidated: list[str] = []

    for child_field, meta in field_config.items():
        if meta.get("depends_on") != changed_field:
            continue

        child_value = updated.get(child_field)
        if child_value is None:
            continue

        valid_options = get_options_for_field(
            service_id, child_field, field_config, updated
        )

        if child_value not in valid_options:
            del updated[child_field]
            invalidated.append(child_field)

            # Recurse: cascade further if this child has its own dependents
            updated, deeper = cascade_invalidate(
                service_id, child_field, updated, field_config
            )
            invalidated.extend(deeper)

    return updated, invalidated


def reset_children(
    service_id: str,
    changed_field: str,
    values: dict[str, Any],
    field_config: dict[str, dict],
) -> tuple[dict[str, Any], list[str]]:

    updated = dict(values)
    reset: list[str] = []

    for child in get_children(service_id, changed_field):
        if child in updated and updated[child] is not None:
            updated[child] = None
            reset.append(child)

            # Recurse: if that child itself has dependents, reset them too
            updated, deeper = reset_children(service_id, child, updated, field_config)
            reset.extend(deeper)

    return updated, reset
