"""
LLM-based input classifier — slow path.

Called only when the fast path cannot resolve the user's input.
Uses OpenAI GPT via langchain-openai.
Falls back to a heuristic if OPENAI_API_KEY is not set.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent.interpreter.prompts import CLASSIFY_PROMPT
from agent.interpreter.typo_hints import get_typo_hints
from agent.tracing import get_callback_handler, get_langfuse_prompt
from agent.llm.provider import get_llm as _get_llm
from langchain_core.prompts import ChatPromptTemplate
import re
def _build_chain(lf_prompt=None):
    """
    Build a prompt | llm chain for classification.

    If a Langfuse prompt object is supplied, compile it into a LangChain
    ChatPromptTemplate so the chain stays identical but prompt versions
    are tracked in Langfuse Prompt Management.
    """
    llm = _get_llm()

    if lf_prompt is not None:
        try:
            

            lc_raw = lf_prompt.get_langchain_prompt()

            # Langfuse v4 returns a list of (role, content) tuples — 
            # exactly the format ChatPromptTemplate.from_messages() expects
            if isinstance(lc_raw, list):
                lc_prompt = ChatPromptTemplate.from_messages(lc_raw)
            else:
                lc_prompt = lc_raw  # already a ChatPromptTemplate

            return lc_prompt | llm
        except Exception:
            pass  # Fall back to local prompt below

    return CLASSIFY_PROMPT | llm


def _validate_llm_output(
    output: dict,
    options: list[str],
    completed_fields: list[str],
) -> dict:
    """Sanitise / reject bad LLM output."""
    action = output.get("action")
    valid_actions = {"answer", "help", "edit", "preview", "cancel", "unclear"}

    if action not in valid_actions:
        return {"action": "unclear", "message": "LLM returned invalid action."}

    if action == "answer" and output.get("value") is None:
        return {"action": "unclear", "message": "LLM returned answer with no value."}

    if action == "edit":
        field = output.get("field")
        if field not in completed_fields:
            return {
                "action": "unclear",
                "message": f"Cannot edit '{field}' — not yet completed.",
            }

    return output


def _fallback_heuristic(
    raw_input: str,
    options: list[str],
    completed_fields: list[str] | None = None,
) -> dict:
    """
    Cheap heuristic used when no LLM API key is available.
    Covers basic fuzzy matching so the demo still works without tokens.
    """
    raw_lower = raw_input.strip().lower()
    completed_fields = completed_fields or []

    # Try fuzzy startswith
    for opt in options:
        if opt.lower().startswith(raw_lower):
            return {"action": "answer", "value": opt}

    # Try option contained in input
    for opt in options:
        if opt.lower() in raw_lower:
            return {"action": "answer", "value": opt}

    # Detect help-like phrasing
    help_signals = ["what is", "what does", "explain", "tell me about", "meaning"]
    if any(s in raw_lower for s in help_signals):
        return {"action": "help", "field": None}

    # Detect edit-like phrasing
    
    edit_match = re.match(
        r"(?:change|update|edit)\s+([\w_]+)(?:\s+to\s+(.+))?",
        raw_lower,
    )
    if edit_match:
        target = edit_match.group(1)
        new_val = edit_match.group(2).strip() if edit_match.group(2) else None
        matched_field = None
        for cf in completed_fields:
            if cf.lower() == target:
                matched_field = cf
                break
        if not matched_field:
            for cf in completed_fields:
                if target in cf.lower() or target.replace("_", "") in cf.lower().replace("_", ""):
                    matched_field = cf
                    break
        if matched_field:
            return {"action": "edit", "field": matched_field, "value": new_val}
        return {
            "action": "unclear",
            "message": f"Cannot edit '{target}'. Editable fields: {completed_fields}",
        }

    return {"action": "unclear", "message": f"Could not understand: {raw_input}"}


def llm_classify_input(
    raw_input: str,
    current_field: str,
    field_meta: dict,
    options: list[str],
    completed_fields: list[str],
    values: dict[str, Any],
    session_id: str | None = None,
) -> dict:
    """
    Classify user input using OpenAI GPT via LangChain.

    If OPENAI_API_KEY is not set, falls back to a heuristic so the
    demo works without burning tokens.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-your"):
        return _fallback_heuristic(raw_input, options, completed_fields)

    # ── Try to fetch prompt from Langfuse Prompt Management ──
    lf_prompt = get_langfuse_prompt("classify-input")

    invoke_vars = {
        "current_field": current_field,
        "field_type": field_meta.get("type", "text"),
        "prompt": field_meta.get("prompt", current_field),
        "options": json.dumps(options),
        "completed_fields": json.dumps(completed_fields),
        "values": json.dumps(
            {k: v for k, v in values.items() if k in completed_fields}
        ),
        "user_input": raw_input,
    }

    # ── Pass Langfuse CallbackHandler for automatic LLM span tracing ──
    invoke_config: dict = {}
    handler = get_callback_handler(session_id)
    if handler is not None:
        invoke_config["config"] = {"callbacks": [handler]}

    try:
        chain = _build_chain(lf_prompt)

        # ── Inject typo hints only at LLM invocation time ──
        hints = get_typo_hints(current_field, raw_input)
        if hints:
            hints_lines = "\n".join(f'  "{wrong}" -> "{correct}"' for wrong, correct in hints.items())
            invoke_vars["typo_hints_block"] = (
                f"\nCommon typos/aliases for this field (wrong -> correct):\n{hints_lines}\n"
                "Use these to correct the user's input before classifying.\n"
            )
        else:
            invoke_vars["typo_hints_block"] = ""

        result = chain.invoke(invoke_vars, **invoke_config)

        text = result.content.strip()

        # Strip markdown fences if the model wraps the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(text)
        return _validate_llm_output(parsed, options, completed_fields)

    except Exception as exc:
        return {
            "action": "unclear",
            "message": f"LLM classification failed: {exc}",
        }
