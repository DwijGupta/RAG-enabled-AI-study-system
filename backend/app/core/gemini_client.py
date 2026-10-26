import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Type, Union
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Google Gemini Client powering the LLM, Brain, and Audio Transcription (Whisper replacement).
    Supports Gemini 2.5 Flash / 1.5 Flash via Google AI Studio.
    """
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""
        self.default_model = settings.GEMINI_MODEL or "gemini-3.8-flash"
        self._client: Optional[genai.Client] = None
        self._init_client()

    def _init_client(self):
        if self.api_key and self.api_key.strip():
            try:
                self._client = genai.Client(api_key=self.api_key.strip())
                logger.info("Google Gemini Client initialized with model: %s", self.default_model)
            except Exception as e:
                logger.error("Failed to initialize Google Gemini Client: %s", str(e))
                self._client = None
        else:
            logger.warning("GEMINI_API_KEY is not set. Gemini features will operate in standby/fallback mode.")

    def reload_key(self, api_key: str):
        """Allows dynamically updating the API key without server restart."""
        self.api_key = api_key
        self._exhausted_models.clear()
        self._init_client()

    def _get_candidate_models(self) -> List[str]:
        # Active v1beta models in Google AI Studio
        models = ["gemini-3.5-flash-lite", "gemini-2.0-flash", self.default_model]
        seen = set()
        candidates = []
        for m in models:
            if m and m not in seen and m not in self._exhausted_models:
                seen.add(m)
                candidates.append(m)
        if not candidates:
            self._exhausted_models.clear()
            for m in models:
                if m and m not in seen:
                    seen.add(m)
                    candidates.append(m)
        return candidates

    async def check_health(self) -> Dict[str, Any]:
        """Checks if Gemini API is configured and responsive."""
        if not self._client:
            return {
                "status": "unconfigured",
                "message": "GEMINI_API_KEY is missing. Please set it in backend/.env to activate Gemini Brain.",
                "model": self.default_model
            }
        
        models_to_check = self._get_candidate_models()

        last_error = ""
        for m in models_to_check:
            try:
                def _probe(model_name=m):
                    return self._client.models.generate_content(
                        model=model_name,
                        contents="Reply with 'OK'",
                        config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.0)
                    )
                
                res = await asyncio.to_thread(_probe)
                return {
                    "status": "connected",
                    "provider": "Google AI Studio",
                    "model": m,
                    "response": res.text.strip() if res.text else "OK"
                }
            except Exception as e:
                last_error = str(e)
                logger.warning("Gemini health check attempt on %s failed: %s", m, str(e))

        return {
            "status": "error",
            "provider": "Google AI Studio",
            "error": last_error,
            "model": self.default_model
        }

    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        temperature: float = 0.2, 
        model: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/png"
    ) -> str:
        """Standard non-streaming generation with automatic fallback and multimodal image support."""
        target_model = model or self.default_model
        
        if not self._client:
            raise RuntimeError(
                "Gemini API key is not configured. Add GEMINI_API_KEY in backend/.env"
            )

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system if system else None
        )

        # Prepare multimodal contents
        if image_bytes:
            img_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            call_contents = [img_part, prompt]
        else:
            call_contents = prompt

        models_to_try = [target_model] + [m for m in self._get_candidate_models() if m != target_model]

        last_error = None
        for m in models_to_try:
            try:
                def _call(model_name=m):
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=call_contents,
                        config=config
                    )
                    return response.text or ""

                return await asyncio.to_thread(_call)
            except Exception as e:
                last_error = e
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    self._exhausted_models.add(m)
                logger.warning("Gemini generate call on %s failed: %s. Retrying fallback...", m, str(e))

        raise last_error or RuntimeError("Gemini generate failed on all models.")

    async def chat_stream(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str] = None, 
        temperature: float = 0.4, 
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Asynchronous streaming of chat completion chunks with automatic fallback."""
        target_model = model or self.default_model

        if not self._client:
            yield "Error: Google Gemini API key is missing. Please set GEMINI_API_KEY in backend/.env"
            return

        # Prepare contents
        formatted_contents = []
        for msg in messages:
            role = "user" if msg.get("role") in ["user", "student"] else "model"
            content = msg.get("content", "")
            formatted_contents.append(f"{role.upper()}: {content}")

        full_prompt = "\n\n".join(formatted_contents)

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system if system else None
        )

        models_to_try = [target_model] + [m for m in self._get_candidate_models() if m != target_model]

        # Run streaming in background queue
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _sync_stream():
            stream_started = False
            for m in models_to_try:
                try:
                    response = self._client.models.generate_content_stream(
                        model=m,
                        contents=full_prompt,
                        config=config
                    )
                    for chunk in response:
                        if chunk.text:
                            stream_started = True
                            loop.call_soon_threadsafe(queue.put_nowait, chunk.text)
                    if stream_started:
                        break
                except Exception as e:
                    logger.warning("Gemini stream failed on %s: %s", m, str(e))
                    if not stream_started and m != models_to_try[-1]:
                        continue
                    loop.call_soon_threadsafe(queue.put_nowait, f"\n[Gemini Error: {str(e)}]")
            loop.call_soon_threadsafe(queue.put_nowait, None)

        asyncio.create_task(asyncio.to_thread(_sync_stream))

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    async def structured_output(
        self, 
        prompt: str, 
        schema_class: Type[BaseModel], 
        system: Optional[str] = None, 
        temperature: float = 0.1
    ) -> BaseModel:
        """
        Forces Gemini to output valid JSON matching a Pydantic schema using
        native JSON mode and schema validation.
        """
        target_model = self.default_model

        if not self._client:
            raise RuntimeError(
                "Gemini API key is not configured. Add GEMINI_API_KEY in backend/.env"
            )

        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema_class,
            system_instruction=system if system else None
        )

        models_to_try = [target_model] + [m for m in self._get_candidate_models() if m != target_model]

        last_error = None
        for m in models_to_try:
            try:
                def _call(model_name=m):
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    raw_text = response.text or "{}"
                    data = json.loads(raw_text)
                    return schema_class.model_validate(data)

                return await asyncio.to_thread(_call)
            except Exception as e:
                last_error = e
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    self._exhausted_models.add(m)
                logger.warning("Gemini structured_output failed on %s: %s", m, str(e))

        raise last_error or RuntimeError("Gemini structured_output failed on all models.")

    async def transcribe_audio(
        self, 
        audio_path_or_bytes: Union[str, bytes], 
        mime_type: str = "audio/mp3",
        prompt: Optional[str] = None
    ) -> str:
        """
        Direct Whisper Replacement using Gemini Multimodal Audio understanding.
        Accepts MP3, WAV, M4A, OGG, AAC or MP4 audio/video tracks and produces
        high-fidelity structured transcriptions.
        """
        if not self._client:
            raise RuntimeError("Gemini API key is not configured. Add GEMINI_API_KEY in backend/.env")

        instruction = prompt or (
            "Transcribe this educational audio/lecture recording accurately and verbatim. "
            "Preserve technical terms, mathematical equations, and divide the lecture into clean "
            "sections with timestamps and topic headers."
        )

        def _transcribe():
            if isinstance(audio_path_or_bytes, str):
                # Upload file to Gemini Files API
                uploaded_file = self._client.files.upload(file=audio_path_or_bytes)
                response = self._client.models.generate_content(
                    model=self.default_model,
                    contents=[uploaded_file, instruction]
                )
                return response.text or ""
            else:
                # Direct inline bytes part
                audio_part = types.Part.from_bytes(
                    data=audio_path_or_bytes,
                    mime_type=mime_type
                )
                response = self._client.models.generate_content(
                    model=self.default_model,
                    contents=[audio_part, instruction]
                )
                return response.text or ""

        return await asyncio.to_thread(_transcribe)

    async def analyze_image(
        self,
        image_path_or_bytes: Union[str, bytes],
        mime_type: str = "image/png",
        prompt: Optional[str] = None
    ) -> str:
        """
        Multimodal image comprehension: extracts text, equations, and diagrams
        from textbook snapshots, lecture slides, handwriting, and whiteboard photos.
        """
        if not self._client:
            raise RuntimeError("Gemini API key is not configured. Add GEMINI_API_KEY in backend/.env")

        instruction = prompt or (
            "You are an academic document parser. Transcribe and extract all educational content from this image:\n"
            "1. Extract all text verbatim with clear markdown formatting.\n"
            "2. Convert any mathematical formulas or equations into standard LaTeX format enclosed in $$ or $.\n"
            "3. If there is a diagram, chart, flowchart, or architecture, describe its structure, labels, and relationships in detail.\n"
            "4. Provide a 1-sentence summary of the main concept explained."
        )

        models_to_try = self._get_candidate_models()

        # Prepare image bytes
        if isinstance(image_path_or_bytes, str):
            with open(image_path_or_bytes, "rb") as f:
                img_data = f.read()
        else:
            img_data = image_path_or_bytes

        image_part = types.Part.from_bytes(data=img_data, mime_type=mime_type)

        last_err = None
        for m in models_to_try:
            try:
                def _vision_call(model_name=m):
                    res = self._client.models.generate_content(
                        model=model_name,
                        contents=[image_part, instruction]
                    )
                    return res.text or ""

                return await asyncio.to_thread(_vision_call)
            except Exception as e:
                last_err = e
                logger.warning("Gemini analyze_image failed on %s: %s", m, str(e))

        raise last_err or RuntimeError("Gemini image analysis failed on all models.")

gemini_client = GeminiClient()
