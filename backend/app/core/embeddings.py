import logging
from typing import List
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model = None
        self._init_model()

    def _init_model(self):
        try:
            from fastembed import TextEmbedding
            # BAAI/bge-small-en-v1.5: 384-dim ONNX model, ultra-fast and lightweight (67MB)
            self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            logger.info("Loaded FastEmbed BAAI/bge-small-en-v1.5 ONNX model.")
        except Exception as e:
            logger.warning("FastEmbed not loaded (%s). Attempting sentence-transformers.", str(e))
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
                logger.info("Loaded SentenceTransformer BAAI/bge-small-en-v1.5")
            except Exception as e2:
                logger.warning("Local embedding model fallback active (%s).", str(e2))
                self.model = None

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        if not texts:
            return []
        
        if self.model is not None:
            try:
                # FastEmbed returns a generator of numpy arrays
                if hasattr(self.model, "embed"):
                    embeddings = list(self.model.embed(texts, batch_size=batch_size))
                    return [emb.tolist() for emb in embeddings]
                # SentenceTransformer
                elif hasattr(self.model, "encode"):
                    embeddings = self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
                    return embeddings.tolist()
            except Exception as e:
                logger.error("Error generating embeddings: %s", str(e))

        # Deterministic 1024-dim fallback for testing/graceful degradation
        return [self._fallback_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        res = self.embed_documents([text])
        return res[0] if res else [0.0] * 384

    def _fallback_vector(self, text: str) -> List[float]:
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(384)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = EmbeddingService()
