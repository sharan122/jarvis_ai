"""Policy guardrails applied before final submission."""

from __future__ import annotations

from typing import Any


def apply_guardrails(
    payload: dict[str, Any],
    user_context: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """
    Run policy checks.  Returns (allowed, reason).

    ``user_context`` is the User Json with ad_groups, allowed_accounts, etc.
    """
    user_context = user_context or {}

    # Guard 1: account authorisation
    allowed_accounts = user_context.get("allowed_accounts", [])
    if allowed_accounts and payload.get("account_id") not in allowed_accounts:
        return False, f"User not authorised for account {payload.get('account_id')}"

    # Guard 2: PROD requires approval flag
    if payload.get("environment") == "PROD":
        if not user_context.get("prod_approved"):
            return False, "PROD provisioning requires manager approval."

    # Guard 3: large instance types blocked in DEV
    large_types = {"m5.xlarge", "c5.2xlarge", "r5.xlarge"}
    if (
        payload.get("instance_type") in large_types
        and payload.get("environment") == "DEV"
    ):
        return False, "Large instance types are not allowed in the DEV environment."

    return True, None
