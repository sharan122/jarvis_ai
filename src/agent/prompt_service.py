"""
Central Langfuse Prompt Management client.

Provides a singleton PromptService that fetches prompts from Langfuse,
caches them locally, and falls back to local hardcoded strings when
Langfuse is unreachable.  Every part of the codebase that needs a
prompt must use this service — it is the single source of truth.


Admin workflow (Langfuse UI):
  1. Prompts → New Prompt → type = Chat → name = "classify-input"
  2. Add System + Human messages with {{variable}} placeholders.
  3. Save with any label you like: "staging", "dev", "v2", …
     (You do NOT need to use "production".)
  4. Set PROMPT_LABEL=<your-label> in .env.
  5. The app picks up the new version within PROMPT_CACHE_TTL_SECONDS (default 60 s).
"""

from __future__ import annotations

import logging
import os
import time

import langfuse as langfuse_sdk

logger = logging.getLogger(__name__)


class PromptService:
    """Singleton wrapper around the Langfuse global client for prompt fetching."""

    _instance: PromptService | None = None

    def __new__(cls) -> PromptService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    # ── Initialisation ──────────────────────────────────────────────────────

    def _init(self) -> None:
        """Initialise cache config; the client is resolved lazily via get_client()."""
        self._cache: dict[str, dict] = {}
        self._label: str = os.environ.get("PROMPT_LABEL", "production")
        # How long (seconds) to serve a cached prompt before re-fetching.
        self._ttl: int = int(os.environ.get("PROMPT_CACHE_TTL_SECONDS", "60"))
        logger.info(
            "[PromptService] Initialised (label=%s, ttl=%ss).", self._label, self._ttl
        )

    def _get_client(self):
        """
        Return the global Langfuse SDK client (get_client()).

        This is the SAME singleton used by the LangChain CallbackHandler,
        which is required for prompt-metric linking to work with any label.
        Returns None when credentials are not configured.
        """
        try:
            client = langfuse_sdk.get_client()
            # get_client() returns a client even without credentials; check auth.
            if not os.environ.get("LANGFUSE_SECRET_KEY"):
                return None
            return client
        except Exception as exc:
            logger.warning("[PromptService] get_client() unavailable: %s", exc)
            return None

    # ── Public API ───────────────────────────────────────────────────────────

    def get_prompt(self, name: str, label: str | None = None):
        """
        Return a Langfuse prompt object for *name*, using the in-process cache.

        The label is resolved from (in priority order):
          1. The explicit ``label`` argument (if given)
          2. The ``PROMPT_LABEL`` environment variable (read live — no restart needed)
          3. The value captured at startup (default: "production")

        Cache TTL is controlled by PROMPT_CACHE_TTL_SECONDS (default 60 s).

        Falls back to ``None`` when Langfuse is unavailable; callers handle
        ``None`` gracefully by using the hardcoded local fallback prompt.
        """
        client = self._get_client()
        if client is None:
            return None


        resolved_label = label or os.environ.get("PROMPT_LABEL", self._label)
        cache_key = f"{name}:{resolved_label}"
        now = time.time()

        cached = self._cache.get(cache_key)
        if cached and (now - cached["time"]) < self._ttl:
            return cached["prompt"]

        try:
         
            prompt = client.get_prompt(name, label=resolved_label)
            self._cache[cache_key] = {"prompt": prompt, "time": now}
            logger.info(
                "[PromptService] Fetched '%s' label='%s' version=%s.",
                name,
                resolved_label,
                getattr(prompt, "version", "?"),
            )
            return prompt
        except Exception as exc:
            logger.warning(
                "[PromptService] get_prompt('%s', label='%s') failed: %s  "
                "— verify the prompt exists in Langfuse UI with this exact label.",
                name,
                resolved_label,
                exc,
            )
            return None

    def invalidate(self, name: str, label: str | None = None) -> None:
        """Remove a cached entry so the next call re-fetches from Langfuse."""
        resolved_label = label or os.environ.get("PROMPT_LABEL", self._label)
        self._cache.pop(f"{name}:{resolved_label}", None)
        logger.debug(
            "[PromptService] Cache invalidated for '%s' label='%s'.", name, resolved_label
        )

    def invalidate_all(self) -> None:
        """Clear the entire cache — useful after changing PROMPT_LABEL at runtime."""
        self._cache.clear()
        logger.info("[PromptService] Full cache cleared.")

    def is_ready(self) -> bool:
        """Return True when Langfuse credentials are configured."""
        return bool(os.environ.get("LANGFUSE_SECRET_KEY"))


# Module-level singleton — import and use this directly.
prompt_service = PromptService()
