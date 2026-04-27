"""
Agent 2 — LangGraph graph definition.

Wires all nodes, edges, and conditional routing, then compiles the app.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.nodes.ask_field import ask_field
from agent.nodes.bootstrap import bootstrap
from agent.nodes.confirm_preview import confirm_preview
from agent.nodes.finalize import finalize
from agent.nodes.handle_edit import handle_edit
from agent.nodes.handle_help import handle_help
from agent.nodes.handle_preview import handle_preview
from agent.nodes.interpret import interpret_input
from agent.nodes.post_action import post_action
from agent.nodes.validate_and_store import validate_and_store
from agent.state import Agent2State
from pathlib import Path
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.memory import MemorySaver

# ── Conditional router (pure function, no LLM) ──

def route_action(state: Agent2State) -> str:
    """Read interpreted_action and return the next node name."""
    action = state.get("interpreted_action")
    if action is None:
        return "unclear"

    action_type = action.get("action", "unclear")

    routing = {
        "answer":  "validate",
        "help":    "help",
        "edit":    "edit",
        "preview": "preview",
        "cancel":  "cancel",
        "unclear": "unclear",
    }
    return routing.get(action_type, "unclear")


# ── Build graph ──

def build_graph(checkpointer=None):
    """Construct and compile the Agent 2 LangGraph workflow."""

    builder = StateGraph(Agent2State)

    # ── Nodes ──
    builder.add_node("bootstrap",          bootstrap)
    builder.add_node("ask_field",          ask_field)
    builder.add_node("interpret",          interpret_input)
    builder.add_node("validate_and_store", validate_and_store)
    builder.add_node("handle_help",        handle_help)
    builder.add_node("handle_edit",        handle_edit)
    builder.add_node("handle_preview",     handle_preview)
    builder.add_node("post_action",        post_action)
    builder.add_node("confirm_preview",    confirm_preview)
    builder.add_node("finalize",           finalize)

    # ── Edges ──
    # START -> bootstrap (bootstrap uses Command to route to ask_field or finalize)
    builder.add_edge(START, "bootstrap")

    # ask_field -> interpret (always, after user resumes)
    builder.add_edge("ask_field", "interpret")

    # interpret -> conditional routing
    builder.add_conditional_edges(
        "interpret",
        route_action,
        {
            "validate": "validate_and_store",
            "help":     "handle_help",
            "edit":     "handle_edit",
            "preview":  "handle_preview",
            "unclear":  "ask_field",    # re-ask same question
            "cancel":   END,
        },
    )

    # All action branches converge at post_action
    builder.add_edge("validate_and_store", "post_action")
    builder.add_edge("handle_help",        "post_action")
    builder.add_edge("handle_edit",        "post_action")
    builder.add_edge("handle_preview",     "post_action")

    # post_action uses Command to route to ask_field or confirm_preview.
    # confirm_preview uses Command to route to finalize | handle_edit | ask_field | END.
    # finalize → END
    builder.add_edge("finalize", END)

    # ── Compile ──
    return builder.compile(checkpointer=checkpointer)


def get_default_app():
    """
    Build the graph with a persistent SQLite checkpointer.

    Sessions are stored in checkpoints.db (project root) so they survive
    server restarts.  Falls back to InMemorySaver only if the sqlite
    package is not installed.
    """

    try:


        # Resolve to project root  (src/agent/graph.py → ../../..)
        db_path = Path(__file__).resolve().parent.parent.parent / "checkpoints.db"

        # Keep the connection open for the lifetime of the process.
        # check_same_thread=False is required because FastAPI may invoke the
        # graph from multiple worker threads.
        # isolation_level=None enables autocommit so writes are immediately
        # flushed to disk without requiring explicit conn.commit() calls.
        conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            isolation_level=None,
        )
        checkpointer = SqliteSaver(conn)
    except Exception:
        # Fallback — no persistence across restarts
        try:
            
            checkpointer = InMemorySaver()
        except ImportError:
            checkpointer = MemorySaver()

    return build_graph(checkpointer=checkpointer)
