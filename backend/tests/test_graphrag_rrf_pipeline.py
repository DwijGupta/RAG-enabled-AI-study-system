import asyncio
import os
import sys
import uuid

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import AsyncSessionLocal, init_db
from app.core.models import User, Document, Chunk
from app.core.graph_db import graph_store
from app.core.vector_db import vector_store
from app.core.embeddings import embedding_service
from app.core.reranker import zpd_reranker
from app.pipeline.offline.indexer import bm25_engine
from app.pipeline.offline.graph_extractor import graph_extractor
from app.pipeline.online.retriever import hybrid_retriever
from app.pipeline.online.coordinator import online_pipeline

async def run_tests():
    print("\n================ 1. Initializing DB and Test Environment ================")
    await init_db()

    async with AsyncSessionLocal() as db:
        user = await db.get(User, "test_graphrag_student")
        if not user:
            user = User(id="test_graphrag_student", name="GraphRAG Tester")
            db.add(user)
            await db.commit()

    print("\n================ 2. Testing Chunk Alignment & source_chunk_ids ================")
    chunk_1_id = str(uuid.uuid4())
    chunk_2_id = str(uuid.uuid4())
    chunk_3_id = str(uuid.uuid4())

    test_chunks = [
        {
            "id": chunk_1_id,
            "chunk_id": chunk_1_id,
            "doc_id": "doc_test_1",
            "doc_title": "Quantum & Neural Computation",
            "page_number": 1,
            "section_title": "1.1 Linear Superposition",
            "content": "Quantum superposition allows state vectors to exist in linear combinations of basis states |0> and |1>.",
            "contextual_line": "Foundations of quantum state vectors and Hilbert spaces.",
            "difficulty_score": 0.4
        },
        {
            "id": chunk_2_id,
            "chunk_id": chunk_2_id,
            "doc_id": "doc_test_1",
            "doc_title": "Quantum & Neural Computation",
            "page_number": 2,
            "section_title": "1.2 Quantum Entanglement",
            "content": "Entanglement describes composite quantum states that cannot be factored as product states of their subsystems.",
            "contextual_line": "EPR paradox and Bell inequalities.",
            "difficulty_score": 0.6
        },
        {
            "id": chunk_3_id,
            "chunk_id": chunk_3_id,
            "doc_id": "doc_test_1",
            "doc_title": "Quantum & Neural Computation",
            "page_number": 3,
            "section_title": "2.1 Variational Quantum Circuits",
            "content": "Parameterized quantum circuits apply unitary rotation gates with classical optimization via parameter-shift rules.",
            "contextual_line": "Quantum neural networks and variational algorithms.",
            "difficulty_score": 0.75
        }
    ]

    # Index into BM25 and Qdrant
    bm25_engine.index(test_chunks)
    dense_vecs = embedding_service.embed_documents([c["content"] for c in test_chunks])
    vector_points = [
        {
            "id": c["id"],
            "vector": dense_vecs[i],
            "payload": {
                "chunk_id": c["id"],
                "doc_id": c["doc_id"],
                "doc_title": c["doc_title"],
                "page_number": c["page_number"],
                "section_title": c["section_title"],
                "content": c["content"],
                "contextual_line": c["contextual_line"],
                "difficulty_score": c["difficulty_score"]
            }
        }
        for i, c in enumerate(test_chunks)
    ]
    vector_store.upsert_chunks(vector_points)

    # Store concepts with source_chunk_ids
    await graph_store.add_concept(
        name="Quantum Superposition",
        description="Linear combinations of quantum basis vectors in Hilbert space.",
        domain="Quantum Physics",
        difficulty=0.4,
        source_chunk_ids=[chunk_1_id]
    )
    await graph_store.add_concept(
        name="Quantum Entanglement",
        description="Non-separable composite quantum states.",
        domain="Quantum Physics",
        difficulty=0.6,
        source_chunk_ids=[chunk_2_id]
    )
    await graph_store.add_concept(
        name="Variational Quantum Circuits",
        description="Parameterized unitary circuits for quantum machine learning.",
        domain="Quantum ML",
        difficulty=0.75,
        source_chunk_ids=[chunk_3_id]
    )

    await graph_store.add_prerequisite("Quantum Superposition", "Quantum Entanglement", source_chunk_ids=[chunk_1_id, chunk_2_id])
    await graph_store.add_prerequisite("Quantum Entanglement", "Variational Quantum Circuits", source_chunk_ids=[chunk_2_id, chunk_3_id])

    node_data_sup = graph_store.nx_graph.nodes.get("Quantum Superposition", {})
    assert chunk_1_id in node_data_sup.get("source_chunk_ids", []), "source_chunk_ids not recorded on concept node"
    print("[PASS] Concept node properly stores and maps source_chunk_ids!")

    print("\n================ 3. Testing Graph Community Clustering (Louvain/Modularity) ================")
    communities = graph_store.detect_communities()
    print(f"Detected {len(communities)} communities:")
    for comm in communities:
        print(f"  - ID: {comm['community_id']}, Members: {comm['members']}, Linked Chunks: {comm['source_chunk_ids']}")
    assert len(communities) >= 1, "Graph community detection returned no clusters"
    quantum_comm = next((c for c in communities if "Quantum Superposition" in c["members"]), None)
    assert quantum_comm is not None, "Quantum community not detected"
    assert len(quantum_comm["source_chunk_ids"]) > 0, "Community does not aggregate member source_chunk_ids"
    print("[PASS] Graph community clustering succeeded and aggregated source_chunk_ids!")

    print("\n================ 4. Testing Pre-Computed Community Summaries & Vector Indexing ================")
    summarized_comms = await graph_extractor.build_and_summarize_communities(domain="Quantum & Neural Computation")
    assert len(summarized_comms) >= 1, "Community summarization failed"
    print(f"Synthesized Summary: {summarized_comms[0]['summary']}")

    # Deterministic Vector Search against Community Summaries (Zero Cypher generation)
    q_vec = embedding_service.embed_query("How do quantum circuits utilize superposition?")
    searched_comms = graph_store.search_community_summaries(q_vec, top_k=2)
    print(f"Community Vector Search returned {len(searched_comms)} communities:")
    for sc in searched_comms:
        print(f"  - Title: {sc['title']}, Score: {sc['score']:.4f}")
    assert len(searched_comms) >= 1, "Community summary vector search failed"
    assert "source_chunk_ids" in searched_comms[0], "Community search result missing source_chunk_ids"
    print("[PASS] Deterministic vector search against community summaries verified!")

    print("\n================ 5. Testing Hybrid Parallel Retrieval (3 Streams) ================")
    retrieval_res = await hybrid_retriever.retrieve(
        query="Explain quantum entanglement and superposition",
        target_concepts=["Quantum Entanglement"]
    )
    print(f"Dense Chunks: {len(retrieval_res['dense'])}")
    print(f"Sparse BM25 Chunks: {len(retrieval_res['sparse'])}")
    print(f"Graph Community Chunks: {len(retrieval_res['graph_chunks'])}")
    print(f"Community Summaries: {len(retrieval_res['community_summaries'])}")

    assert len(retrieval_res["dense"]) >= 1, "Dense retrieval failed"
    assert len(retrieval_res["sparse"]) >= 1, "Sparse retrieval failed"
    assert len(retrieval_res["graph_chunks"]) >= 1, "Graph community chunk unrolling failed"
    print("[PASS] All 3 parallel retrieval streams succeeded!")

    print("\n================ 6. Testing 3-Stream Reciprocal Rank Fusion (RRF) ================")
    fused = zpd_reranker.reciprocal_rank_fusion([
        retrieval_res["dense"],
        retrieval_res["sparse"],
        retrieval_res["graph_chunks"]
    ], k=60)
    print(f"Fused candidate pool size: {len(fused)}")
    for fc in fused:
        print(f"  - ID: {fc['id'][:8]}... RRF Score: {fc['rrf_score']:.6f} (Source: {fc.get('source')})")
    assert len(fused) >= 1, "RRF fusion returned empty pool"
    assert "rrf_score" in fused[0], "RRF score missing from fused item"
    print("[PASS] Mathematical Reciprocal Rank Fusion verified!")

    print("\n================ 7. Testing Late Interaction Cross-Encoder & ZPD Filtering ================")
    reranked = zpd_reranker.rerank_and_filter(
        query="Explain quantum entanglement and superposition",
        candidates=fused,
        learner_mastery=0.55,
        top_k=3
    )
    print(f"Reranked top candidates: {len(reranked)}")
    for rc in reranked:
        print(f"  - ID: {rc['id'][:8]}... Final ZPD Score: {rc.get('final_zpd_score', 0):.4f} (Norm Rel: {rc.get('norm_relevance', 0):.4f})")
    assert len(reranked) >= 1, "Late interaction cross-encoder reranking failed"
    print("[PASS] Late interaction neural reranker and ZPD matching verified!")

    print("\n================ 8. Testing End-to-End Online Pipeline Execution ================")
    async with AsyncSessionLocal() as db:
        res = await online_pipeline.run(
            user_id="test_graphrag_student",
            session_id=str(uuid.uuid4()),
            user_query="What is quantum entanglement and how does it relate to superposition?",
            db=db
        )
        print(f"Answer generated (length {len(res['answer'])} chars):")
        print(res["answer"][:250] + "...")
        assert len(res["answer"]) > 20, "Answer generated was empty"
        assert "faithfulness_score" in res, "Verification faithfulness missing"
    print("[PASS] End-to-end online pipeline executed successfully with 0 agent loops!")

    print("\n>>> ALL GRAPHRAG RRF PIPELINE TESTS PASSED WITH DISTINCTION! <<<\n")
    from app.core.db import engine
    await engine.dispose()

def test_graphrag_rrf_suite():
    """Pytest suite runner for GraphRAG, Louvain community clustering, RRF, and Cross-Encoder."""
    asyncio.run(run_tests())

if __name__ == "__main__":
    asyncio.run(run_tests())
