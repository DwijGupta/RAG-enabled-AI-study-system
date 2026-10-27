# AI Study Buddy — Full Project Context Document

> **Purpose:** This document provides a complete, self-contained overview of the **AI Study Buddy** project — its goals, architecture, technology stack, codebase structure, algorithms, data models, API surface, deployment strategy, and key design decisions. It is designed to be shared with LLMs, collaborators, or evaluators for report writing, presentation preparation, or onboarding.

---

## 1. Project Identity

| Field | Details |
| :--- | :--- |
| **Project Name** | AI Study Buddy: Learner-State-Aware RAG Platform |
| **Tagline** | An enterprise educational tutoring platform combining RAG, cognitive modeling, and adaptive pedagogy. |
| **Repository** | `DwijGupta/RAG-enabled-AI-study-system` |
| **License** | MIT License (2026) |
| **Version** | 1.0.0 |
| **Primary Author(s)** | AI Study Buddy Contributors |

---

## 2. Problem Statement & Motivation

Traditional AI tutoring systems treat all learners identically — they retrieve static content and generate one-size-fits-all answers regardless of what the student already knows or struggles with. This leads to:

- **Frustration** when content is too advanced for the student.
- **Boredom** when content is too basic for the student.
- **Hallucinations** when LLM responses are not grounded in course material.
- **No long-term retention** because spaced review is never scheduled.
- **No diagnostic insight** into *why* a student is stuck (missing prerequisites).

**AI Study Buddy solves all five problems** by building a closed-loop intelligent tutoring system that:

1. **Knows what the student knows** — via Bayesian Knowledge Tracing (BKT) mastery modeling.
2. **Retrieves the right content** — via hybrid dense + sparse RAG with prerequisite-aware reranking.
3. **Explains at the right level** — via Vygotskian Zone of Proximal Development (ZPD) calibration.
4. **Verifies its own answers** — via structured claim-level hallucination detection.
5. **Schedules long-term retention** — via FSRS spaced repetition.

---

## 3. High-Level System Architecture

The system operates across **three unified phases**:

### Phase 1: Asynchronous Multimodal Ingestion
- User uploads documents (PDF, DOCX, PPTX, Web URLs, YouTube) via the dashboard.
- Backend returns `HTTP 202 Accepted` with a `job_id` and processes in background.
- **Dual parser** (PyMuPDF + Docling) extracts text, tables, equations, and page images.
- **Contextual hierarchical chunker** splits content with section-aware boundaries.
- Three parallel indexing paths:
  - **Dense embeddings** → Qdrant vector DB (`kb_chunks` collection, 384-dim BGE ONNX).
  - **Sparse lexical index** → Rank-BM25 inverted index.
  - **Knowledge graph** → Neo4j/NetworkX DAG of concepts and `PREREQUISITE_FOR` relationships, plus Louvain community summaries.

### Phase 2: 12-Step Online Pedagogical Pipeline
Every student query passes through a deterministic, quality-controlled 12-step pipeline:

| Step | Component | What It Does |
|:-----|:----------|:-------------|
| 1 | **Memory Lookup** | Retrieves recent chat turns from SQLite session memory + past struggles from Qdrant `learner_traces`. |
| 2 | **Intent Analysis** | Gemini classifies intent type, target concepts, and question difficulty. |
| 3 | **Learner Overlay** | BKT looks up the student's current mastery probability P(L_t) ∈ [0.0, 1.0] for each concept. |
| 4 | **Root-Cause Gap Analysis** | Traverses the prerequisite DAG backwards (BFS) to find unmastered foundational concepts (P < 0.45). |
| 5 | **Hybrid Retrieval** | Parallel dense (Qdrant cosine) + sparse (BM25 keyword) search, fused via Reciprocal Rank Fusion (k=60). |
| 6 | **ZPD Neural Reranking** | BGE cross-encoder re-scores candidates calibrated to the student's zone: Target = P(L_t) + 0.15. |
| 7 | **Context Pruning** | Deduplicates overlapping chunk text and caps context under 2,500 tokens. |
| 8 | **Tutor Planner** | Deterministic cognitive policy selects action: `EXPLAIN`, `SOCRATIC`, `HINT`, `REMEDIATE`, `WORKED_EXAMPLE`, or `QUIZ`. |
| 9 | **Grounded Generation** | Gemini generates the response with XML-tagged source citations: `<source id="REF-X" doc="..." page="...">`. |
| 10 | **Claim Verification** | Structured LLM output (Temp=0.0) extracts atomic claims and verifies entailment against sources. |
| 11 | **Leak & Guardrail Filter** | Regex + policy sanitizer strips system prompt leaks and unintended metadata. |
| 12 | **Observability** | Langfuse logs latency, token counts, faithfulness scores, and retrieval metrics. |

