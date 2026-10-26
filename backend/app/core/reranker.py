import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ZPDReranker:
    def __init__(self):
        self.cross_encoder = None
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import CrossEncoder
            # bge-reranker-v2-m3 or small cross-encoder
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Loaded CrossEncoder for neural reranking.")
        except Exception as e:
            logger.warning("CrossEncoder not loaded (%s). Using weighted rank fusion.", str(e))
            self.cross_encoder = None

    def reciprocal_rank_fusion(self, ranked_lists: List[List[Dict[str, Any]]], k: int = 60) -> List[Dict[str, Any]]:
        """
        Combines multiple ranked lists (e.g., Dense BGE-M3, BM25, Graph) using RRF.
        score(d) = sum( 1 / (k + rank(d)) )
        """
        scores: Dict[str, float] = {}
        items: Dict[str, Dict[str, Any]] = {}

        for r_list in ranked_lists:
            for rank, item in enumerate(r_list):
                item_id = item.get("id") or item.get("chunk_id")
                if not item_id:
                    continue
                if item_id not in scores:
                    scores[item_id] = 0.0
                    items[item_id] = item
                scores[item_id] += 1.0 / (k + rank + 1)

        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for s_id in sorted_ids:
            elem = items[s_id].copy()
            elem["rrf_score"] = scores[s_id]
            results.append(elem)

        return results

    def compute_zpd_multiplier(self, chunk_difficulty: float, learner_mastery: float) -> float:
        """
        Zone of Proximal Development (Vygotsky ZPD) Score.
        Optimal challenge target is slightly above student's current mastery:
        target = learner_mastery + 0.15
        Penalizes chunks that are either way too advanced (frustration) or way too basic (boredom).
        """
        target_difficulty = min(1.0, learner_mastery + 0.15)
        # Gaussian penalty around target
        diff = chunk_difficulty - target_difficulty
        sigma = 0.35
        zpd_score = math.exp(-(diff ** 2) / (2 * (sigma ** 2)))
        return zpd_score

    def rerank_and_filter(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        learner_mastery: float = 0.5,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Applies Cross-Encoder relevance scoring and ZPD difficulty alignment.
        """
        if not candidates:
            return []

        # Step 1: Neural relevance score
        pairs = []
        for c in candidates:
            text = c.get("content") or c.get("text") or ""
            pairs.append((query, text))

        if self.cross_encoder is not None and pairs:
            try:
                ce_scores = self.cross_encoder.predict(pairs)
                for i, score in enumerate(ce_scores):
                    candidates[i]["relevance_score"] = float(score)
            except Exception as e:
                logger.error("Error in CrossEncoder scoring: %s", str(e))
                for c in candidates:
                    c["relevance_score"] = c.get("rrf_score", 0.5)
        else:
            for c in candidates:
                c["relevance_score"] = c.get("rrf_score", c.get("score", 0.5))

        # Normalize relevance scores to [0, 1]
        rel_vals = [c["relevance_score"] for c in candidates]
        min_v, max_v = min(rel_vals), max(rel_vals)
        for c in candidates:
            if max_v > min_v:
                c["norm_relevance"] = (c["relevance_score"] - min_v) / (max_v - min_v)
            else:
                c["norm_relevance"] = 0.5

        # Step 2: Calculate ZPD Match & Final Combined Score
        for c in candidates:
            chunk_diff = c.get("difficulty_score", 0.5)
            zpd_weight = self.compute_zpd_multiplier(chunk_diff, learner_mastery)
            c["zpd_multiplier"] = zpd_weight
            
            # Final score = 0.7 * Relevance + 0.3 * ZPD fit
            c["final_zpd_score"] = (0.7 * c["norm_relevance"]) + (0.3 * zpd_weight)

        # Sort by final ZPD score descending
        candidates.sort(key=lambda x: x["final_zpd_score"], reverse=True)
        return candidates[:top_k]

zpd_reranker = ZPDReranker()
