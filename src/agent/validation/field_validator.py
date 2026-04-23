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
            field_label = meta.get("prompt", field).replace("Select ", "")
            options_str = ", ".join(str(o) for o in options)
            return (
                False,
                None,
                f"'{value}' is not a valid choice for \"{field_label}\". "
                f"Please pick one of: {options_str}.",
            )
        return True, value, None

    # ── Number ──
    if field_type == "number":
        try:
            num = int(str(value).strip())
        except (ValueError, TypeError):
            field_label = meta.get("prompt", field).replace("Enter ", "")
            return False, None, f"Please enter a valid number for \"{field_label}\"."

        rules = meta.get("validator") or {}
        min_v = rules.get("min")
        max_v = rules.get("max")

        if min_v is not None and num < min_v:
            field_label = meta.get("prompt", field).replace("Enter ", "")
            return (
                False, None,
                f"{num} is too small for \"{field_label}\". Minimum allowed is {min_v} GB.",
            )
        if max_v is not None and num > max_v:
            field_label = meta.get("prompt", field).replace("Enter ", "")
            return (
                False, None,
                f"{num} is too large for \"{field_label}\". Maximum allowed is {max_v} GB.",
            )

        return True, num, None

    # ── Text ──
    text = str(value).strip() if value is not None else ""
    if meta.get("required") and not text:
        return False, None, f"{field} cannot be empty."
    return True, text, None