### Phase 3: Closed-Loop Mastery & Spaced Review
- **Practice generation**: Diagnostic MCQ and open-ended questions based on emerging-mastery concepts.
- **BKT state update**: After every student answer, mastery probability is recalculated accounting for slip P(S) and guess P(G).
- **FSRS scheduling**: Calculates Stability (S), Difficulty (D), and Retrievability (R) to schedule flashcard reviews at optimal forgetting curve thresholds.

---

## 4. Technology Stack (Categorized)

### 4.1 Languages & Runtimes
| Technology | Version | Role |
|:-----------|:--------|:-----|
| Python | 3.11+ | Backend: pipeline, API, models, ingestion workers |
| JavaScript (ES6+) | Modern | Frontend: React SPA UI, interactive canvas, polling |
| Node.js | v20 LTS | Build tooling for Vite |
| HTML5 & CSS3 | Modern | Semantic structure, dark-mode glassmorphism styling |

### 4.2 Backend Frameworks
| Tool | Version | Role |
|:-----|:--------|:-----|
| FastAPI | ≥0.110.0 | Async REST API framework |
| Uvicorn | ≥0.28.0 | ASGI server |
| Pydantic & Pydantic-Settings | ≥2.6.0 | Schema validation, typed contracts, env parsing |
| SQLAlchemy | ≥2.0.28 | Async ORM for SQLite |
| aiosqlite | ≥0.20.0 | Async SQLite driver |

### 4.3 Frontend Frameworks
| Tool | Version | Role |
|:-----|:--------|:-----|
| React | ^18.2.0 | Declarative component-based UI |
| Vite | ^5.0.0 | Fast dev server + HMR + production bundler |
| Lucide React | ^0.359.0 | Icon set |

### 4.4 Databases & Storage
| Engine | Type | Role |
|:-------|:-----|:-----|
| Qdrant | v1.8.4 (Vector DB) | Stores 384-dim dense embeddings for `kb_chunks` and `learner_traces` collections |
| SQLite (aiosqlite) | Relational | User profiles, documents, pages, chat turns, BKT mastery state, review cards |
| Neo4j | 5.20-community (Graph DB) | Cypher-based concept prerequisite graph, Louvain communities |
| NetworkX | In-Memory Graph | Zero-config fallback DAG when Neo4j is offline |
| Local File Storage | Persistent Volume | Uploaded docs, rendered page PNGs, audio |

### 4.5 Ingestion & Parsing
| Library | Version | Role |
|:--------|:--------|:-----|
| PyMuPDF (fitz) | ≥1.24.0 | PDF parsing + high-res page rasterization |
| PyMuPDF4LLM | ≥0.0.17 | Markdown/table/formula extraction from PDFs |
| Docling | ≥2.0.0 | Advanced layout analysis for multi-column papers and slides |
| Trafilatura | ≥1.8.0 | Web scraping — clean article text from URLs |
| yt-dlp | ≥2024.3.10 | YouTube transcript and subtitle extraction |

