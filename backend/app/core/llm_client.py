import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Type
from pydantic import BaseModel
import httpx
from app.core.config import settings
from app.core.gemini_client import gemini_client

logger = logging.getLogger(__name__)

class UnifiedLLMClient:
    """
    Unified AI Brain for AI Study Buddy System.
    - Primary: Google Gemini API (gemini-2.5-flash via Google AI Studio).
    - Offline Fallback: Local Ollama (qwen2.5) if running offline/air-gapped.
    """
    def __init__(self):
        self.gemini = gemini_client
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.ollama_model = settings.OLLAMA_MODEL

    async def check_health(self) -> Dict[str, Any]:
        """Checks Gemini API first, then checks local offline Ollama."""
        # 1. Primary: Google Gemini
        gemini_health = await self.gemini.check_health()
        if gemini_health.get("status") in ["connected", "unconfigured"]:
            return {
                "active_brain": "Google Gemini (Google AI Studio)",
                "gemini": gemini_health
            }

        # 2. Offline Fallback: Local Ollama
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.ollama_base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    return {
                        "active_brain": "Local Ollama (Offline Fallback)",
                        "ollama": {"status": "connected", "models": models}
                    }
        except Exception:
            pass

        return {
            "active_brain": "Google Gemini (Google AI Studio)",
            "gemini": gemini_health
        }

    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        temperature: float = 0.2, 
        model: Optional[str] = None
    ) -> str:
        """Generates text via Google Gemini, falling back to local Ollama if offline."""
        if self.gemini._client:
            try:
                return await self.gemini.generate(prompt=prompt, system=system, temperature=temperature, model=model)
            except Exception as e:
                logger.warning("Gemini online request failed (%s). Falling back to local offline model.", str(e))

        # Offline fallback via Ollama
        try:
            payload = {
                "model": model or self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature}
            }
            if system:
                payload["system"] = system

            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=5.0)) as client:
                res = await client.post(f"{self.ollama_base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception as e:
            logger.error("Both Gemini and local offline Ollama failed: %s", str(e))
        
        raise RuntimeError("No LLM available. Please set GEMINI_API_KEY in backend/.env")

    async def chat_stream(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str] = None, 
        temperature: float = 0.4, 
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams chat tokens via Google Gemini."""
        if self.gemini._client:
            async for chunk in self.gemini.chat_stream(messages=messages, system=system, temperature=temperature, model=model):
                yield chunk
            return

        yield "Google Gemini API key required. Please configure GEMINI_API_KEY in backend/.env"

    async def structured_output(
        self, 
        prompt: str, 
        schema_class: Type[BaseModel], 
        system: Optional[str] = None, 
        temperature: float = 0.1
    ) -> BaseModel:
        """Generates structured JSON conforming to a Pydantic schema using Gemini."""
        if self.gemini._client:
            return await self.gemini.structured_output(prompt=prompt, schema_class=schema_class, system=system, temperature=temperature)

        raise RuntimeError("Gemini API key is required for structured output. Please set GEMINI_API_KEY in backend/.env")

llm_client = UnifiedLLMClient()
