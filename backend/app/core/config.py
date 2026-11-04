import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Learner-State-Aware RAG Educational Tutor"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: str = "./data/storage"
    DATA_DIR: str = "./data"

    # Google Gemini LLM & Brain (Google AI Studio)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Legacy / Optional Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/studybuddy.db"
    
    # Qdrant Vector Store
    QDRANT_PATH: str = "./data/qdrant_db"
    QDRANT_URL: str = ""
    QDRANT_CHUNK_COLLECTION: str = "kb_chunks"
    QDRANT_TRACE_COLLECTION: str = "learner_traces"

    # Neo4j Graph DB
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    NLI_MODEL: str = "cross-encoder/nli-deberta-v3-small"

    # Langfuse Observability & Telemetry (Container or Cloud)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3001"
    LANGFUSE_ENABLED: bool = True

    # API Security & Access Controls
    API_KEY_AUTH_ENABLED: bool = False
    API_SECRET_KEY: str = ""  # If non-empty or API_KEY_AUTH_ENABLED=True, enforces X-API-Key / Bearer auth
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"

    # API Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_EXPENSIVE_PER_MINUTE: int = 30

    # Payload & Upload Security
    MAX_UPLOAD_SIZE_MB: int = 50

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=[
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            ".env"
        ],
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "pages"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "uploads"), exist_ok=True)
