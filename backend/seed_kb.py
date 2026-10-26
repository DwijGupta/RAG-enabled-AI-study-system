import asyncio
import os
import uuid
from app.core.db import AsyncSessionLocal, init_db
from app.core.models import Document, Chunk, Concept, PrerequisiteEdge, Misconception, ReviewCard, LearnerMastery, User
from app.core.graph_db import graph_store
from app.core.vector_db import vector_store
from app.core.embeddings import embedding_service
from app.pipeline.offline.indexer import bm25_engine

SAMPLE_CURRICULUM = [
    {
        "title": "Deep Learning & Neural Networks Fundamentals",
        "concepts": [
            {
                "name": "Vectors & Matrices",
                "description": "Multi-dimensional numeric arrays representing features and linear transformations.",
                "difficulty": 0.2,
                "domain": "Mathematics",
                "prerequisites": [],
                "misconceptions": []
            },
            {
                "name": "Dot Product & Projection",
                "description": "Algebraic operation multiplying matching components and summing them, quantifying alignment.",
                "difficulty": 0.35,
                "domain": "Mathematics",
                "prerequisites": ["Vectors & Matrices"],
                "misconceptions": [
                    {
                        "name": "Dot product yields a vector",
                        "description": "Believing dot product produces another vector rather than a scalar value.",
                        "refutation": "The dot product maps two vectors of equal dimension to a single real scalar number."
                    }
                ]
            },
            {
                "name": "Activation Functions",
                "description": "Non-linear mappings (ReLU, GELU, Sigmoid) enabling networks to approximate non-linear functions.",
                "difficulty": 0.45,
                "domain": "Deep Learning",
                "prerequisites": ["Vectors & Matrices"],
                "misconceptions": [
                    {
                        "name": "Linear networks can learn complex curves",
                        "description": "Believing stacking multiple linear layers without activation functions can model non-linear boundaries.",
                        "refutation": "The composition of linear functions is strictly linear; non-linear activation is mathematically required."
                    }
                ]
            },
            {
                "name": "Loss Functions & Gradient Descent",
                "description": "Quantifying prediction error and iteratively updating parameters along the negative gradient vector.",
                "difficulty": 0.55,
                "domain": "Optimization",
                "prerequisites": ["Dot Product & Projection"],
                "misconceptions": [
                    {
                        "name": "Learning rate should always be large for speed",
                        "description": "Assuming maximum learning rate speeds up convergence without instability.",
                        "refutation": "Excessive learning rate causes divergence and oscillation across loss landscape ravines."
                    }
                ]
            },
            {
                "name": "Backpropagation & Chain Rule",
                "description": "Systematic application of multivariable calculus chain rule to compute partial derivatives of loss with respect to all weights.",
                "difficulty": 0.70,
                "domain": "Deep Learning",
                "prerequisites": ["Activation Functions", "Loss Functions & Gradient Descent"],
                "misconceptions": [
                    {
                        "name": "Gradients update forward in time",
                        "description": "Confusing forward propagation of activations with backward error sensitivity propagation.",
                        "refutation": "Activations flow forward from input to output; error gradients flow in reverse from loss back to input weights."
                    }
                ]
            },
            {
                "name": "Self-Attention Mechanism",
                "description": "Dynamic pairwise token affinity computation using Query, Key, and Value projections normalized by softmax.",
                "difficulty": 0.85,
                "domain": "Transformers",
                "prerequisites": ["Backpropagation & Chain Rule", "Dot Product & Projection"],
                "misconceptions": [
                    {
                        "name": "Attention requires sequential recurrence",
                        "description": "Believing tokens must be fed one-by-one like RNNs rather than parallel matrix operations.",
                        "refutation": "Self-attention computes all token pairwise affinities simultaneously in parallel matrices."
                    }
                ]
            }
        ],
        "chunks": [
            {
                "page": 1,
                "section": "1.1 Linear Algebra Foundations",
                "context": "Introduces vector spaces and matrix notation for machine learning features.",
                "difficulty": 0.25,
                "content": "Vectors represent points or directions in n-dimensional space. In machine learning, an input feature vector x represents attributes of an example. When computing transformations, we represent linear maps using matrices. Multiplying a matrix W by a vector x produces a new vector representing rotated, scaled, or sheared coordinates."
            },
            {
                "page": 2,
                "section": "1.2 Dot Products and Vector Similarity",
                "context": "Explains geometric and algebraic properties of the dot product.",
                "difficulty": 0.35,
                "content": "The dot product of two vectors u and v equals the sum of element-wise products: u · v = sum(u_i * v_i). Geometrically, u · v = ||u|| ||v|| cos(theta). When two vectors are normalized to unit length, their dot product equals the cosine of the angle between them, providing the mathematical foundation for cosine similarity."
            },
            {
                "page": 3,
                "section": "2.1 Non-Linear Activation Functions",
                "context": "Explains why neural networks require non-linearities like ReLU and Sigmoid.",
                "difficulty": 0.45,
                "content": "Without non-linear activation functions, a deep neural network with 100 layers would collapse into a single equivalent linear transformation, since W2 * (W1 * x) = (W2 * W1) * x = W_combined * x. Activation functions like ReLU(z) = max(0, z) or GELU introduce piecewise non-linearity, allowing networks to act as universal function approximators."
            },
            {
                "page": 4,
                "section": "2.3 Gradient Descent Optimization",
                "context": "Covers loss functions and iterative optimization algorithms.",
                "difficulty": 0.55,
                "content": "Gradient descent minimizes a loss function L(theta) by stepping parameters in the direction of steepest decrease: theta_new = theta_old - eta * grad_L(theta). The learning rate eta controls step magnitude. If eta is too small, convergence is agonizingly slow; if eta is too large, the optimizer overshoots minima and diverges."
            },
            {
                "page": 5,
                "section": "3.1 Backpropagation & The Chain Rule",
                "context": "Explains multivariable chain rule implementation for computing deep network parameter gradients.",
                "difficulty": 0.70,
                "content": "Backpropagation computes dL/dw using recursive application of the calculus chain rule. In the forward pass, intermediate activations and pre-activations z are cached. In the backward pass, incoming error gradients delta = dL/dz are scaled by local derivatives and propagated backwards to previous layers. This prevents redundant exponential computation."
            },
            {
                "page": 6,
                "section": "4.1 Scaled Dot-Product Attention",
                "context": "Details the Transformer self-attention formula Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V.",
                "difficulty": 0.85,
                "content": "Scaled Dot-Product Attention transforms input representations into Query (Q), Key (K), and Value (V) matrices. The attention weight matrix is computed as Attention_Weights = softmax((Q * K^T) / sqrt(d_k)). The scaling factor sqrt(d_k) prevents dot products from growing excessively large in high dimensions, which would cause softmax gradients to vanish."
            }
        ]
    }
]

