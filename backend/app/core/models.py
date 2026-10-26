import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), default="Student")
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    masteries = relationship("LearnerMastery", back_populates="user", cascade="all, delete-orphan")
    traces = relationship("InteractionTrace", back_populates="user", cascade="all, delete-orphan")
    review_cards = relationship("ReviewCard", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), default="pdf") # pdf, web, youtube, note
    source_url = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=True)
    total_pages = Column(Integer, default=1)
    status = Column(String(50), default="processed") # pending, processing, indexed, error
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship("PageImage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class PageImage(Base):
    __tablename__ = "page_images"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, default="")
    has_diagrams = Column(Boolean, default=False)
    has_equations = Column(Boolean, default=False)

    document = relationship("Document", back_populates="pages")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, default=1)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String(255), default="")
    content = Column(Text, nullable=False)
    contextual_line = Column(Text, default="") # LLM prepended context line
    difficulty_score = Column(Float, default=0.5) # 0.0 to 1.0 (easy to advanced)
    token_count = Column(Integer, default=0)
    primary_concepts = Column(JSON, default=list) # List of extracted concept names
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")

class Concept(Base):
    __tablename__ = "concepts"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    domain = Column(String(100), default="General")
    base_difficulty = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)

    misconceptions = relationship("Misconception", back_populates="concept", cascade="all, delete-orphan")
    masteries = relationship("LearnerMastery", back_populates="concept", cascade="all, delete-orphan")

class PrerequisiteEdge(Base):
    __tablename__ = "prerequisite_edges"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False) # Prerequisite
    target_concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False) # Advanced concept
    strength = Column(Float, default=1.0) # 0.0 to 1.0

class Misconception(Base):
    __tablename__ = "misconceptions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    refutation_strategy = Column(Text, default="")

    concept = relationship("Concept", back_populates="misconceptions")

class LearnerMastery(Base):
    """
    Bayesian Knowledge Tracing (BKT) State per concept per user.
    P(L_k): probability of mastery.
    """
    __tablename__ = "learner_mastery"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False, index=True)
    
    # BKT State
    p_mastery = Column(Float, default=0.20) # P(L) initial prior
    uncertainty = Column(Float, default=0.40) # Variance/uncertainty
    
    # Practice stats
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    active_misconceptions = Column(JSON, default=list) # Detected active wrong beliefs
    last_practiced_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="masteries")
    concept = relationship("Concept", back_populates="masteries")

class InteractionTrace(Base):
    """
    Episodic memory trace for session replay, learner overlay history & evaluation.
    """
    __tablename__ = "interaction_traces"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_query = Column(Text, nullable=False)
    tutor_response = Column(Text, nullable=False)
    
    # Pipeline Metadata
    intent_type = Column(String(50), default="conceptual")
    target_concepts = Column(JSON, default=list)
    diagnosed_weak_concept = Column(String(100), nullable=True)
    planner_action = Column(String(50), default="explain") # explain, hint, socratic, remediate, quiz
    citations = Column(JSON, default=list) # [{doc_id, page, snippet, score}]
    claims_verified = Column(Boolean, default=True)
    faithfulness_score = Column(Float, default=1.0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="traces")

class ReviewCard(Base):
    """
    FSRS (Free Spaced Repetition Scheduler) Flashcards.
    """
    __tablename__ = "review_cards"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, default="")
    
    # FSRS parameters
    stability = Column(Float, default=1.0)
    difficulty = Column(Float, default=5.0) # 1.0 to 10.0
    elapsed_days = Column(Integer, default=0)
    scheduled_days = Column(Integer, default=1)
    reps = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    state = Column(Integer, default=0) # 0: New, 1: Learning, 2: Review, 3: Relearning
    due_at = Column(DateTime, default=datetime.utcnow)
    last_review_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="review_cards")
