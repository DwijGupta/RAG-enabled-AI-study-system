import time
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.online.intent import intent_analyzer
from app.pipeline.online.learner_overlay import learner_overlay
from app.pipeline.online.memory import memory_manager
from app.pipeline.online.root_cause import root_cause_finder
from app.pipeline.online.retriever import hybrid_retriever
from app.core.reranker import zpd_reranker
from app.pipeline.online.context_builder import context_builder
from app.pipeline.online.planner import tutor_planner
from app.pipeline.online.writer import grounded_writer
from app.pipeline.online.verifier import claim_verifier
from app.pipeline.online.fallback import fallback_loop
from app.pipeline.online.leak_filter import leak_filter
from app.core.telemetry import telemetry_manager

logger = logging.getLogger(__name__)

class OnlineTutoringPipeline:
    """
    Coordinates the 12-step deterministic online tutoring pipeline
    with asynchronous Langfuse observability spans and zero latency penalty.
    """
    async def run(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # Initiate Langfuse Root Trace
        trace = telemetry_manager.create_trace(
            name="student_tutoring_turn",
            user_id=user_id,
            session_id=session_id,
            input_query=user_query,
            metadata={"source": "api", "pipeline": "deterministic-plan-1"}
        )

        # Step 3: Session Memory Retrieval
        session_data = memory_manager.get_or_create_session(session_id, user_id)
        memory_manager.add_turn(session_id, user_id, "user", user_query)
        past_traces = await memory_manager.retrieve_past_traces(user_id, user_query, limit=2)

        # Step 1, 2, 4: Cognitive State & Intent Diagnosis (Span: cognitive_analysis)
        cog_span = telemetry_manager.create_span(trace, name="cognitive_analysis")
        intent = await intent_analyzer.analyze(user_query, session_data["turns"])
        primary_concept = intent.target_concepts[0] if intent.target_concepts else "General"
        mastery_state = await learner_overlay.get_mastery(user_id, primary_concept, db)
        learner_p = mastery_state["p_mastery"]
        root_cause = await root_cause_finder.find_root_cause(user_id, intent.target_concepts, db)
        weak_c = root_cause.get("weakest_concept")
        telemetry_manager.end_span(
            cog_span,
            output_data={
                "intent": intent.question_type,
                "primary_concept": primary_concept,
                "learner_p": learner_p,
                "weakest_concept": weak_c
            }
        )

        # Step 5: Hybrid Retrieval (Dense BGE-M3 + BM25 + Graph Communities)
        ret_span = telemetry_manager.create_span(trace, name="retrieval_hybrid_3stream", input_data={"query": user_query})
        retrieval_res = await hybrid_retriever.retrieve(
            query=user_query,
            target_concepts=intent.target_concepts,
            weak_concept=weak_c
        )
        telemetry_manager.end_span(
            ret_span,
            output_data={
                "dense_count": len(retrieval_res.get("dense", [])),
                "sparse_count": len(retrieval_res.get("sparse", [])),
                "graph_chunks_count": len(retrieval_res.get("graph_chunks", [])),
                "communities_matched": len(retrieval_res.get("community_summaries", []))
            }
        )

        # Step 6: Alignment via Shared Chunk ID & Reciprocal Rank Fusion (RRF)
        fuse_span = telemetry_manager.create_span(trace, name="fusion_rrf_k60")
        fused = zpd_reranker.reciprocal_rank_fusion([
            retrieval_res["dense"],
            retrieval_res["sparse"],
            retrieval_res.get("graph_chunks", [])
        ], k=60)
        telemetry_manager.end_span(fuse_span, output_data={"fused_candidates_count": len(fused)})

        # Late Interaction Cross-Encoder (Final Filter) with ZPD pedagogical match
        rerank_span = telemetry_manager.create_span(trace, name="reranker_cross_encoder_zpd")
        reranked_chunks = zpd_reranker.rerank_and_filter(
            query=user_query,
            candidates=fused,
            learner_mastery=learner_p,
            top_k=8
        )
        telemetry_manager.end_span(
            rerank_span,
            output_data={"filtered_top_chunks": [c.get("id") for c in reranked_chunks]}
        )

        # Step 7: Context Builder
        pedagogical_context = context_builder.build_context(
            reranked_chunks=reranked_chunks,
            root_cause_result=root_cause,
            learner_mastery=learner_p,
            session_turns=session_data["turns"],
            past_traces=past_traces,
            community_summaries=retrieval_res.get("community_summaries", [])
        )

        # Step 8: Tutor Planner
        plan = tutor_planner.plan(intent, pedagogical_context, root_cause)

        # Step 9: Grounded Writer
        writer_span = telemetry_manager.create_span(
            trace,
            name="writer_grounded_generation",
            input_data={"plan_action": plan.action, "scaffolding": plan.scaffolding_directive}
        )
        try:
            raw_answer = await grounded_writer.write_answer(user_query, plan, pedagogical_context)
        except Exception as e:
            logger.warning("Grounded writer exception (%s). Generating evidence-synthesized response.", str(e))
            evidence_snippets = [f"[{e.cite_id}] {e.content}" for e in pedagogical_context.citeable_evidence[:2]]
            raw_answer = (
                f"### Academic Concept Overview\n\n"
                f"Based on your course materials:\n\n" + "\n\n".join(evidence_snippets) + "\n\n"
                f"**Pedagogical Guidance:** {plan.scaffolding_directive}"
            )
        telemetry_manager.end_span(writer_span, output_data={"raw_answer_length": len(raw_answer)})

        # Step 10: Claim Verifier
        verif_span = telemetry_manager.create_span(trace, name="verifier_claim_nli")
        verification_report = await claim_verifier.verify(raw_answer, pedagogical_context)
        telemetry_manager.end_span(
            verif_span,
            output_data={
                "faithfulness": verification_report.overall_faithfulness,
                "hallucination": verification_report.hallucination_detected
            }
        )

        # Step 11: Fallback Loop (if hallucination or unverified)
        if verification_report.hallucination_detected:
            logger.warning("Low faithfulness detected (%.2f). Executing fallback query rewrite.",
                           verification_report.overall_faithfulness)
            rewritten_q = await fallback_loop.rewrite_query(user_query, weak_c)
            retry_res = await hybrid_retriever.retrieve(rewritten_q, intent.target_concepts, weak_c)
            retry_fused = zpd_reranker.reciprocal_rank_fusion([
                retry_res["dense"],
                retry_res["sparse"],
                retry_res.get("graph_chunks", [])
            ], k=60)
            retry_chunks = zpd_reranker.rerank_and_filter(rewritten_q, retry_fused, learner_p, top_k=3)
            pedagogical_context = context_builder.build_context(
                reranked_chunks=retry_chunks,
                root_cause_result=root_cause,
                learner_mastery=learner_p,
                session_turns=session_data["turns"],
                past_traces=past_traces,
                community_summaries=retry_res.get("community_summaries", [])
            )
            raw_answer = await grounded_writer.write_answer(user_query, plan, pedagogical_context)

        # Step 12: Leak Filter
        clean_response = leak_filter.sanitize(raw_answer)

        # Append response to session memory
        memory_manager.add_turn(session_id, user_id, "assistant", clean_response)

        latency = (time.time() - start_time) * 1000

        # Build citations list for UI
        ui_citations = [
            {
                "cite_id": ev.cite_id,
                "doc_title": ev.doc_title,
                "page_number": ev.page_number,
                "section_title": ev.section_title,
                "image_url": ev.image_url,
                "content_snippet": ev.content[:160] + "..."
            }
            for ev in pedagogical_context.citeable_evidence
        ]

        # Log episodic trace to DB
        await memory_manager.log_interaction_trace(
            user_id=user_id,
            session_id=session_id,
            user_query=user_query,
            tutor_response=clean_response,
            intent_type=intent.question_type,
            target_concepts=intent.target_concepts,
            diagnosed_weak_concept=weak_c,
            planner_action=plan.action,
            citations=ui_citations,
            faithfulness_score=verification_report.overall_faithfulness,
            db=db
        )

        # Log metric scores to Langfuse & Flush
        telemetry_manager.log_score(
            trace_id=trace.id,
            name="faithfulness",
            value=verification_report.overall_faithfulness,
            comment=f"Action: {plan.action}"
        )
        telemetry_manager.log_score(
            trace_id=trace.id,
            name="latency_ms",
            value=latency
        )
        telemetry_manager.flush()

        return {
            "answer": clean_response,
            "citations": ui_citations,
            "intent": intent.model_dump(),
            "planner_action": plan.action,
            "rationale": plan.rationale,
            "learner_mastery": learner_p,
            "diagnosed_weakness": weak_c,
            "faithfulness_score": verification_report.overall_faithfulness,
            "latency_ms": round(latency, 1),
            "trace_id": trace.id
        }

online_pipeline = OnlineTutoringPipeline()
