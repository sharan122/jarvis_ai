"""FastAPI routes for Agent 2."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from agent.graph import get_default_app
from agent.tracing import create_callback_handler, flush_handler, get_callback_handler
from models.models import EditRequest, ResumeRequest, SessionResponse, StartRequest
from redis_loader.loader import load_all as load_redis_data

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
            detail=f"Session '{req.session_id}' not found. It may have expired or the server was restarted before this fix. Please start a new session.",
        )

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


@router.post("/edit", response_model=SessionResponse)
def edit_field(req: EditRequest):
    """
    Directly edit a previously filled field.

    The frontend sends field name + optional new value.
    This injects an edit action into the graph by resuming
    with a structured edit command that the interpret node
    recognises via the fast path.
    """
    app = _get_app()

    if not _session_exists(req.session_id):
        raise HTTPException(
            status_code=404,
            detail=f"Session '{req.session_id}' not found. It may have expired or the server was restarted before this fix. Please start a new session.",
        )

    handler = get_callback_handler(req.session_id)
    config = _make_config(req.session_id, handler)

    if req.value:
        answer = f"change {req.field} to {req.value}"
    else:
        answer = f"edit {req.field}"

    try:
        result = app.invoke(Command(resume=answer), config=config)
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

    return SessionResponse(
        session_id=req.session_id,
        status="cancelled",
    )



