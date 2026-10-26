"""
Backward compatibility module.
Redirects legacy ollama_client imports to the new UnifiedLLMClient.
"""
from app.core.llm_client import llm_client as ollama_client, llm_client

__all__ = ["ollama_client", "llm_client"]