### 4.6 Embeddings, Search & Reranking (RAG Core)
| Component | Model / Spec | Role |
|:----------|:-------------|:-----|
| FastEmbed | ≥0.2.6 | Local ONNX embedding inference on CPU |
| BAAI/bge-small-en-v1.5 | 384-dim | Dense embedding model |
| Rank-BM25 | ≥0.2.2 | Okapi BM25 sparse lexical search |
| RRF (Reciprocal Rank Fusion) | k=60 | Fuses dense + sparse ranking lists |
| BGE-Reranker v2-m3 | Cross-encoder | Neural reranking of top candidates |

### 4.7 AI & LLM
| Service | Integration | Role |
|:--------|:------------|:-----|
| Google Gemini API | `google-genai` + `google-generativeai` | Core intelligence: intent analysis, concept extraction, grounded tutoring, claim verification |
| Models Used | `gemini-2.5-flash` / `gemini-3.8-flash` | Fast, cost-effective reasoning |
| Ollama (optional fallback) | Local LLM client | Offline resilience |
| Structured JSON Outputs | Pydantic schemas | Typed contracts for TutorPlan, IntentResult, VerificationReport |

### 4.8 Cognitive & Pedagogical Algorithms
| Algorithm | Theory | Role |
|:----------|:-------|:-----|
| Bayesian Knowledge Tracing (BKT) | P(L_t) updates with slip & guess | Real-time per-concept mastery tracking |
| FSRS | Difficulty, Stability, Retrievability | Optimal spaced repetition scheduling |
| Zone of Proximal Development (ZPD) | Vygotskian scaffolding | Reranking content to Target = P(L_t) + 0.15 |
| Root-Cause Prerequisite Traversal | Graph BFS/DAG | Diagnoses upstream knowledge gaps |
| Deterministic Tutor Planner | Cognitive policy engine | Selects pedagogical action based on diagnosis |

### 4.9 Observability & Evaluation
| Tool | Role |
|:-----|:-----|
| Langfuse (≥2.0.0) | LLM observability: latency, tokens, faithfulness tracing |
| RAGAS (≥0.1.0) | RAG evaluation: context relevance, answer faithfulness |

### 4.10 DevOps & Infrastructure
| Tool | Role |
|:-----|:-----|
| Docker | Multi-stage hardened containers (non-root) |
| Docker Compose (v3.8) | Orchestrates Frontend (Nginx:3000), Backend (FastAPI:8000), Qdrant (6333/6334) |
| Nginx (alpine-slim) | Static file server + reverse proxy for `/api/`, `/storage/`, `/ws` |
| GitHub Actions | CI: Python tests, frontend build validation, compose checks |

---

## 5. Codebase Structure (File Map)

