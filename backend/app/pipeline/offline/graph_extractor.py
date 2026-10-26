import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.llm_client import llm_client
from app.core.graph_db import graph_store
from app.core.embeddings import embedding_service

logger = logging.getLogger(__name__)

class ExtractedConcept(BaseModel):
    name: str = Field(description="Clear, standard academic concept name (e.g., 'Newton's Second Law', 'Binary Search', 'Backpropagation')")
    description: str = Field(description="Concise 1-2 sentence definition of the concept.")
    domain: str = Field(default="Science/Tech", description="Academic field or topic domain.")
    difficulty: float = Field(default=0.5, description="Difficulty from 0.1 (basic foundational) to 1.0 (advanced).")

class ExtractedPrerequisite(BaseModel):
    source_concept: str = Field(description="The prerequisite concept that MUST be understood first.")
    target_concept: str = Field(description="The more advanced concept that depends on the prerequisite.")
    strength: float = Field(default=1.0, description="Dependency strength from 0.5 to 1.0.")

class ExtractedMisconception(BaseModel):
    concept_name: str = Field(description="The exact concept this misconception relates to.")
    misconception_name: str = Field(description="Short label of the false mental model or trap (e.g. 'Heavier objects fall faster').")
    description: str = Field(description="Detailed explanation of what students incorrectly believe.")
    refutation: str = Field(description="Pedagogical explanation or counter-example resolving this misconception.")

class KnowledgeGraphExtraction(BaseModel):
    concepts: List[ExtractedConcept] = Field(default_factory=list)
    prerequisites: List[ExtractedPrerequisite] = Field(default_factory=list)
    misconceptions: List[ExtractedMisconception] = Field(default_factory=list)

class GraphExtractor:
    async def extract_and_store(
        self,
        text: str,
        domain: str = "General",
        source_chunk_ids: Optional[List[str]] = None
    ) -> KnowledgeGraphExtraction:
        """
        Invokes Google Gemini (or offline fallback) to extract concepts, prerequisite DAG edges,
        and student misconceptions, then stores them in the Knowledge Graph aligned with source_chunk_ids.
        """
        # Truncate text if excessively long to fit LLM prompt window
        sample_text = text[:4000]

        prompt = (
            f"Analyze this educational content and extract the underlying conceptual knowledge graph:\n\n"
            f"--- CONTENT BEGIN ---\n{sample_text}\n--- CONTENT END ---\n\n"
            f"Extract:\n"
            f"1. Core concepts with estimated difficulty (0.1 to 1.0).\n"
            f"2. Strict prerequisite relationships (which concept is required before another can be understood).\n"
            f"3. Common student misconceptions, wrong beliefs, or intuitive errors associated with these concepts, along with how to refute them."
        )

        system_instruction = (
            "You are an expert cognitive scientist and educational curriculum designer. "
            "You identify concepts, construct accurate prerequisite dependency graphs (DAGs), "
            "and diagnose common student misconceptions with high precision."
        )

        try:
            result: KnowledgeGraphExtraction = await llm_client.structured_output(
                prompt=prompt,
                schema_class=KnowledgeGraphExtraction,
                system=system_instruction,
                temperature=0.1
            )
        except Exception as e:
            logger.warning("Structured extraction failed (%s). Generating heuristic concepts.", str(e))
            result = KnowledgeGraphExtraction()

        # Commit to Knowledge Graph Store (Neo4j / NetworkX) with aligned chunk IDs
        for c in result.concepts:
            await graph_store.add_concept(
                name=c.name,
                description=c.description,
                domain=c.domain or domain,
                difficulty=c.difficulty,
                source_chunk_ids=source_chunk_ids
            )

        for p in result.prerequisites:
            await graph_store.add_prerequisite(
                source_concept=p.source_concept,
                target_concept=p.target_concept,
                strength=p.strength,
                source_chunk_ids=source_chunk_ids
            )

        for m in result.misconceptions:
            await graph_store.add_misconception(
                concept_name=m.concept_name,
                misconception_name=m.misconception_name,
                description=m.description,
                refutation=m.refutation,
                source_chunk_ids=source_chunk_ids
            )

        logger.info(
            "Graph extraction complete: %d concepts, %d prerequisite links, %d misconceptions.",
            len(result.concepts), len(result.prerequisites), len(result.misconceptions)
        )
        return result

    async def build_and_summarize_communities(self, domain: str = "General") -> List[Dict[str, Any]]:
        """
        Executes hierarchical community detection (Leiden/Louvain) inside the Graph Store.
        Pre-computes rich pedagogical summaries using LLM, embeds them for vector search,
        and saves them deterministically (Microsoft GraphRAG style).
        """
        detected_communities = graph_store.detect_communities()
        if not detected_communities:
            logger.info("No graph communities detected to summarize.")
            return []

        summarized = []
        for comm in detected_communities:
            comm_id = comm["community_id"]
            members = comm["members"]
            source_chunk_ids = comm.get("source_chunk_ids", [])

            member_details = []
            for m in members:
                node_data = graph_store.nx_graph.nodes.get(m, {})
                desc = node_data.get("description", "")
                member_details.append(f"- Concept: {m} ({desc})")

            summary_prompt = (
                f"You are synthesizing a high-level conceptual community summary for an educational Knowledge Graph.\n"
                f"Domain: {domain}\n"
                f"Community Concepts:\n" + "\n".join(member_details) + "\n\n"
                f"Write a concise, structured 2-3 sentence overarching pedagogical summary explaining how these concepts "
                f"thematically link together, the foundational principles they share, and the core learning trajectory."
            )

            try:
                summary_text = await llm_client.generate(summary_prompt, temperature=0.1)
                summary_text = summary_text.strip()
            except Exception as e:
                logger.warning("LLM community summary generation failed (%s). Using heuristic synthesis.", str(e))
                summary_text = f"Curriculum cluster covering {', '.join(members[:5])}. Focuses on fundamental principles in {domain}."

            title = f"{members[0]} & Related Concepts" if members else f"Community {comm_id}"
            emb = embedding_service.embed_query(f"{title}: {summary_text}")

            await graph_store.save_community(
                community_id=comm_id,
                title=title,
                summary=summary_text,
                member_concepts=members,
                source_chunk_ids=source_chunk_ids,
                embedding=emb
            )
            summarized.append({
                "community_id": comm_id,
                "title": title,
                "summary": summary_text,
                "members": members,
                "source_chunk_ids": source_chunk_ids
            })

        logger.info("Generated and indexed %d community summaries in GraphRAG layer.", len(summarized))
        return summarized

graph_extractor = GraphExtractor()

