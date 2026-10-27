# Technology Stack & Tools Inventory: AI Study Buddy

This document provides a comprehensive inventory of all technologies, libraries, databases, and frameworks utilized across the **AI Study Buddy** platform, detailing their exact purpose and operational role within the system.

---

## 1. Programming Languages & Core Runtimes

| Technology | Version / Spec | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Primary backend language powering the 12-step deterministic pedagogical pipeline, ingestion workers, mathematical modeling (BKT, FSRS), and API services. |
| **JavaScript (ES6+)** | Modern ECMAScript | Core frontend language powering interactive UI state, canvas graph rendering, polling workers, and WebSockets. |
| **Node.js** | `v20 LTS` | Build and tooling runtime for compiling the React SPA bundle with Vite. |
| **HTML5 & CSS3** | Modern Standards | Semantic structure and responsive design featuring custom CSS variables, dark-mode glassmorphism, and responsive layouts. |

---

## 2. Web Frameworks & API Architecture

| Tool | Version / Library | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **FastAPI** | `>=0.110.0` | Asynchronous high-performance REST API framework serving chat endpoints, file upload streams, graph inspection, and learner telemetry. |
| **Uvicorn** | `>=0.28.0` (standard) | Lightning-fast ASGI server running the FastAPI application with multi-worker event loops. |
| **React** | `^18.2.0` | Declarative UI framework powering modular components (ChatWorkspace, ConceptGraphCanvas, PageInspector, LearnerDashboard, StudyToolsView). |
| **Vite** | `^5.0.0` | Next-generation frontend build tool providing sub-second Hot Module Replacement (HMR) and optimized rollup production bundles. |
| **Pydantic & Pydantic-Settings** | `>=2.6.0` | Type enforcement, structured schema validation (e.g., `TutorPlan`, `ClaimVerificationReport`), and environment variable parsing. |
| **Lucide React** | `^0.344.0` | Consistent, clean icon set for study tools, upload status indicators, citations, and navigation. |

---

## 3. Databases & Storage Engines

| Database Engine | Type | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **Qdrant** | Vector Database (`v1.8.4`) | High-performance Rust-based vector search engine storing 384-dimensional dense chunk embeddings (`kb_chunks`) and episodic learner traces (`learner_traces`) with Cosine distance indexing. |
| **SQLite with aiosqlite** | Relational DB | Asynchronous local SQL database (`studybuddy.db`) maintaining user profiles, documents, page metadata, chat session turns, and concept mastery state. |
| **Neo4j** | Graph Database (`5.20-community`) | Native graph database executing Cypher queries to model prerequisites (`(:Concept)-[:PREREQUISITE_FOR]->(:Concept)`), hierarchical chapters, and Louvain topological communities. |
| **NetworkX** | Embedded In-Memory Graph | Lightweight zero-config graph library providing fallback directed acyclic graph (DAG) traversal and BFS prerequisite ancestor lookup when Neo4j is offline. |
| **Local File Storage** | Persistent Volume | Dedicated file directory (`/app/data/storage`) hosting uploaded source documents, rendered high-resolution page preview images (`pages/*.png`), and audio recordings. |

---

## 4. Multimodal Ingestion & Document Parsing

| Tool / Library | Version | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **PyMuPDF (`fitz`)** | `>=1.24.0` | Ultra-fast PDF parsing and high-resolution page rendering (rasterizing PDF pages to PNGs for visual inspection). |
| **PyMuPDF4LLM** | `>=0.0.17` | Extracts markdown, tables, mathematical formulas, and structural hierarchy directly from academic textbooks. |
| **Docling** | `>=2.0.0` | Advanced document layout analysis for complex multi-column academic papers, slide decks, and OCR diagrams. |
| **Trafilatura** | `>=1.8.0` | Robust web scraping engine that extracts clean article body text and metadata from arbitrary URLs, stripping boilerplates and ads. |
| **yt-dlp** | `>=2024.3.10` | Extracts audio transcripts, subtitles, and chapter timestamps from educational YouTube lectures. |

---

## 5. Embeddings, Hybrid Search & Reranking (RAG)

| Tool / Model | Version / Checkpoint | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **FastEmbed** | `>=0.2.6` | Lightweight ONNX runtime generating dense semantic vectors locally on CPU in batches (`batch_size=32`) with minimal latency and no external GPU dependencies. |
| **BAAI/bge-small-en-v1.5** | 384-dimensional ONNX | Default high-efficiency dense embedding model balancing retrieval accuracy with fast inference speed. |
| **Rank-BM25** | `rank-bm25>=0.2.2` | Python-native Okapi BM25 sparse lexical search engine guaranteeing exact keyword matching for formulas, acronyms, and symbols. |
| **Reciprocal Rank Fusion (RRF)** | Custom Algorithm ($k=60$) | Rank-merging algorithm mathematically fusing disparate ranking lists from dense vector search, sparse BM25 search, and graph community hits: $RRF = \sum \frac{1}{60 + r}$. |
| **BGE-Reranker (Cross-Encoder)** | `BAAI/bge-reranker-v2-m3` | Neural cross-encoder computing deep token-level relevance scores across the top retrieved candidates to eliminate false positives. |