```
aistudybuddy/
├── README.md                          # Project overview & architecture diagrams
├── TOOLS.md                           # Complete technology inventory
├── CONTRIBUTING.md                    # Dev workflow & PR guidelines
├── CODE_OF_CONDUCT.md                 # Community standards
├── SECURITY.md                        # Security policy
├── LICENSE                            # MIT License
├── context.md                         # ← This file (full project context)
├── .env.example                       # Environment variable template
├── .gitignore                         # Git exclusion rules
├── docker-compose.yml                 # 3-service stack orchestration
│
├── backend/
│   ├── Dockerfile                     # Multi-stage Python container
│   ├── requirements.txt               # 50+ Python dependencies
│   ├── requirements-dev.txt           # Dev/test extras
│   ├── pyproject.toml                 # Python project metadata
│   ├── run_server.py                  # Dev server entry point
│   ├── seed_kb.py                     # Knowledge base seeder script
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory + lifespan + router mounts
│   │   │
│   │   ├── core/                      # Shared infrastructure layer
│   │   │   ├── config.py              # Pydantic-Settings configuration (env vars)
│   │   │   ├── db.py                  # SQLAlchemy async engine + session factory
│   │   │   ├── models.py             # 9 ORM models (User, Document, Chunk, Concept, etc.)
│   │   │   ├── embeddings.py          # FastEmbed BGE ONNX wrapper
│   │   │   ├── vector_db.py           # Qdrant client (kb_chunks + learner_traces)
│   │   │   ├── graph_db.py            # Neo4j + NetworkX dual graph store
│   │   │   ├── gemini_client.py       # Google Gemini API client
│   │   │   ├── llm_client.py          # Unified LLM abstraction layer
│   │   │   ├── ollama_client.py       # Legacy Ollama fallback client
│   │   │   ├── reranker.py            # BGE cross-encoder reranker
│   │   │   └── telemetry.py           # Langfuse observability manager
│   │   │
│   │   ├── pipeline/                  # Three-phase processing pipeline
│   │   │   ├── offline/               # Phase 1: Ingestion
│   │   │   │   ├── parser.py          # Dual-engine PDF/document parser
│   │   │   │   ├── chunker.py         # Contextual hierarchical chunker
│   │   │   │   ├── graph_extractor.py # Gemini-powered concept & relation extractor
│   │   │   │   └── indexer.py         # Atomic multi-store indexer (Qdrant + BM25 + Graph)
│   │   │   │
│   │   │   ├── online/                # Phase 2: 12-Step Tutoring Pipeline
│   │   │   │   ├── coordinator.py     # Pipeline orchestrator (chains all 12 steps)
│   │   │   │   ├── memory.py          # Session memory (SQLite + Qdrant traces)
│   │   │   │   ├── intent.py          # Gemini intent & difficulty classifier
│   │   │   │   ├── learner_overlay.py # BKT mastery state lookup
│   │   │   │   ├── root_cause.py      # Graph DAG prerequisite gap analysis
│   │   │   │   ├── retriever.py       # Hybrid RRF retriever (Qdrant + BM25)
│   │   │   │   ├── context_builder.py # Context pruner & XML formatter
│   │   │   │   ├── planner.py         # Deterministic tutor policy selector
│   │   │   │   ├── writer.py          # Grounded generation with system-prompt scaffolding
│   │   │   │   ├── verifier.py        # Structured claim-level fact checker
│   │   │   │   ├── leak_filter.py     # Security: prompt leak & guardrail filter
│   │   │   │   └── fallback.py        # Graceful degradation handler
│   │   │   │
│   │   │   └── closed_loop/           # Phase 3: Mastery & Review
│   │   │       ├── assessment.py      # Practice question generation
│   │   │       ├── state_update.py    # BKT mastery state transitions
│   │   │       └── fsrs_scheduler.py  # FSRS spaced repetition scheduler
│   │   │
│   │   ├── api/routers/               # REST API endpoints
│   │   │   ├── chat.py                # POST /api/chat — main tutoring endpoint
│   │   │   ├── ingestion.py           # POST /api/ingestion/upload, GET /status/{id}
│   │   │   ├── graph.py               # GET /api/graph/concepts, edges, communities
│   │   │   ├── learner.py             # GET /api/learner/mastery, progress
│   │   │   ├── assessment.py          # POST /api/assessment/generate, /submit
│   │   │   └── review.py             # GET/POST /api/review/cards, /schedule
│   │   │
│   │   └── eval/                      # Evaluation harness
│   │       └── eval_harness.py        # RAGAS-based pipeline evaluation
│   │
│   └── tests/                         # Automated test suites
│       ├── conftest.py                # Shared test fixtures
│       ├── test_unit_core.py          # Core module unit tests
│       ├── test_pipeline.py           # Pipeline integration tests
│       ├── test_graphrag_rrf_pipeline.py  # GraphRAG + RRF verification
│       ├── test_image_and_memory.py   # Image processing & memory tests
│       ├── test_evaluation_and_ops.py # Eval harness & ops tests
│       └── verify_enhanced_ingestion.py # Enhanced ingestion verification
│
├── frontend/
│   ├── Dockerfile                     # Nginx-based static build container
│   ├── nginx.conf                     # Reverse proxy config (/api → backend:8000)
│   ├── package.json                   # React 18 + Vite 5 + Lucide
│   ├── vite.config.js                 # Vite dev/build configuration
│   ├── index.html                     # HTML entry point
│   │
│   └── src/
│       ├── main.jsx                   # React app mount point
│       ├── App.jsx                    # Root app: routing, state, layout
│       ├── index.css                  # Global styles: dark mode, glassmorphism, animations
│       │
│       └── components/                # 18 React UI components
│           ├── Header.jsx             # App header with branding & nav
│           ├── Navbar.jsx             # Navigation bar
│           ├── Sidebar.jsx            # Document library & session sidebar
│           ├── HomeView.jsx           # Landing/home page view
│           ├── ChatPanel.jsx          # Real-time chat with tutor
│           ├── ChatWorkspace.jsx      # Chat workspace layout (chat + evidence + sources)
│           ├── EvidencePanel.jsx      # Retrieved evidence/citation display
│           ├── SourcesPanel.jsx       # Source document references
│           ├── ConceptGraphCanvas.jsx # Interactive prerequisite DAG visualization
│           ├── PageInspector.jsx      # Rendered page image inspector
│           ├── LearnerDashboard.jsx   # BKT mastery overview dashboard
│           ├── LearningProgressView.jsx # Detailed learning progress & analytics
│           ├── StudyToolsView.jsx     # Study tools hub (flashcards, notes, summaries)
│           ├── UploadModal.jsx        # Document upload with live progress
│           ├── PracticeModal.jsx      # Interactive practice/quiz modal
│           ├── SpacedReviewModal.jsx  # FSRS spaced review flashcard modal
│           ├── SettingsModal.jsx      # App settings configuration
│           └── CommandPalette.jsx     # Keyboard-driven command palette
│
├── data/                              # Persistent data directory
│
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md       # PR template
    ├── ISSUE_TEMPLATE/                # Issue templates
    └── workflows/                     # GitHub Actions CI pipeline
```

