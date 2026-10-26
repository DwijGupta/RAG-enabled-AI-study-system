import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import networkx as nx
from app.core.config import settings

logger = logging.getLogger(__name__)

class GraphStore:
    def __init__(self):
        self.use_neo4j = False
        self.driver = None
        self.nx_graph = nx.DiGraph()
        self.nx_file = os.path.join(settings.DATA_DIR, "concept_graph.json")
        self.community_file = os.path.join(settings.DATA_DIR, "graph_communities.json")
        self.communities: Dict[str, Dict[str, Any]] = {}
        self._init_connection()
        self._load_nx_cache()
        self._load_community_cache()

    def _init_connection(self):
        driver = None
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            driver.verify_connectivity()
            self.driver = driver
            self.use_neo4j = True
            logger.info("Connected successfully to Neo4j server at %s", settings.NEO4J_URI)
        except Exception as e:
            logger.warning("Neo4j server unavailable (%s). Using embedded NetworkX graph store.", str(e))
            if driver:
                try:
                    driver.close()
                except Exception:
                    pass
            self.driver = None
            self.use_neo4j = False

    def _load_nx_cache(self):
        if os.path.exists(self.nx_file):
            try:
                with open(self.nx_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.nx_graph = nx.node_link_graph(data, directed=True)
                logger.info("Loaded %d concepts and %d relationships from local graph cache.",
                            self.nx_graph.number_of_nodes(), self.nx_graph.number_of_edges())
            except Exception as e:
                logger.error("Failed to load local graph cache: %s", str(e))
                self.nx_graph = nx.DiGraph()

    def _save_nx_cache(self):
        try:
            data = nx.node_link_data(self.nx_graph)
            with open(self.nx_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to persist graph cache: %s", str(e))

    def _load_community_cache(self):
        if os.path.exists(self.community_file):
            try:
                with open(self.community_file, "r", encoding="utf-8") as f:
                    self.communities = json.load(f)
                logger.info("Loaded %d pre-computed communities from cache.", len(self.communities))
            except Exception as e:
                logger.error("Failed to load community cache: %s", str(e))
                self.communities = {}

    def _save_community_cache(self):
        try:
            with open(self.community_file, "w", encoding="utf-8") as f:
                json.dump(self.communities, f, indent=2)
        except Exception as e:
            logger.error("Failed to persist community cache: %s", str(e))

    async def add_concept(
        self,
        name: str,
        description: str = "",
        domain: str = "General",
        difficulty: float = 0.5,
        source_chunk_ids: Optional[List[str]] = None
    ):
        name_clean = name.strip()
        cids = [cid for cid in (source_chunk_ids or []) if cid]

        if self.use_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MERGE (c:Concept {name: $name})
                        SET c.description = $description, c.domain = $domain, c.difficulty = $difficulty
                        SET c.source_chunk_ids = [x IN (coalesce(c.source_chunk_ids, []) + $cids) WHERE x IS NOT NULL]
                        """,
                        name=name_clean, description=description, domain=domain, difficulty=difficulty, cids=cids
                    )
            except Exception as e:
                logger.error("Neo4j error in add_concept: %s", str(e))
        
        # Always update local graph representation with aligned chunk IDs
        existing_cids = []
        if self.nx_graph.has_node(name_clean):
            existing_cids = list(self.nx_graph.nodes[name_clean].get("source_chunk_ids", []))
        for cid in cids:
            if cid not in existing_cids:
                existing_cids.append(cid)

        self.nx_graph.add_node(
            name_clean,
            type="concept",
            description=description,
            domain=domain,
            difficulty=difficulty,
            source_chunk_ids=existing_cids
        )
        self._save_nx_cache()

    async def add_prerequisite(
        self,
        source_concept: str,
        target_concept: str,
        strength: float = 1.0,
        source_chunk_ids: Optional[List[str]] = None
    ):
        """
        source_concept is a prerequisite for target_concept.
        Direction: source -> target (Edge attribute: relation='PREREQUISITE_FOR')
        """
        s_clean = source_concept.strip()
        t_clean = target_concept.strip()
        cids = [cid for cid in (source_chunk_ids or []) if cid]
        
        if s_clean == t_clean:
            return

        if self.use_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (s:Concept {name: $source}), (t:Concept {name: $target})
                        MERGE (s)-[r:PREREQUISITE_FOR]->(t)
                        SET r.strength = $strength
                        SET r.source_chunk_ids = [x IN (coalesce(r.source_chunk_ids, []) + $cids) WHERE x IS NOT NULL]
                        """,
                        source=s_clean, target=t_clean, strength=strength, cids=cids
                    )
            except Exception as e:
                logger.error("Neo4j error in add_prerequisite: %s", str(e))

        if not self.nx_graph.has_node(s_clean):
            self.nx_graph.add_node(s_clean, type="concept", description="", domain="General", difficulty=0.4, source_chunk_ids=cids)
        if not self.nx_graph.has_node(t_clean):
            self.nx_graph.add_node(t_clean, type="concept", description="", domain="General", difficulty=0.6, source_chunk_ids=cids)

        self.nx_graph.add_edge(s_clean, t_clean, relation="PREREQUISITE_FOR", strength=strength, source_chunk_ids=cids)
        self._save_nx_cache()

    async def add_misconception(
        self,
        concept_name: str,
        misconception_name: str,
        description: str,
        refutation: str = "",
        source_chunk_ids: Optional[List[str]] = None
    ):
        c_clean = concept_name.strip()
        m_clean = misconception_name.strip()
        cids = [cid for cid in (source_chunk_ids or []) if cid]

        if self.use_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (c:Concept {name: $concept})
                        MERGE (m:Misconception {name: $misconception})
                        SET m.description = $description, m.refutation = $refutation
                        SET m.source_chunk_ids = [x IN (coalesce(m.source_chunk_ids, []) + $cids) WHERE x IS NOT NULL]
                        MERGE (m)-[:REFUTES]->(c)
                        """,
                        concept=c_clean, misconception=m_clean, description=description, refutation=refutation, cids=cids
                    )
            except Exception as e:
                logger.error("Neo4j error in add_misconception: %s", str(e))

        self.nx_graph.add_node(
            m_clean,
            type="misconception",
            description=description,
            refutation=refutation,
            source_chunk_ids=cids
        )
        self.nx_graph.add_edge(m_clean, c_clean, relation="REFUTES", source_chunk_ids=cids)
        self._save_nx_cache()

    def detect_communities(self) -> List[Dict[str, Any]]:
        """
        Groups related nodes into hierarchical 'communities' using Louvain or modularity
        clustering algorithms inside the Graph Store (Microsoft GraphRAG style).
        Aggregates linked source_chunk_ids per community for deterministic RRF fusion.
        """
        concept_nodes = [
            n for n, d in self.nx_graph.nodes(data=True)
            if d.get("type", "concept") == "concept"
        ]
        if not concept_nodes:
            return []

        subgraph = self.nx_graph.subgraph(concept_nodes).to_undirected()

        communities_raw = []
        try:
            if subgraph.number_of_edges() > 0:
                from networkx.algorithms.community import louvain_communities
                communities_raw = list(louvain_communities(subgraph, seed=42))
            else:
                communities_raw = [{n} for n in concept_nodes]
        except Exception as e:
            logger.warning("Louvain community detection fallback to greedy modularity (%s)", str(e))
            try:
                from networkx.algorithms.community import greedy_modularity_communities
                communities_raw = list(greedy_modularity_communities(subgraph))
            except Exception:
                communities_raw = [{n} for n in concept_nodes]

        detected = []
        for idx, comm_set in enumerate(communities_raw):
            members = sorted(list(comm_set))
            chunk_ids_set = set()
            for m in members:
                node_data = self.nx_graph.nodes.get(m, {})
                for cid in node_data.get("source_chunk_ids", []):
                    if cid:
                        chunk_ids_set.add(cid)

            comm_id = f"community_{idx + 1}"
            detected.append({
                "community_id": comm_id,
                "members": members,
                "source_chunk_ids": sorted(list(chunk_ids_set))
            })

        return detected

    async def save_community(
        self,
        community_id: str,
        title: str,
        summary: str,
        member_concepts: List[str],
        source_chunk_ids: List[str],
        embedding: Optional[List[float]] = None
    ):
        """
        Saves pre-computed community summary and its dense vector embedding.
        """
        self.communities[community_id] = {
            "community_id": community_id,
            "title": title,
            "summary": summary,
            "member_concepts": member_concepts,
            "source_chunk_ids": source_chunk_ids,
            "embedding": embedding or []
        }

        if self.use_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    session.run(
                        """
                        MERGE (comm:Community {id: $id})
                        SET comm.title = $title, comm.summary = $summary, comm.source_chunk_ids = $cids
                        WITH comm
                        UNWIND $members AS m_name
                        MATCH (c:Concept {name: m_name})
                        MERGE (c)-[:IN_COMMUNITY]->(comm)
                        """,
                        id=community_id, title=title, summary=summary,
                        cids=source_chunk_ids, members=member_concepts
                    )
            except Exception as e:
                logger.error("Neo4j error in save_community: %s", str(e))

        self._save_community_cache()

    def search_community_summaries(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Deterministic vector search against Community Summaries in the Graph Store.
        No dynamic Cypher query writing on the fly.
        """
        if not self.communities or not query_vector:
            return []

        q_arr = np.array(query_vector, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_arr))
        if q_norm == 0:
            return []

        results = []
        for comm_id, comm in self.communities.items():
            emb = comm.get("embedding")
            if not emb:
                continue
            emb_arr = np.array(emb, dtype=np.float32)
            e_norm = float(np.linalg.norm(emb_arr))
            if e_norm == 0:
                continue
            sim = float(np.dot(q_arr, emb_arr) / (q_norm * e_norm))
            results.append({
                "community_id": comm_id,
                "title": comm["title"],
                "summary": comm["summary"],
                "member_concepts": comm["member_concepts"],
                "source_chunk_ids": comm.get("source_chunk_ids", []),
                "score": sim
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_prerequisites(self, concept_name: str) -> List[str]:
        """
        Returns all immediate prerequisites required to understand concept_name.
        In directed graph: (prerequisite) -> (concept_name)
        """
        concept_clean = concept_name.strip()
        if not self.nx_graph.has_node(concept_clean):
            return []
        
        prereqs = []
        for u, v, data in self.nx_graph.in_edges(concept_clean, data=True):
            if data.get("relation") == "PREREQUISITE_FOR":
                prereqs.append(u)
        return prereqs

    def get_full_prerequisite_tree(self, concept_name: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Traverses upstream prerequisites recursively (ancestors in prerequisite DAG).
        """
        concept_clean = concept_name.strip()
        if not self.nx_graph.has_node(concept_clean):
            return []

        tree = []
        visited = set()
        queue = [(concept_clean, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if curr in visited or depth > max_depth:
                continue
            visited.add(curr)

            node_data = self.nx_graph.nodes.get(curr, {})
            prereqs = self.get_prerequisites(curr)
            
            tree.append({
                "concept": curr,
                "depth": depth,
                "description": node_data.get("description", ""),
                "difficulty": node_data.get("difficulty", 0.5),
                "prerequisites": prereqs
            })

            for p in prereqs:
                if p not in visited:
                    queue.append((p, depth + 1))

        return tree

    def get_misconceptions(self, concept_name: str) -> List[Dict[str, str]]:
        concept_clean = concept_name.strip()
        if not self.nx_graph.has_node(concept_clean):
            return []

        results = []
        for u, v, data in self.nx_graph.in_edges(concept_clean, data=True):
            if data.get("relation") == "REFUTES":
                node_data = self.nx_graph.nodes.get(u, {})
                results.append({
                    "name": u,
                    "description": node_data.get("description", ""),
                    "refutation": node_data.get("refutation", "")
                })
        return results

    def get_all_graph_data(self) -> Dict[str, Any]:
        """
        Returns nodes and edges formatted for 2D frontend force-directed graph visualization.
        """
        nodes = []
        edges = []

        for node_id, data in self.nx_graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": node_id,
                "type": data.get("type", "concept"),
                "description": data.get("description", ""),
                "domain": data.get("domain", "General"),
                "difficulty": data.get("difficulty", 0.5),
                "source_chunk_ids": data.get("source_chunk_ids", [])
            })

        for u, v, data in self.nx_graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "PREREQUISITE_FOR"),
                "strength": data.get("strength", 1.0),
                "source_chunk_ids": data.get("source_chunk_ids", [])
            })

        return {"nodes": nodes, "edges": edges, "communities": self.communities}

    def close(self):
        """Closes any active Neo4j database driver connection pool."""
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
            self.driver = None

# Singleton instance
graph_store = GraphStore()

import atexit
atexit.register(graph_store.close)

