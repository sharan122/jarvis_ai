"""
Hardcoded fallback prompt templates for the LLM interpreter.

These strings are used ONLY when Langfuse Prompt Management is
unreachable.  The canonical, admin-editable version of every prompt lives
in Langfuse under the same name and label (see prompt_service.py).

Langfuse prompt name : "classify-input"
Langfuse label       : controlled by PROMPT_LABEL env var (default: "production")
Langfuse variables   : current_field, field_type, prompt, options,
                       completed_fields, values, typo_hints_block, user_input
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

# ── System message ────────────────────────────────────────────────────────────

_SYSTEM = """\
You are a form-input interpreter for a cloud resource provisioning system.

The user is filling out a form one field at a time. Your job is to classify
what the user said into exactly one action.

You must return valid JSON with one of these action types:

1. answer — The user provided a value for the current field.
   {{"action": "answer", "value": "<extracted value>"}}

2. help — The user is asking for information about the current or another field.
   {{"action": "help", "field": "<field name>"}}

3. edit — The user wants to change a previously filled field.
   {{"action": "edit", "field": "<field name>", "value": "<new value or null>"}}

4. preview — The user wants to see what they have filled so far.
   {{"action": "preview"}}

5. cancel — The user wants to stop the form.
   {{"action": "cancel"}}

6. unclear — You cannot determine what the user meant.
   {{"action": "unclear", "message": "<brief explanation>"}}

Rules:
- For "answer", the value MUST be one of the valid options if options are provided.
  Map informal language to the closest option (e.g., "Ohio" → "us-east-2").
- For number fields like disk_size_gb (no options list): ALWAYS return a plain integer string.
  Convert any text the user enters — number words, units, keywords — into a digit
  (e.g., "twenty GB" → "20", "hundred" → "100", "min" → "20", "max" → "500",
  "50 gigabytes" → "50"). Valid disk sizes are between 20 and 500 GB (inclusive).
  Use the typo hints block for guidance. If the number is out of range, return
  action "unclear" with a message explaining the valid range.
- For "edit", the field must be one of the already-completed fields.
- Return ONLY the JSON object. No explanation. No markdown fences.\
"""

# ── Human / user message ──────────────────────────────────────────────────────

_HUMAN = """\
Current field: "{current_field}"
Field type: {field_type}
Field description: "{prompt}"
Valid options: {options}
Already completed fields: {completed_fields}
Current values: {values}
{typo_hints_block}
User said: "{user_input}"

Classify this input. Return JSON only.\
"""

# ── Assembled LangChain prompt (fallback only) ────────────────────────────────

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human", _HUMAN),
])