---

## 6. Data Models (SQLite ORM Schema)

The application maintains **9 core database tables** via SQLAlchemy ORM:

| Model | Table | Purpose | Key Fields |
|:------|:------|:--------|:-----------|
| **User** | `users` | Student profiles | `id`, `name`, `email` |
| **Document** | `documents` | Ingested course materials | `id`, `title`, `source_type` (pdf/web/youtube), `status`, `total_pages` |
| **PageImage** | `page_images` | Rendered page previews | `document_id`, `page_number`, `image_path`, `has_diagrams`, `has_equations` |
| **Chunk** | `chunks` | Text chunks with embeddings | `document_id`, `section_title`, `content`, `contextual_line`, `difficulty_score`, `primary_concepts` |
| **Concept** | `concepts` | Knowledge graph nodes | `name`, `description`, `domain`, `base_difficulty` |
| **PrerequisiteEdge** | `prerequisite_edges` | Concept dependency edges | `source_concept_id` → `target_concept_id`, `strength` |
| **Misconception** | `misconceptions` | Common student wrong beliefs | `concept_id`, `name`, `description`, `refutation_strategy` |
| **LearnerMastery** | `learner_mastery` | BKT state per concept per user | `user_id`, `concept_id`, `p_mastery`, `uncertainty`, `total_attempts`, `correct_attempts`, `hints_used`, `active_misconceptions` |
| **InteractionTrace** | `interaction_traces` | Episodic memory & telemetry | `user_id`, `session_id`, `user_query`, `tutor_response`, `intent_type`, `planner_action`, `citations`, `faithfulness_score`, `latency_ms` |
| **ReviewCard** | `review_cards` | FSRS flashcards | `user_id`, `concept_id`, `question`, `answer`, `stability`, `difficulty`, `scheduled_days`, `state` (New/Learning/Review/Relearning) |

---

## 7. API Surface (REST Endpoints)

All endpoints are served under the `/api` prefix via FastAPI.

