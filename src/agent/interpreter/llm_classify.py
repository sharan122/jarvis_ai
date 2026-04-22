"""
LLM-based input classifier — slow path.

Called only when the fast path cannot resolve the user's input.
Uses the LLM configured by provider.py (Azure OpenAI or standard OpenAI).
The prompt is fetched from Langfuse Prompt Management via PromptService;
if Langfuse is unreachable the local fallback in prompts.py is used instead.
Falls back to a heuristic classifier when no API key is available.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from agent.interpreter.prompts import CLASSIFY_PROMPT
from agent.interpreter.typo_hints import get_typo_hints
from agent.llm.provider import get_llm
from agent.prompt_service import prompt_service
from agent.tracing import get_callback_handler

logger = logging.getLogger(__name__)


# ── Chain builder ─────────────────────────────────────────────────────────────

def _build_chain(lf_prompt=None):
    """
    Return a prompt | LLM chain, preferring the Langfuse-managed prompt.

    If *lf_prompt* is supplied it is compiled into a LangChain
    ChatPromptTemplate so that the Langfuse trace records the exact prompt
    version used.  The ``langfuse_prompt`` is attached to the template via
    ``.with_config(metadata=...)`` — the SDK-documented way to link generations
    to a specific prompt version for ALL labels (not just 'production').
    Falls back to the local CLASSIFY_PROMPT constant.
    """
    llm = get_llm()

    if lf_prompt is not None:
        try:
            lc_raw = lf_prompt.get_langchain_prompt()

            if isinstance(lc_raw, list):
                # Chat prompt — expected type; preserves system + human structure.
                lc_prompt = ChatPromptTemplate.from_messages(lc_raw)
            elif isinstance(lc_raw, str):
                # Text prompt — Chat type is preferred; wrap as system message.
                logger.warning(
                    "[llm_classify] Prompt '%s' is Text type; Chat type is preferred. "
                    "Wrapping as system message.",
                    getattr(lf_prompt, "name", "?"),
                )
                lc_prompt = ChatPromptTemplate.from_messages([("system", lc_raw)])
            else:
                lc_prompt = lc_raw

            # Attach langfuse_prompt to the TEMPLATE (not only the invoke config).
            # This is the correct Langfuse-documented method for linking a
            # generation to a prompt version — works with any label, not just
            # 'production'.
            lc_prompt = lc_prompt.with_config(
                {"metadata": {"langfuse_prompt": lf_prompt}}
            )

            return lc_prompt | llm

        except Exception as exc:
            logger.warning(
                "[llm_classify] Langfuse prompt unusable (%s); using local fallback.", exc
            )

    return CLASSIFY_PROMPT | llm


# ── Output validation ─────────────────────────────────────────────────────────

def _validate_llm_output(
    output: dict,
    options: list[str],
    completed_fields: list[str],
) -> dict:
    """Reject structurally invalid LLM responses and normalise edge cases."""
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


# ── Heuristic fallback ────────────────────────────────────────────────────────

def _fallback_heuristic(
    raw_input: str,
    options: list[str],
    completed_fields: list[str] | None = None,
) -> dict:
    """
    Simple rule-based classifier used when no LLM API key is available.

    Covers basic fuzzy matching so the bot still works in dev without tokens.
    """
    raw_lower = raw_input.strip().lower()
    completed_fields = completed_fields or []

    for opt in options:
        if opt.lower().startswith(raw_lower):
            return {"action": "answer", "value": opt}

    for opt in options:
        if opt.lower() in raw_lower:
            return {"action": "answer", "value": opt}

    help_signals = ["what is", "what does", "explain", "tell me about", "meaning"]
    if any(s in raw_lower for s in help_signals):
        return {"action": "help", "field": None}

    edit_match = re.match(
        r"(?:change|update|edit)\s+([\w_]+)(?:\s+to\s+(.+))?",
        raw_lower,
    )
    if edit_match:
        target = edit_match.group(1)
        new_val = edit_match.group(2).strip() if edit_match.group(2) else None
        matched_field = next(
            (cf for cf in completed_fields if cf.lower() == target),
            next(
                (
                    cf for cf in completed_fields
                    if target in cf.lower()
                    or target.replace("_", "") in cf.lower().replace("_", "")
                ),
                None,
            ),
        )
        if matched_field:
            return {"action": "edit", "field": matched_field, "value": new_val}
        return {
            "action": "unclear",
            "message": f"Cannot edit '{target}'. Editable fields: {completed_fields}",
        }

    return {"action": "unclear", "message": f"Could not understand: {raw_input}"}


# ── Public classifier ─────────────────────────────────────────────────────────

def llm_classify_input(
    raw_input: str,
    current_field: str,
    field_meta: dict,
    options: list[str],
    completed_fields: list[str],
    values: dict[str, Any],
    session_id: str | None = None,
    service_id: str = "aws_ec2",
) -> dict:
    """
    Classify user input using the configured LLM (Azure OpenAI or OpenAI).

    1. Resolves the Langfuse prompt name from CLASSIFY_INPUT_PROMPT env var.
    2. Fetches that prompt from Langfuse via PromptService (cached 60 s).
    3. Injects typo hints at invocation time to keep the stored prompt lean.
    4. Attaches the Langfuse CallbackHandler so every call is traced.
    5. Falls back to a heuristic when no API key is configured.
    """
    provider = os.environ.get("LLM_PROVIDER", "azure").lower()
    api_key = (
        os.environ.get("DEV_OPENAI_API_KEY", "")
        if provider == "openai"
        else os.environ.get("OPENAI_API_KEY", "")
    )

    if not api_key or api_key.startswith("sk-your"):
        return _fallback_heuristic(raw_input, options, completed_fields)

    # Prompt name is configured via env var — no code change needed to rename.
    prompt_name = os.environ.get("CLASSIFY_INPUT_PROMPT", "classify-input")
    # PromptService uses get_client() — the same global SDK singleton as the
    # CallbackHandler — so the returned lf_prompt object is correctly linked
    # to the active trace for ANY label (not just "production").
    lf_prompt = prompt_service.get_prompt(prompt_name)

    invoke_vars: dict = {
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

    # Typo hints are injected at call-time, not stored in the prompt template,
    # so the Langfuse admin sees a clean, field-agnostic prompt in the UI.
    hints = get_typo_hints(current_field, raw_input, service_id=service_id)
    if hints:
        hint_lines = "\n".join(
            f'  "{wrong}" -> "{correct}"' for wrong, correct in hints.items()
        )
        invoke_vars["typo_hints_block"] = (
            f"\nCommon typos/aliases for this field (wrong -> correct):\n{hint_lines}\n"
            "Use these to correct the user's input before classifying.\n"
        )
    else:
        invoke_vars["typo_hints_block"] = ""

    invoke_config: dict = {}
    handler = get_callback_handler(session_id)

    # Build the invocation config.
    # langfuse_prompt in metadata is the Langfuse-documented API for linking a
    # generation to a specific prompt version when using LangChain CallbackHandler.
    # This is what populates Prompt → Metrics and Traces → Prompt Name.
    config_dict: dict = {}
    if handler is not None:
        config_dict["callbacks"] = [handler]
    if lf_prompt is not None:
        config_dict["metadata"] = {"langfuse_prompt": lf_prompt}
    if config_dict:
        invoke_config["config"] = config_dict

    try:
        chain = _build_chain(lf_prompt)
        result = chain.invoke(invoke_vars, **invoke_config)

        # Flush Langfuse spans synchronously so the trace is exported before
        # the FastAPI response is returned. Without this, async OTel export
        # races against the HTTP response and traces get silently dropped.
        if handler is not None:
            try:
                handler.flush()
            except Exception as flush_exc:
                logger.debug("[llm_classify] Langfuse flush warning: %s", flush_exc)

        text = result.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(text)
        return _validate_llm_output(parsed, options, completed_fields)

    except Exception as exc:
        return {
            "action": "unclear",
            "message": f"LLM classification failed: {exc}",
        }
