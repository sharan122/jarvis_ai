"""
Central Langfuse tracing module for Agent 2 — Langfuse SDK v4 compatible.

Responsible for the LangChain CallbackHandler lifecycle only.
Prompt fetching is handled by agent.prompt_service.PromptService.

Lifecycle per request:
  1. Routes call create_callback_handler(session_id, user_id, service_id).
  2. Routes pass the handler via config={"callbacks": [handler]} to every invoke().
  3. Routes call flush_handler(session_id) at the end of the session.
"""

from __future__ import annotations

import logging
import os
from typing import Any
import langfuse
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
logger = logging.getLogger(__name__)

# ── Singleton Langfuse client (init once) ──
_langfuse_client = None
_initialized = False

# ── Active handlers & metadata per session ──
_handlers: dict[str, Any] = {}
_session_meta: dict[str, dict] = {}   # session_id → {user_id, service_id}


def initialize_langfuse() -> bool:
    """
    Initialize the Langfuse client once at application startup.
    This must be called before any CallbackHandler is created so the
    singleton (with the correct keys) is registered globally.
    Returns True if initialization succeeded.
    """
    global _langfuse_client, _initialized
    if _initialized:
        return _langfuse_client is not None

    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    host = os.environ.get("LANGFUSE_HOST")

    if not secret_key or not public_key:
        logger.warning(
            "[Langfuse] LANGFUSE_SECRET_KEY / LANGFUSE_PUBLIC_KEY not set — tracing disabled."
        )
        _initialized = True
        return False

    try:

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _initialized = True
        logger.info("[Langfuse] Client initialized.")
        return True
    except Exception as exc:
        logger.error("[Langfuse] Client init failed: %s", exc)
        _initialized = True
        return False


def _get_client():
    if not _initialized:
        initialize_langfuse()
    return _langfuse_client


# ── CallbackHandler lifecycle ──

def create_callback_handler(session_id: str, user_id: str, service_id: str):
    """
    Create a Langfuse v4 LangChain CallbackHandler for this session.

    Stores session metadata and enters a per-request propagate_attributes()
    context so every span in this HTTP request is tagged with the correct
    session_id, user_id, and tags.

    On subsequent requests (resume, edit), get_callback_handler() will
    re-enter the context automatically using the stored metadata.

    Returns the CallbackHandler (pass it to chain.invoke via config["callbacks"]),
    or None if Langfuse is not configured.
    """
    lf = _get_client()
    if lf is None:
        return None

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")

    try:


        # Store session metadata for use on subsequent requests
        _session_meta[session_id] = {"user_id": user_id, "service_id": service_id}

        # Enter propagate_attributes for THIS request
        langfuse.propagate_attributes(
            session_id=session_id,
            user_id=user_id,
            metadata={"service_id": service_id},
            tags=["agent2", service_id],
            trace_name="agent2-session",
        ).__enter__()

        # Build handler — public_key routes it to the right project
        handler = CallbackHandler(public_key=public_key if public_key else None)
        _handlers[session_id] = handler

        logger.info("[Langfuse] CallbackHandler created for session=%s", session_id)
        return handler

    except Exception as exc:
        logger.error("[Langfuse] create_callback_handler failed: %s", exc)
        return None


def get_callback_handler(session_id: str | None):
    """
    Retrieve the active CallbackHandler for a session and re-enter the
    propagate_attributes() context for this HTTP request.

    Each HTTP request (resume, edit) runs in a fresh async/thread context,
    so propagate_attributes() must be re-entered each time to ensure spans
    in this request inherit the correct userId and sessionId.
    """
    if not session_id:
        return None
    handler = _handlers.get(session_id)
    if handler is None:
        return None

    meta = _session_meta.get(session_id)
    if meta:
        try:
            public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
            langfuse.propagate_attributes(
                session_id=session_id,
                user_id=meta["user_id"],
                metadata={"service_id": meta["service_id"]},
                tags=["agent2", meta["service_id"]],
                trace_name="agent2-resume",
            ).__enter__()
        except Exception:
            pass

    return handler


def flush_handler(session_id: str | None) -> None:
    """Flush buffered events and clean up the session's handler and metadata."""
    if not session_id:
        return

    _handlers.pop(session_id, None)
    _session_meta.pop(session_id, None)

    # Flush all buffered OTel spans
    lf = _get_client()
    if lf:
        try:
            lf.flush()
            logger.info("[Langfuse] Flushed for session=%s", session_id)
        except Exception as exc:
            logger.error("[Langfuse] flush failed: %s", exc)