| Method | Endpoint | Purpose |
|:-------|:---------|:--------|
| `GET` | `/api/health` | Health check — returns brain status, graph stats, version |
| `POST` | `/api/chat` | Main tutoring endpoint — runs the 12-step pipeline |
| `POST` | `/api/ingestion/upload` | Upload document → returns `job_id` (202 Accepted) |
| `GET` | `/api/ingestion/status/{job_id}` | Poll ingestion progress (10%→30%→55%→80%→100%) |
| `GET` | `/api/graph/concepts` | Retrieve all concepts in the knowledge graph |
| `GET` | `/api/graph/edges` | Retrieve all prerequisite relationships |
| `GET` | `/api/graph/communities` | Retrieve Louvain community summaries |
| `GET` | `/api/learner/mastery` | Get student's BKT mastery state for all concepts |
| `GET` | `/api/learner/progress` | Get learning analytics and progress data |
| `POST` | `/api/assessment/generate` | Generate diagnostic practice questions |
| `POST` | `/api/assessment/submit` | Submit answers and trigger BKT state update |
| `GET` | `/api/review/cards` | Get due flashcards from FSRS scheduler |
| `POST` | `/api/review/schedule` | Record review result and reschedule card |

Static files (page images, uploads) are served via `/storage/` mount.

---

## 8. Key Algorithms — Mathematical Formulations

### 8.1 Bayesian Knowledge Tracing (BKT)

BKT maintains a per-concept mastery probability P(L_t) for each student:

**On correct answer:**
```
P(L_t | correct) = P(L_t) * (1 - P(S)) / [P(L_t) * (1 - P(S)) + (1 - P(L_t)) * P(G)]
```

**On incorrect answer:**
```
P(L_t | incorrect) = P(L_t) * P(S) / [P(L_t) * P(S) + (1 - P(L_t)) * (1 - P(G))]
```

**Learning transition:**
```
P(L_{t+1}) = P(L_t | evidence) + (1 - P(L_t | evidence)) * P(T)
```

Where:
- **P(S)** = Slip probability (knowing but answering wrong)
- **P(G)** = Guess probability (not knowing but guessing right)
- **P(T)** = Transition probability (learning rate)

### 8.2 Reciprocal Rank Fusion (RRF)

Fuses ranking lists from dense vector search, sparse BM25, and graph community hits:

```
RRF_score(d) = Σ 1 / (k + rank_i(d))    where k = 60
```

### 8.3 ZPD-Calibrated Reranking

Content difficulty is matched to the student's zone of proximal development:

```
Target_Difficulty = P(L_t) + 0.15
Final_Score = Relevance_Score * (1 - |chunk_difficulty - Target_Difficulty|)
```

### 8.4 FSRS Spaced Repetition

Three core parameters maintained per flashcard:
- **S** (Stability): Interval at which retrievability drops to 90%
- **D** (Difficulty): Inherent card difficulty on a 1–10 scale
- **R** (Retrievability): Current probability the student remembers the card

```
R(t) = (1 + t / (9 * S))^(-1)
```

Cards are scheduled for review when R drops below a configurable threshold.

---

## 9. Key Design Decisions & Differentiators

1. **Learner-state-aware retrieval**: Unlike standard RAG, retrieval results are not just ranked by relevance — they are reranked by the student's current mastery level to serve content in the Zone of Proximal Development.

2. **Prerequisite-aware gap diagnosis**: Before answering any question, the system traverses the knowledge graph backwards to check if the student has unmastered prerequisites. If so, it automatically remediates the foundational gap first.

3. **Structured claim verification**: Every LLM response is post-processed through a structured claim verifier (Temp=0.0) that extracts atomic factual claims and checks each against the source evidence, producing a faithfulness score.

4. **Deterministic pedagogical planning**: The tutor doesn't just "answer questions" — it selects from 6 pedagogical strategies (EXPLAIN, SOCRATIC, HINT, REMEDIATE, WORKED_EXAMPLE, QUIZ) based on student mastery state, intent type, and prerequisite diagnosis.

5. **Dual-parser ingestion**: Two separate document parsing engines (PyMuPDF for speed + Docling for complex layouts) ensure robust handling of diverse academic materials.

6. **GraphRAG + Hybrid Search**: Combines traditional vector RAG with graph-based prerequisite retrieval and Louvain community summaries for richer context.

