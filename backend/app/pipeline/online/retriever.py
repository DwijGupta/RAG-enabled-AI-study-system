import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.core.embeddings import embedding_service
from app.core.vector_db import vector_store
from app.core.graph_db import graph_store
from app.pipeline.offline.indexer import bm25_engine

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Step 5: Hybrid multi-source retriever combining:
    - Dense semantic search (BGE-M3 via Qdrant)
    - Sparse BM25 keyword search
    - Concept graph prerequisite context
    """
    async def retrieve(
        self,
        query: str,
        target_concepts: List[str],
        weak_concept: Optional[str] = None,
        top_k_per_source: int = 8
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Executes dense, sparse, and graph retrieval in parallel.
        """
        # Formulate query enriched with weak prerequisite if diagnosed
        retrieval_query = query
        if weak_concept:
            retrieval_query = f"{query} foundational concept: {weak_concept}"

        # 1. Dense BGE-M3 Retrieval Task
        async def fetch_dense():
            query_vec = embedding_service.embed_query(retrieval_query)
            qdrant_results = vector_store.search_chunks(query_vector=query_vec, limit=top_k_per_source)
            dense_candidates = []
            for r in qdrant_results:
                payload = r.get("payload", {})
                dense_candidates.append({
                    "id": payload.get("chunk_id", r["id"]),
                    "doc_id": payload.get("doc_id", ""),
                    "doc_title": payload.get("doc_title", "Document"),
                    "page_number": payload.get("page_number", 1),
                    "section_title": payload.get("section_title", ""),
                    "content": payload.get("content", ""),
                    "contextual_line": payload.get("contextual_line", ""),
                    "difficulty_score": payload.get("difficulty_score", 0.5),
                    "score": r["score"],
                    "source": "dense_bge_m3"
                })
            return dense_candidates

        # 2. Sparse BM25 Retrieval Task
        def fetch_sparse():
            bm25_results = bm25_engine.search(retrieval_query, top_k=top_k_per_source)
            sparse_candidates = []
            for r in bm25_results:
                sparse_candidates.append({
                    "id": r.get("id", ""),
                    "doc_id": r.get("doc_id", ""),
                    "doc_title": r.get("doc_title", "Document"),
                    "page_number": r.get("page_number", 1),
                    "section_title": r.get("section_title", ""),
                    "content": r.get("content", ""),
                    "contextual_line": r.get("contextual_line", ""),
                    "difficulty_score": r.get("difficulty_score", 0.5),
                    "score": r.get("score", 1.0),
                    "source": "sparse_bm25"
                })
            return sparse_candidates

        # 3. Deterministic GraphRAG Community Vector Retrieval & Chunk Resolution
        def fetch_graph_communities(query_vec: List[float]):
            comm_results = graph_store.search_community_summaries(query_vector=query_vec, top_k=5)
            graph_chunk_candidates = []
            seen_chunk_ids = set()

            for rank, comm in enumerate(comm_results):
                cids = comm.get("source_chunk_ids", [])
                if not cids:
                    continue

                # Unroll chunks mapped to this community
                resolved_chunks = bm25_engine.get_chunks_by_ids(cids)
                if not resolved_chunks and hasattr(vector_store, "get_chunks_by_ids"):
                    q_chunks = vector_store.get_chunks_by_ids(cids)
                    for qc in q_chunks:
                        pl = qc.get("payload", {})
                        resolved_chunks.append({
                            "id": qc.get("id"),
                            "doc_id": pl.get("doc_id", ""),
                            "doc_title": pl.get("doc_title", "Document"),
                            "page_number": pl.get("page_number", 1),
                            "section_title": pl.get("section_title", ""),
                            "content": pl.get("content", ""),
                            "contextual_line": pl.get("contextual_line", ""),
                            "difficulty_score": pl.get("difficulty_score", 0.5)
                        })

                for ch in resolved_chunks:
                    cid = ch.get("id") or ch.get("chunk_id")
                    if cid and cid not in seen_chunk_ids:
                        seen_chunk_ids.add(cid)
                        ch_entry = ch.copy()
                        ch_entry["id"] = cid
                        ch_entry["source"] = "graph_community"
                        ch_entry["score"] = float(comm.get("score", 0.5))
                        ch_entry["community_title"] = comm.get("title", "")
                        ch_entry["community_summary"] = comm.get("summary", "")
                        graph_chunk_candidates.append(ch_entry)

            return comm_results, graph_chunk_candidates

        # 4. Concept Graph Context (Prerequisites & Misconceptions)
        def fetch_graph_context():
            graph_items = []
            concepts_to_check = set(target_concepts)
            if weak_concept:
                concepts_to_check.add(weak_concept)

            for c_name in concepts_to_check:
                prereqs = graph_store.get_prerequisites(c_name)
                misconceptions = graph_store.get_misconceptions(c_name)
                node_data = graph_store.nx_graph.nodes.get(c_name, {})
                if node_data:
                    graph_items.append({
                        "id": f"graph_{c_name}",
                        "concept": c_name,
                        "description": node_data.get("description", ""),
                        "difficulty": node_data.get("difficulty", 0.5),
                        "prerequisites": prereqs,
                        "misconceptions": misconceptions,
                        "source": "concept_graph"
                    })
            return graph_items

        # Precompute query vector once for both dense chunk and graph community searches
        q_vec = embedding_service.embed_query(retrieval_query)

        async def fetch_dense_task():
            qdrant_results = vector_store.search_chunks(query_vector=q_vec, limit=top_k_per_source)
            dense_candidates = []
            for r in qdrant_results:
                payload = r.get("payload", {})
                dense_candidates.append({
                    "id": payload.get("chunk_id", r["id"]),
                    "doc_id": payload.get("doc_id", ""),
                    "doc_title": payload.get("doc_title", "Document"),
                    "page_number": payload.get("page_number", 1),
                    "section_title": payload.get("section_title", ""),
                    "content": payload.get("content", ""),
                    "contextual_line": payload.get("contextual_line", ""),
                    "difficulty_score": payload.get("difficulty_score", 0.5),
                    "score": r["score"],
                    "source": "dense_bge_m3"
                })
            return dense_candidates

        dense_res, sparse_res, (top_communities, graph_chunk_res), graph_res = await asyncio.gather(
            fetch_dense_task(),
            asyncio.to_thread(fetch_sparse),
            asyncio.to_thread(fetch_graph_communities, q_vec),
            asyncio.to_thread(fetch_graph_context)
        )

        return {
            "dense": dense_res,
            "sparse": sparse_res,
            "graph_chunks": graph_chunk_res,
            "community_summaries": top_communities,
            "graph": graph_res
        }

hybrid_retriever = HybridRetriever()
