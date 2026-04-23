"""FastAPI routes for Agent 2."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from agent.graph import get_default_app
from agent.tracing import create_callback_handler, flush_handler, get_callback_handler
from models.models import ResumeRequest, SessionResponse, StartRequest
from redis_loader.loader import load_all as load_redis_data
from agent.interpreter.fast_path import try_fast_path
from agent.interpreter.llm_classify import llm_classify_input
from agent.nodes.handle_edit import handle_edit as _apply_edit
router = APIRouter(prefix="/api/agent2", tags=["agent2"])

# ── Singleton graph app (created once, reused) ──
_app = None


def _get_app():
    global _app
    if _app is None:
        load_redis_data()
        _app = get_default_app()
    return _app


def _extract_interrupt(result: dict) -> dict | None:
    """Pull the interrupt payload out of the graph result."""
    interrupts = result.get("__interrupt__", ())
    if not interrupts:
        return None
    first = interrupts[0]
    return first.value if hasattr(first, "value") else first


def _make_config(thread_id: str, handler=None) -> dict:
    """Build a LangGraph invoke config, optionally attaching the Langfuse callback."""
    config: dict = {"configurable": {"thread_id": thread_id}}
    if handler is not None:
        config["callbacks"] = [handler]
    return config


def _session_exists(session_id: str) -> bool:
    """Return True if the checkpointer has a stored checkpoint for this session."""
    try:
        app = _get_app()
        config = {"configurable": {"thread_id": session_id}}
        snapshot = app.get_state(config)
        # snapshot.values is empty dict when no checkpoint exists
        return bool(snapshot and snapshot.values)
    except Exception:
        return False


def _session_is_finalized(session_id: str) -> bool:
    """Return True if the graph has already reached END (no pending interrupt).

    LangGraph sets snapshot.next to an empty tuple once the graph finishes.
    A session with a pending interrupt always has at least one entry in next.
    """
    try:
        app = _get_app()
        config = {"configurable": {"thread_id": session_id}}
        snapshot = app.get_state(config)
        # next is () when graph is at END; non-empty when waiting at interrupt
        return bool(snapshot and snapshot.values and not snapshot.next)
    except Exception:
        return False


def _handle_post_completion_edit(req: ResumeRequest, app) -> SessionResponse:



    snapshot = app.get_state(_make_config(req.session_id))
    saved: dict = dict(snapshot.values)

    completed: list = saved.get("completed_fields", [])
    service_id: str = saved.get("service_id", "aws_ec2")
    values: dict = saved.get("values", {})

    raw = req.answer.strip()

 
    ctx_field = completed[-1] if completed else ""
    fast = try_fast_path(raw, ctx_field, {}, [], completed)
    if fast and fast.get("action") == "edit":
        action = fast
    else:
        llm_result = llm_classify_input(
            raw_input=raw,
            current_field=ctx_field,
            field_meta={},
            options=[],
            completed_fields=completed,
            values=values,
            session_id=req.session_id,
            service_id=service_id,
        )
        action = llm_result if llm_result.get("action") == "edit" else None

    if not action:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Session '{req.session_id}' is already complete. "
                "To change a field say e.g. 'change environment to PROD'. "
                "Otherwise please start a new session."
            ),
        )

    # ── Apply edit: validate + cascade-reset dependents ──────────────────────
    edit_state = {**saved, "interpreted_action": action, "last_user_input": raw}
    edit_result = _apply_edit(edit_state)

    if edit_result.get("error"):
        raise HTTPException(status_code=400, detail=edit_result["error"])

    # ── Determine updated values for re-invocation ───────────────────────────
    if "values" in edit_result:
        # Edit supplied a value — handle_edit already applied cascade-reset
        updated_values = edit_result["values"]
    else:
        # No value in the edit intent — null the field so bootstrap re-asks it
        target = action.get("field")
        updated_values = {**values, target: None} if target else values

    # ── Re-invoke the graph with the modified values ──────────────────────────
    # Bootstrap re-reads the config and recalculates completed/missing from
    # updated_values, then routes to ask_field for every null required field.
    new_initial_state = {
        "session_id": req.session_id,
        "service_id": service_id,
        "user_id": saved.get("user_id", ""),
        "values": updated_values,
        "messages": [],
    }

    handler = get_callback_handler(req.session_id)
    config = _make_config(req.session_id, handler)
    result = app.invoke(new_initial_state, config=config)

    payload = _extract_interrupt(result)
    if payload:
        return SessionResponse(
            session_id=req.session_id,
            status="collecting",
            payload=payload,
        )

    mode = result.get("mode", "")
    if mode == "done":
        flush_handler(req.session_id)
        return SessionResponse(
            session_id=req.session_id,
            status="done",
            final_json=result.get("final_json"),
            agent_json=result.get("agent_json"),
        )

    flush_handler(req.session_id)
    return SessionResponse(session_id=req.session_id, status="cancelled")


# ── Endpoints ──

@router.post("/start", response_model=SessionResponse)
def start_session(req: StartRequest):
    app = _get_app()
    thread_id = f"{req.user_id}_{req.service_id}_{int(time.time())}"

    # ── Create a Langfuse CallbackHandler for this session ──
    handler = create_callback_handler(
        session_id=thread_id,
        user_id=req.user_id,
        service_id=req.service_id,
    )

    config = _make_config(thread_id, handler)

    initial_state = {
        "session_id": thread_id,
        "service_id": req.service_id,
        "user_id": req.user_id,
        "values": req.initial_values or {},
        "messages": [],
    }

    result = app.invoke(initial_state, config=config)
    payload = _extract_interrupt(result)

    if payload:
        return SessionResponse(
            session_id=thread_id,
            status="collecting",
            payload=payload,
        )

    # All fields were pre-filled — already finalized
    flush_handler(thread_id)
    return SessionResponse(
        session_id=thread_id,
        status="done",
        final_json=result.get("final_json"),
        agent_json=result.get("agent_json"),
    )


@router.post("/resume", response_model=SessionResponse)
def resume_session(req: ResumeRequest):
    app = _get_app()

    if not _session_exists(req.session_id):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Session '{req.session_id}' not found. "
                "It may have expired or the server was restarted. "
                "Please start a new session."
            ),
        )

    # If the session already reached END, treat the message as a post-completion
    # edit rather than silently re-running and returning the same final_json.
    if _session_is_finalized(req.session_id):
        return _handle_post_completion_edit(req, app)

    # ── Reuse the existing session's Langfuse handler ──
    handler = get_callback_handler(req.session_id)
    config = _make_config(req.session_id, handler)

    try:
        result = app.invoke(Command(resume=req.answer), config=config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    payload = _extract_interrupt(result)

    if payload:
        return SessionResponse(
            session_id=req.session_id,
            status="collecting",
            payload=payload, 
        )

    mode = result.get("mode", "")
    if mode == "done":
        flush_handler(req.session_id)
        return SessionResponse(
            session_id=req.session_id,
            status="done",
            final_json=result.get("final_json"),
            agent_json=result.get("agent_json"),
        )

    # Cancelled or other terminal state
    flush_handler(req.session_id)
    return SessionResponse(
        session_id=req.session_id,
        status="cancelled",
    )