7. **Asynchronous non-blocking ingestion**: Upload returns immediately (202 Accepted) while heavy parsing, embedding, and graph extraction run in background workers with live progress polling.

8. **Graceful degradation**: Neo4j falls back to NetworkX, Qdrant can run embedded, Gemini falls back to Ollama — the system adapts to available infrastructure.

---

## 10. Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Docker Compose                     │
│                                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────┐ │
│  │  Frontend    │   │   Backend    │   │  Qdrant   │ │
│  │  (Nginx)     │──▶│  (FastAPI)   │──▶│ (Vector)  │ │
│  │  Port: 3000  │   │  Port: 8000  │   │ Port:6333 │ │
│  │  React SPA   │   │  Python 3.11 │   │ v1.8.4    │ │
│  └─────────────┘   └──────────────┘   └───────────┘ │
│                           │                          │
│                     ┌─────┴─────┐                    │
│                     │  SQLite   │                    │
│                     │  (Async)  │                    │
│                     └───────────┘                    │
│                           │                          │
│                    ┌──────┴───────┐                   │
│                    │ Neo4j (Opt.) │                   │
│                    │ / NetworkX   │                   │
│                    └──────────────┘                   │
└──────────────────────────────────────────────────────┘
```

| Service | Container | Port | Image |
|:--------|:----------|:-----|:------|
| Frontend | `studybuddy-frontend` | 3000 → 80 | Custom Nginx + React build |
| Backend | `studybuddy-backend` | 8000 | Custom Python 3.11 |
| Vector DB | `studybuddy-qdrant` | 6333, 6334 | `qdrant/qdrant:v1.8.4` |

All services communicate over an isolated Docker bridge network (`studybuddy-net`) with persistent named volumes for data durability.

---

## 11. Environment Configuration

Key environment variables (from `.env`):

| Variable | Default | Purpose |
|:---------|:--------|:--------|
| `GEMINI_API_KEY` | (required) | Google Gemini API authentication |
| `GEMINI_MODEL` | `gemini-2.5-flash` | LLM model selection |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/studybuddy.db` | Relational DB path |
| `QDRANT_URL` | `""` (embedded) | Qdrant server URL (empty = local embedded) |
| `QDRANT_PATH` | `./data/qdrant_db` | Embedded Qdrant storage path |
| `NEO4J_URI` | `bolt://localhost:7687` | Optional Neo4j connection |
| `LANGFUSE_ENABLED` | `false` | Enable/disable observability |
| `STORAGE_DIR` | `./data/storage` | File upload storage directory |

---

## 12. Testing Strategy

The project maintains multiple test suites:

| Test File | Scope | What It Validates |
|:----------|:------|:------------------|
| `test_unit_core.py` | Unit | Core modules: config, embeddings, models |
| `test_pipeline.py` | Integration | Full 12-step pipeline end-to-end |
| `test_graphrag_rrf_pipeline.py` | Integration | GraphRAG extraction + RRF fusion |
| `test_image_and_memory.py` | Integration | Image processing + episodic memory |
| `test_evaluation_and_ops.py` | Integration | RAGAS evaluation harness + ops |
| `verify_enhanced_ingestion.py` | Verification | Enhanced dual-parser ingestion flow |

Run tests:
```bash
pytest backend/tests/test_unit_core.py backend/tests/test_pipeline.py -v
python backend/tests/verify_enhanced_ingestion.py
```

---

## 13. Quick Start

```bash
# 1. Clone and configure
git clone <repo_url>
cp .env.example .env
# Edit .env → add your GEMINI_API_KEY

# 2. Launch all services
docker compose up -d

# 3. Access
# Student UI:     http://localhost:3000
# API Docs:       http://localhost:8000/docs
# Qdrant Dashboard: http://localhost:6333/dashboard
```

---

## 14. Frontend UI Components (18 Components)