---

## 6. Artificial Intelligence & LLMs

| AI Service / Engine | Integration | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **Google Gemini API** | `google-genai` & `google-generativeai` | Core intelligence brain executing multi-turn pedagogical dialogue, intent analysis, concept extraction, and citation-grounded tutoring answers. Models used: `gemini-2.5-flash` / `gemini-3.8-flash`. |
| **XML-Structured Grounding** | Native Prompt Engineering | Formats retrieved chunks in explicit XML tags (`<source id="REF-X" doc="..." page="...">`), instructing Gemini to cite sources natively as `[REF-X: p. Y]`. |
| **Structured JSON Outputs** | Pydantic Schemas | Forces model adherence to typed contracts for `TutorPlan` decisions, intent classification, and verification reports with zero parsing errors. |
| **Unified LLM Fallback Client** | Custom Layer (`llm_client.py`) | Abstracted LLM interface supporting Google Gemini AI Studio with automatic retries and local Ollama fallback for offline resilience. |

---

## 7. Cognitive Modeling & Pedagogical Algorithms

| Algorithm / Framework | Theory / Formulation | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **Bayesian Knowledge Tracing (BKT)** | $P(L_t) = P(L_{t-1}) \cdot (1 - P(S)) / \dots$ | Computes real-time dynamic concept mastery probability per student, accounting for slip and guess probabilities after every interaction. |
| **FSRS (Free Spaced Repetition Scheduler)** | `fsrs>=2.1.0` | Modern DSR (Difficulty, Stability, Retrievability) spaced repetition algorithm scheduling flashcard review intervals for durable memory consolidation. |
| **Zone of Proximal Development (ZPD)** | Vygotskian Scaffolding | Dynamically re-scores candidate content to target material slightly above current student mastery ($\text{Target} = P(L_t) + 0.15$), preventing frustration or boredom. |
| **Root-Cause Prerequisite Traversal** | Directed Graph BFS/DAG | Traverses the concept dependency tree backwards to diagnose whether a student's difficulty stems from unmastered upstream prerequisite concepts. |
| **Deterministic Tutor Planner** | Cognitive Policy Engine | Selects appropriate pedagogical action (`EXPLAIN`, `SOCRATIC`, `HINT`, `REMEDIATE`, `WORKED_EXAMPLE`, or `QUIZ`) based on diagnosis and intent. |

---

## 8. Verification, Security & Observability

| Tool | Role in AI Study Buddy |
| :--- | :--- |
| **LLM Structured Claim Verifier** | High-speed structured fact-checker evaluating generated tutor responses against `<source>` chunks to calculate factual faithfulness and prevent hallucinations. |
| **Prompt Leak & Security Filter** | Rule-based and semantic filter scrubbing output responses to prevent prompt injection or internal system instruction disclosure. |
| **Langfuse** (`langfuse>=2.0.0`) | Open-source LLM observability platform tracing end-to-end turn latency, token counts, retrieval scores, and evaluation metrics with zero overhead in light mode. |
| **RAGAS** (`ragas>=0.1.0`) | Retrieval Augmented Generation Assessment framework evaluating context relevance, answer faithfulness, and answer relevance. |

---

## 9. DevOps, Containerization & Infrastructure

| Tool / Technology | Configuration | Role in AI Study Buddy |
| :--- | :--- | :--- |
| **Docker** | Multi-Stage Hardened Dockerfiles | Containerizes Python FastAPI backend (non-root unprivileged runtime) and React frontend (alpine slim). |
| **Docker Compose** | `docker-compose.yml` (v3.8) | Orchestrates the lightweight local stack: Frontend (Nginx), Backend (FastAPI), and Vector DB (Qdrant) across isolated bridge networks with persistent volumes. |
| **Nginx** | `nginx:alpine-slim` | Production web server hosting compiled static frontend assets and reverse-proxying `/api/`, `/storage/`, and `/ws` WebSockets to the backend container. |
| **GitHub Actions** | `.github/workflows/ci.yml` | Continuous Integration automated workflow running Python unit test suites, frontend production compilation, and compose syntax validation on every push. |
| **Git** | Version Control | Source code control with conventional commit messages and automated `.gitignore` policies safeguarding local secrets and datasets. |
