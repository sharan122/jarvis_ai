

from __future__ import annotations

from typing import Literal

from langgraph.graph import END
from langgraph.types import Command, interrupt

from agent.interpreter.fast_path import try_fast_path
from agent.interpreter.llm_classify import llm_classify_input
from agent.state import Agent2State

# ── Keyword sets (zero-LLM fast exits) ─────────────────────────────────────────

_CONFIRM_KEYWORDS: frozenset[str] = frozenset({
    # Explicit
    "yes", "confirm", "submit", "ok", "okay", "approve", "correct",
    # Save / submit intent
    "save", "save it", "save and submit", "submit it", "apply",
    # Positive affirmations
    "go ahead", "proceed", "done", "looks good", "all good",
    "looks correct", "that's correct", "that's right",
    "sure", "absolutely", "sounds good", "perfect", "great",
    "i confirm", "confirmed", "i agree", "agreed",
})

_CANCEL_KEYWORDS: frozenset[str] = frozenset({
    "cancel", "quit", "stop", "exit", "abort", "no", "nope", "nevermind",
})


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _build_preview_payload(state: Agent2State) -> dict:

    values: dict = state.get("values", {})
    completed: list[str] = state.get("completed_fields", [])
    missing: list[str] = state.get("missing_fields", [])
    sources: dict = state.get("field_sources", {})

    return {
        "status": "preview_ready",
        "message": (
            "All required fields have been filled. "
            "Please review and confirm to submit, "
            "or say 'change <field> to <value>' to make edits."
        ),
        # Matches handle_preview's payload structure exactly
        "service": state.get("service_id"),
        "completed": {
            f: {"value": values.get(f), "source": sources.get(f, "unknown")}
            for f in completed
        },
        "missing": missing,
        "progress": f"{len(completed)}/{len(completed) + len(missing)}",
        "error": state.get("error"),
    }


def _classify_intent(raw: str, state: Agent2State) -> dict:

    raw_lower = raw.strip().lower()
    completed: list[str] = state.get("completed_fields", [])

    # 1. Keyword match — zero tokens
    if raw_lower in _CONFIRM_KEYWORDS:
        return {"action": "confirm"}

    if raw_lower in _CANCEL_KEYWORDS:
        return {"action": "cancel"}

    # Use last completed field as context, mirroring _handle_post_completion_edit
    ctx_field = completed[-1] if completed else ""

    # 2. Fast path — zero tokens (catches "change region to us-east-2" etc.)
    fast = try_fast_path(raw, ctx_field, {}, [], completed)
    if fast and fast.get("action") in ("edit", "cancel"):
        return fast

    # 3. LLM fallback — handles indirect phrasing like "save it", "i need to edit region"
    llm_result = llm_classify_input(
        raw_input=raw,
        current_field=ctx_field,
        field_meta={},
        options=[],
        completed_fields=completed,
        values=state.get("values", {}),
        session_id=state.get("session_id"),
        service_id=state.get("service_id", "aws_ec2"),
    )

    llm_action = llm_result.get("action")

 
    if llm_action in ("edit", "cancel"):
        return llm_result


    if llm_action == "answer":
        return {"action": "confirm"}

    # unclear / help / preview → re-show preview with error nudge
    return {"action": "unclear"}


# ── Node ────────────────────────────────────────────────────────────────────────

def confirm_preview(
    state: Agent2State,
) -> Command[Literal["finalize", "handle_edit", "ask_field"]]:
  
    payload = _build_preview_payload(state)

    # ── PAUSE — graph stops here until Command(resume=...) ───────────────────
    user_answer: str = interrupt(payload)

    intent = _classify_intent(user_answer.strip(), state)
    action = intent.get("action")

    # ── Confirm ──────────────────────────────────────────────────────────────
    if action == "confirm":
        return Command(
            update={
                "mode": "confirm",
                "last_user_input": user_answer,
                "error": None,
                "messages": ["User confirmed — proceeding to finalize."],
            },
            goto="finalize",
        )

    # ── Cancel ───────────────────────────────────────────────────────────────
    if action == "cancel":
        return Command(
            update={
                "mode": "collect",
                "last_user_input": user_answer,
                "error": None,
                "messages": ["User cancelled at confirmation step."],
            },
            goto=END,
        )

    # ── Edit ─────────────────────────────────────────────────────────────────
    if action == "edit":
        field = intent.get("field")
        value = intent.get("value")

        if value is not None:

            current = state.get("values", {}).get(field)
            if current is not None and str(value).strip().lower() == str(current).strip().lower():
                return Command(
                    update={
                        "error": (
                            f"'{field}' is already set to '{current}'. "
                            "Please provide a different value to update it."
                        ),
                        "last_user_input": user_answer,
                        "messages": [f"Same-value rejected: {field}='{current}' unchanged."],
                    },
                    goto="confirm_preview",
                )

            return Command(
                update={
                    "mode": "collect",
                    "interpreted_action": intent,
                    "last_user_input": user_answer,
                    "error": None,
                    "messages": [f"Edit at confirmation: {field} → {value}"],
                },
                goto="handle_edit",
            )


        return Command(
            update={
                "mode": "collect",
                "current_field": field,
                "last_user_input": user_answer,
                "error": None,
                "messages": [f"Re-asking '{field}' at user request."],
            },
            goto="ask_field",
        )

    # ── Unclear — re-show preview with a helpful nudge ───────────────────────
    return Command(
        update={
            "error": (
                "Sorry, I didn't understand that. "
                "Type 'confirm' to submit, 'cancel' to abort, "
                "or 'change <field> to <value>' to edit a value."
            ),
            "last_user_input": user_answer,
            "messages": [f"Unclear input at confirmation: '{user_answer}'"],
        },
        goto="confirm_preview",
    )