| Component | Purpose |
|:----------|:--------|
| **Header** | App branding, navigation, and global actions |
| **Navbar** | Primary navigation bar |
| **Sidebar** | Document library, session management, and quick actions |
| **HomeView** | Landing page with getting-started guidance |
| **ChatPanel** | Real-time streaming chat with the AI tutor |
| **ChatWorkspace** | Composite layout: chat + evidence panel + sources panel |
| **EvidencePanel** | Displays retrieved evidence chunks with citations |
| **SourcesPanel** | Shows source documents referenced in the response |
| **ConceptGraphCanvas** | Interactive force-directed graph visualization of the concept prerequisite DAG |
| **PageInspector** | Zoom/pan viewer for rendered document page images |
| **LearnerDashboard** | Overview of BKT mastery scores across all concepts |
| **LearningProgressView** | Detailed analytics: mastery trends, practice history, strengths/weaknesses |
| **StudyToolsView** | Hub for flashcards, summaries, notes, and AI-generated study materials |
| **UploadModal** | Drag-and-drop document upload with live progress bar |
| **PracticeModal** | Interactive MCQ/open-ended practice sessions |
| **SpacedReviewModal** | FSRS flashcard review with difficulty rating |
| **SettingsModal** | Configuration: model selection, theme, telemetry |
| **CommandPalette** | Keyboard shortcut-driven command palette (Cmd+K) |

---

## 15. Summary for Report / PPT Use

### One-Liner
> AI Study Buddy is a learner-state-aware RAG platform that combines Bayesian Knowledge Tracing, hybrid vector/lexical retrieval, prerequisite graph analysis, and adaptive pedagogical planning to deliver personalized, hallucination-verified educational tutoring.

### Key Contributions (for academic framing)
1. **Novel integration** of BKT cognitive modeling with RAG retrieval pipelines.
2. **ZPD-calibrated reranking** that adapts content difficulty to the student's evolving mastery.
3. **Prerequisite-aware gap diagnosis** via knowledge graph DAG traversal before answering.
4. **Structured claim verification** pipeline for LLM hallucination elimination.
5. **Closed-loop learning** with FSRS spaced repetition driven by real-time mastery updates.

### Suggested PPT Slide Titles
1. Title Slide: "AI Study Buddy — Learner-State-Aware RAG Platform"
2. Problem Statement: Why One-Size-Fits-All Tutoring Fails
3. System Architecture Overview (3-Phase Diagram)
4. Phase 1: Multimodal Document Ingestion Pipeline
5. Phase 2: The 12-Step Pedagogical Pipeline
6. Bayesian Knowledge Tracing — How We Model Learning
7. Hybrid RAG: Dense + Sparse + Graph Retrieval
8. ZPD-Calibrated Reranking — Teaching at the Right Level
9. Hallucination Prevention: Structured Claim Verification
10. Phase 3: Closed-Loop Mastery & FSRS Spaced Repetition
11. Technology Stack & Tool Combination Matrix
12. Frontend: Interactive Student Dashboard
13. Deployment Architecture (Docker Compose)
14. Demo / Screenshots
15. Results, Evaluation & Future Work
16. Q&A

---

## 16. Glossary

| Term | Definition |
|:-----|:-----------|
| **RAG** | Retrieval-Augmented Generation — grounding LLM outputs in retrieved evidence |
| **BKT** | Bayesian Knowledge Tracing — probabilistic model of student concept mastery |
| **FSRS** | Free Spaced Repetition Scheduler — modern algorithm for memory retention |
| **ZPD** | Zone of Proximal Development — Vygotskian theory of optimal learning difficulty |
| **RRF** | Reciprocal Rank Fusion — algorithm for merging multiple ranked lists |
| **GraphRAG** | Graph-enhanced RAG using knowledge graphs for structured retrieval |
| **DAG** | Directed Acyclic Graph — structure modeling concept prerequisite dependencies |
| **BM25** | Best Matching 25 — classic probabilistic information retrieval algorithm |
| **Cross-Encoder** | Neural model that jointly encodes query + document for fine-grained relevance |
| **Louvain** | Community detection algorithm for clustering nodes in graphs |

---

*This document was generated on 2026-10-27 and reflects the current state of the AI Study Buddy codebase.*
