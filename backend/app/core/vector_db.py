import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.core.config import settings

logger = logging.getLogger(__name__)

# BGE-small dense dimension is 384
VECTOR_DIMENSION = 384

class VectorStore:
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self._init_qdrant()

    def _init_qdrant(self):
        try:
            if settings.QDRANT_URL:
                self.client = QdrantClient(url=settings.QDRANT_URL)
                logger.info("Connected to Qdrant server at %s", settings.QDRANT_URL)
            else:
                os.makedirs(settings.QDRANT_PATH, exist_ok=True)
                self.client = QdrantClient(path=settings.QDRANT_PATH)
                logger.info("Initialized local embedded Qdrant storage at %s", settings.QDRANT_PATH)
            
            self._ensure_collections()
        except Exception as e:
            logger.error("Failed to initialize Qdrant: %s. Using memory fallback.", str(e))
            self.client = QdrantClient(location=":memory:")
            self._ensure_collections()

    def _ensure_collections(self):
        if not self.client:
            return
        
        collections = [c.name for c in self.client.get_collections().collections]
        
        # 1. Knowledge Base Chunks Collection
        if settings.QDRANT_CHUNK_COLLECTION not in collections:
            self.client.create_collection(
                collection_name=settings.QDRANT_CHUNK_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info("Created Qdrant collection: %s", settings.QDRANT_CHUNK_COLLECTION)

        # 2. Learner Episodic Traces Collection
        if settings.QDRANT_TRACE_COLLECTION not in collections:
            self.client.create_collection(
                collection_name=settings.QDRANT_TRACE_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info("Created Qdrant collection: %s", settings.QDRANT_TRACE_COLLECTION)

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        chunks: list of dicts with:
        id: str (UUID)
        vector: list[float]
        payload: {chunk_id, doc_id, doc_title, page_number, content, section, difficulty, concepts}
        """
        if not self.client or not chunks:
            return

        points = [
            qmodels.PointStruct(
                id=c["id"],
                vector=c["vector"],
                payload=c["payload"]
            )
            for c in chunks
        ]

        self.client.upsert(
            collection_name=settings.QDRANT_CHUNK_COLLECTION,
            points=points
        )

    def delete_document_chunks(self, doc_id: str):
        if not self.client:
            return
        try:
            self.client.delete(
                collection_name=settings.QDRANT_CHUNK_COLLECTION,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="doc_id",
                                match=qmodels.MatchValue(value=doc_id)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            logger.warning("Failed to delete chunks for doc_id %s from Qdrant: %s", doc_id, str(e))


    def search_chunks(self, query_vector: List[float], limit: int = 10, concept_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        query_filter = None
        if concept_filter:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="concepts",
                        match=qmodels.MatchValue(value=concept_filter)
                    )
                ]
            )

        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=settings.QDRANT_CHUNK_COLLECTION,
                query=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            results = res.points
        else:
            results = self.client.search(
                collection_name=settings.QDRANT_CHUNK_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )

        return [
            {
                "id": str(r.id),
                "score": float(r.score),
                "payload": r.payload
            }
            for r in results
        ]

    def upsert_trace(self, trace_id: str, vector: List[float], payload: Dict[str, Any]):
        if not self.client:
            return

        self.client.upsert(
            collection_name=settings.QDRANT_TRACE_COLLECTION,
            points=[
                qmodels.PointStruct(
                    id=trace_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    def search_traces(self, user_id: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        user_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=user_id)
                )
            ]
        )

        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=settings.QDRANT_TRACE_COLLECTION,
                query=query_vector,
                limit=limit,
                query_filter=user_filter
            )
            results = res.points
        else:
            results = self.client.search(
                collection_name=settings.QDRANT_TRACE_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                query_filter=user_filter
            )

        return [
            {
                "id": str(r.id),
                "score": float(r.score),
                "payload": r.payload
            }
            for r in results
        ]

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves points/chunks from Qdrant by their UUIDs or string IDs.
        """
        if not self.client or not chunk_ids:
            return []
        try:
            points = self.client.retrieve(
                collection_name=settings.QDRANT_CHUNK_COLLECTION,
                ids=chunk_ids,
                with_payload=True,
                with_vectors=False
            )
            return [
                {
                    "id": str(p.id),
                    "payload": p.payload or {}
                }
                for p in points
            ]
        except Exception as e:
            logger.warning("Error retrieving chunks by ID from Qdrant: %s", str(e))
            return []

    def close(self):
        """Cleanly closes Qdrant client to release local file locks and avoid shutdown warnings."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

vector_store = VectorStore()

import atexit
atexit.register(vector_store.close)

