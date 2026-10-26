import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import AsyncSessionLocal, init_db
from app.pipeline.offline.indexer import offline_indexer
from app.pipeline.online.retriever import hybrid_retriever
from app.core.reranker import zpd_reranker
from app.core.graph_db import graph_store

SAMPLE_TEXT = """
# Lecture: Attention Mechanisms and Transformer Ingestion

## 1. Multi-Vector Representations
In modern retrieval systems, we pair dense vector embeddings (which capture deep semantic nuance) with sparse representations like BM25 or SPLADE (which preserve exact serial codes, keyword tokens, and identifiers). When queries contain specific technical acronyms like BLEU, ROUGE-L, or BGE-M3, sparse representations guarantee exact token hits that dense embeddings might smooth over.

## 2. Graph Communities in Educational Curricula
Rather than running dynamic Cypher generation at inference time, knowledge graphs organize domain concepts into topological communities using Louvain clustering. Concepts such as Query-Key-Value projection, Scaled Dot-Product, and Multi-Head Attention naturally cluster together. Pre-computed community summaries provide macro-level context for complex queries like "Explain how attention scales across representations."

## 3. Shared Chunk ID Alignment and RRF
Every entity in the knowledge graph maintains a pointer to its originating source_chunk_ids. When both unstructured vector chunks and graph community summaries are retrieved, Reciprocal Rank Fusion (RRF) scores each candidate purely based on its positional ranks:
RRF_Score(d) = sum(1 / (60 + rank_m(d)))
This mathematically unifies the semantic vector hits, keyword sparse hits, and structural graph context into a single ranked pool.

## 4. Late-Interaction Cross-Encoder Reranking
Finally, passing the fused candidates through a token-level Cross-Encoder compresses the context window. Only the highest-signal chunks and community summaries reach the generation LLM, minimizing noise and hallucination.
"""

async def verify_ingestion_and_retrieval():
    print("=" * 60)
    print("DEMONSTRATION: ENHANCED EMBEDDING INGESTION & ZERO-AGENT RETRIEVAL")
    print("=" * 60)
    await init_db()

    async with AsyncSessionLocal() as db:
        print("\n[Step 1] Ingesting educational text through Enhanced Offline Indexer...")
        ingest_res = await offline_indexer.index_source(
            file_path_or_content=SAMPLE_TEXT,
            title="Advanced Attention & GraphRAG Retrieval",
            source_type="note",
            db=db,
            original_filename="attention_graphrag.md"
        )
        print(f"-> Ingestion complete:")
        print(f"   - Chunks generated: {ingest_res['chunks']}")
        print(f"   - Concepts extracted: {ingest_res['concepts_extracted']}")
        print(f"   - Communities detected & summarized: {ingest_res['communities_created']}")

        print("\n[Step 2] Testing Deterministic Vector Search on Community Summaries...")
        test_query = "How does RRF merge sparse-dense embeddings with graph communities?"
        dense_q = [0.0] * 384
        from app.core.embeddings import embedding_service
        dense_q = embedding_service.embed_query(test_query)
        comm_hits = graph_store.search_community_summaries(dense_q, top_k=2)
        print(f"-> Found {len(comm_hits)} matching communities:")
        for ch in comm_hits:
            print(f"   * [{ch['title']}] (Score: {ch['score']:.4f})")
            print(f"     Summary: {ch['summary'][:120]}...")
            print(f"     Linked Chunks: {len(ch.get('source_chunk_ids', []))} chunks")

        print("\n[Step 3] Parallel 3-Stream Retrieval (Dense + Sparse + Graph Unrolled)...")
        ret_res = await hybrid_retriever.retrieve(
            query=test_query,
            target_concepts=["Multi-Vector Representations"]
        )
        print(f"-> Stream 1 (Dense Vector BGE-M3): {len(ret_res['dense'])} chunks")
        print(f"-> Stream 2 (Sparse Lexical BM25):  {len(ret_res['sparse'])} chunks")
        print(f"-> Stream 3 (Graph Community Unrolled): {len(ret_res['graph_chunks'])} chunks")

        print("\n[Step 4] Mathematical Reciprocal Rank Fusion (k=60)...")
        fused = zpd_reranker.reciprocal_rank_fusion([
            ret_res["dense"],
            ret_res["sparse"],
            ret_res["graph_chunks"]
        ], k=60)
        print(f"-> Fused pool contains {len(fused)} unified candidates:")
        for i, c in enumerate(fused[:5]):
            print(f"   {i+1}. [{c['id'][:8]}] RRF={c['rrf_score']:.6f} | Src={c.get('source')} | Title={c.get('section_title')}")

        print("\n[Step 5] Late Interaction Cross-Encoder + ZPD Difficulty Filter...")
        reranked = zpd_reranker.rerank_and_filter(
            query=test_query,
            candidates=fused,
            learner_mastery=0.6,
            top_k=3
        )
        print(f"-> Final Filtered Context for LLM (Top {len(reranked)} Chunks):")
        for i, rc in enumerate(reranked):
            print(f"   {i+1}. [{rc.get('section_title')}] (Final Score: {rc.get('final_zpd_score'):.4f}, NormRel: {rc.get('norm_relevance'):.4f})")
            print(f"      Snippet: {rc.get('content', '')[:100]}...")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(verify_ingestion_and_retrieval())
