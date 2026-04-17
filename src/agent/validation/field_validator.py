"""Per-field validation logic."""

from __future__ import annotations

from typing import Any

from agent.tools.options import get_options_for_field


def validate_field(
    service_id: str,
    field: str,
    value: Any,
    field_config: dict[str, dict],
    values: dict[str, Any],
) -> tuple[bool, Any, str | None]:
    """
    Validate a single field value.

    Returns (ok, parsed_value, error_message).
    On success:  (True,  parsed_value, None)
    On failure:  (False, None,          error_string)
    """
    meta = field_config.get(field, {})
    field_type = meta.get("type", "text")

    # ── Select ──
    if field_type == "select":
        options = get_options_for_field(service_id, field, field_config, values)
        if value not in options:
            return False, None, f"'{value}' is not valid for {field}. Options: {options}"
        return True, value, None

    # ── Number ──
    if field_type == "number":
        try:
            num = int(str(value).strip())
        except (ValueError, TypeError):
            return False, None, f"{field} must be a number."

        rules = meta.get("validator") or {}
        min_v = rules.get("min")
        max_v = rules.get("max")

        if min_v is not None and num < min_v:
            return False, None, f"{field} must be at least {min_v}. You entered {num}."
        if max_v is not None and num > max_v:
            return False, None, f"{field} must be at most {max_v}. You entered {num}."

        return True, num, None

    # ── Text ──
    text = str(value).strip() if value is not None else ""
    if meta.get("required") and not text:
        return False, None, f"{field} cannot be empty."
    return True, text, None
