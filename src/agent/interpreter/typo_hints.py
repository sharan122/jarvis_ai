"""
Typo-hints dispatcher.

For each field key, we maintain a dictionary of:
    { "probable_wrong_input": "correct_canonical_value" }

Hints are split into per-service files to keep each file small and to
avoid injecting irrelevant hints into the LLM prompt:

    typo_hints_aws_ec2.py   — AWS EC2 instance fields
    typo_hints_azure_vm.py  — Azure VM fields
    (add more by following the same pattern)

When the LLM classifier calls get_typo_hints() it passes the service_id
so only that service's hints are loaded.  The returned dict (or None) is
injected as a compact block into the prompt at call-time, keeping the
stored Langfuse prompt template lean and field-agnostic.

Design notes:
- Only realistic common mistakes are included — not an exhaustive list.
- Keys are lowercase so matching is case-insensitive in the LLM prompt.
- The LLM already knows the full list of valid options from `options`;
  these hints just give it extra context for fuzzy matching.
- Adding a new service requires only a new typo_hints_<service_id>.py
  file exporting a top-level HINTS dict — no changes to this file.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal registry cache  (service_id → HINTS dict)
# ---------------------------------------------------------------------------
_registry: dict[str, dict[str, dict[str, str]]] = {}


def _load_hints(service_id: str) -> dict[str, dict[str, str]]:
    """
    Dynamically import typo_hints_<service_id>.py and cache its HINTS dict.

    Returns an empty dict if no hints file exists for the service — this is
    not an error; it just means no typo correction for that service.
    """
    if service_id in _registry:
        return _registry[service_id]

    module_name = f"agent.interpreter.typo_hints_{service_id}"
    try:
        module = importlib.import_module(module_name)
        hints: dict[str, dict[str, str]] = getattr(module, "HINTS", {})
    except ModuleNotFoundError:
        logger.debug(
            "[typo_hints] No hints file found for service '%s' (%s). "
            "Typo correction will be skipped for this service.",
            service_id,
            module_name,
        )
        hints = {}
    except Exception as exc:
        logger.warning(
            "[typo_hints] Failed to load hints for service '%s': %s",
            service_id,
            exc,
        )
        hints = {}

    _registry[service_id] = hints
    return hints


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_typo_hints(
    field_key: str,
    user_input: str,
    service_id: str = "aws_ec2",
) -> dict[str, str] | None:
    """
    Return the probable-wrong → correct mapping for *field_key* under
    *service_id*.

    Returns None if no hints are registered for this field so the caller
    can omit the hint block from the prompt entirely (zero prompt tokens).

    Args:
        field_key:   The config field name (e.g. "region", "vm_size").
        user_input:  Raw string entered by the user (reserved for future
                     dynamic filtering; currently unused).
        service_id:  Service identifier that selects which hints file to
                     load (e.g. "aws_ec2", "azure_vm").

    Returns:
        A dict of { wrong: correct } pairs, or None.
    """
    hints = _load_hints(service_id)
    return hints.get(field_key) or None


def clear_hints_cache() -> None:
    """Clear the in-process hints cache (useful in tests)."""
    _registry.clear()