async def seed_knowledge_base():
    print("Initializing Database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Create default demo user
        user = User(id="student_1", name="Alex Rivera", email="alex@student.edu")
        db.add(user)
        await db.commit()

        for cur in SAMPLE_CURRICULUM:
            doc_id = str(uuid.uuid4())
            db_doc = Document(
                id=doc_id,
                title=cur["title"],
                source_type="textbook",
                total_pages=len(cur["chunks"]),
                status="indexed"
            )
            db.add(db_doc)
            await db.commit()

            # Pre-generate chunk IDs for deterministic alignment
            chunk_ids = []
            for ch in cur["chunks"]:
                cid = str(uuid.uuid4())
                ch["id"] = cid
                ch["chunk_id"] = cid
                ch["doc_id"] = doc_id
                ch["doc_title"] = cur["title"]
                chunk_ids.append(cid)

            print(f"Populating Knowledge Graph for: {cur['title']}")
            for c in cur["concepts"]:
                await graph_store.add_concept(
                    name=c["name"],
                    description=c["description"],
                    domain=c["domain"],
                    difficulty=c["difficulty"],
                    source_chunk_ids=chunk_ids
                )
                # Store concept in DB
                db_c = Concept(
                    name=c["name"],
                    description=c["description"],
                    domain=c["domain"],
                    base_difficulty=c["difficulty"]
                )
                db.add(db_c)
                await db.commit()
                await db.refresh(db_c)

                # Initialize learner mastery prior
                m_prior = 0.80 if c["difficulty"] <= 0.35 else (0.45 if c["difficulty"] <= 0.60 else 0.20)
                lm = LearnerMastery(
                    user_id="student_1",
                    concept_id=db_c.id,
                    p_mastery=m_prior,
                    uncertainty=0.30
                )
                db.add(lm)

                for prereq in c["prerequisites"]:
                    await graph_store.add_prerequisite(prereq, c["name"], source_chunk_ids=chunk_ids)

                for m in c["misconceptions"]:
                    await graph_store.add_misconception(
                        concept_name=c["name"],
                        misconception_name=m["name"],
                        description=m["description"],
                        refutation=m["refutation"],
                        source_chunk_ids=chunk_ids
                    )
                    db_m = Misconception(
                        concept_id=db_c.id,
                        name=m["name"],
                        description=m["description"],
                        refutation_strategy=m["refutation"]
                    )
                    db.add(db_m)

                # Create sample FSRS Flashcard
                card = ReviewCard(
                    user_id="student_1",
                    concept_id=db_c.id,
                    question=f"What is the core principle of {c['name']}?",
                    answer=c["description"],
                    explanation=f"Foundational requirement for {c['domain']}.",
                    difficulty=5.0,
                    stability=2.0
                )
                db.add(card)

            await db.commit()

            print(f"Embedding and indexing {len(cur['chunks'])} chunks...")
            texts = [f"{ch['context']}\n\n{ch['content']}" for ch in cur["chunks"]]
            vectors = embedding_service.embed_documents(texts)

            qdrant_points = []
            for i, ch in enumerate(cur["chunks"]):
                chunk_id = ch["id"]
                db_ch = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    page_number=ch["page"],
                    chunk_index=i,
                    section_title=ch["section"],
                    content=ch["content"],
                    contextual_line=ch["context"],
                    difficulty_score=ch["difficulty"]
                )
                db.add(db_ch)

                qdrant_points.append({
                    "id": chunk_id,
                    "vector": vectors[i],
                    "payload": {
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "doc_title": cur["title"],
                        "page_number": ch["page"],
                        "section_title": ch["section"],
                        "content": ch["content"],
                        "contextual_line": ch["context"],
                        "difficulty_score": ch["difficulty"],
                        "concepts": [cp["name"] for cp in cur["concepts"]]
                    }
                })

            vector_store.upsert_chunks(qdrant_points)
            bm25_engine.index(cur["chunks"])
            await db.commit()

            # Build communities and pre-computed summaries for GraphRAG
            from app.pipeline.offline.graph_extractor import graph_extractor
            await graph_extractor.build_and_summarize_communities(domain=cur["title"])

    print("\nKnowledge Base Seeding Complete!")
    print(f"Total Concepts in Graph: {graph_store.nx_graph.number_of_nodes()}")
    print(f"Total Edges in Graph: {graph_store.nx_graph.number_of_edges()}")
    print(f"Total Communities in GraphRAG: {len(graph_store.communities)}")

if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
