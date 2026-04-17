"""
Fast-path interpreter — deterministic classification with zero LLM tokens.

Handles ~80% of user inputs: exact matches, partial matches, numbers, keywords.
"""

from __future__ import annotations

import re
from typing import Any

_HELP_KEYWORDS = frozenset({"help", "?", "what is this", "info", "explain"})
_PREVIEW_KEYWORDS = frozenset({"preview", "show", "summary", "show me", "review"})
_CANCEL_KEYWORDS = frozenset({"cancel", "quit", "stop", "exit", "abort"})

_EDIT_RE = re.compile(
    r"^(?:change|update|edit)\s+([\w_]+)(?:\s+to\s+(.+))?$", re.IGNORECASE
)


def try_fast_path(
    raw_input: str,
    field: str,
    field_meta: dict[str, Any],
    options: list[str],
    completed_fields: list[str] | None = None,
) -> dict | None:
    """
    Attempt to classify user input without calling the LLM.

    Returns an action dict if classification succeeds, otherwise None
    (meaning the slow LLM path should be used).
    """
    raw = raw_input.strip()
    raw_lower = raw.lower()

    # 1. Help keywords
    if raw_lower in _HELP_KEYWORDS:
        return {"action": "help", "field": field}

    # 2. Preview keywords
    if raw_lower in _PREVIEW_KEYWORDS:
        return {"action": "preview"}

    # 3. Cancel keywords
    if raw_lower in _CANCEL_KEYWORDS:
        return {"action": "cancel"}

    field_type = field_meta.get("type", "text")

    # 4. Exact option match (case-insensitive)
    if field_type == "select" and options:
        for opt in options:
            if opt.lower() == raw_lower:
                return {"action": "answer", "value": opt}

    # 5. Number field — direct parse
    if field_type == "number":
        try:
            return {"action": "answer", "value": int(raw)}
        except ValueError:
            # Could be natural language like "one hundred", let LLM handle
            pass

    # 6. Unique partial / substring match for select fields
    if field_type == "select" and options and raw_lower:
        matches = [o for o in options if raw_lower in o.lower()]
        if len(matches) == 1:
            return {"action": "answer", "value": matches[0]}

    # 7. Edit command: "change region to us-east-2", "edit availability_zone"
    edit_match = _EDIT_RE.match(raw)
    if edit_match and completed_fields:
        target = edit_match.group(1).lower()
        new_val = edit_match.group(2).strip() if edit_match.group(2) else None
        for cf in completed_fields:
            if cf.lower() == target or target in cf.lower():
                return {"action": "edit", "field": cf, "value": new_val}

    # 8. Text field — accept non-empty input as-is
    if field_type == "text" and raw:
        return {"action": "answer", "value": raw}

    # Could not resolve deterministically
    return None