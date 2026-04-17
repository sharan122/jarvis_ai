"""LLM provider factory to isolate Azure vs standard OpenAI usage."""

import os
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
# Cached instance
_llm_instance = None

def get_llm() -> Any:
    """Lazy-init the ChatOpenAI model, supporting both Azure and standard OpenAI."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    # Check if we should use standard OpenAI instead of Azure
    llm_provider = os.environ.get("LLM_PROVIDER", "azure").lower()

    if llm_provider == "openai":
       
        
        kwargs = {
            "api_key": os.environ.get("DEV_OPENAI_API_KEY"),
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "temperature": 0,
            "max_tokens": 256,
            "base_url": "https://api.openai.com/v1"
        }
        
        _llm_instance = ChatOpenAI(**kwargs)
    else:
        # Default to Azure for production and backwards compatibility
        

        _llm_instance = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            azure_endpoint=os.environ.get("OPENAI_API_BASE"),
            openai_api_version=os.environ.get("OPENAI_API_VERSION"),
            azure_deployment=os.environ.get("CHAT_DEPLOYMENT"),
            temperature=0.1
        )

    return _llm_instance
