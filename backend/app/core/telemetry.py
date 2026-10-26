import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class NoopSpan:
    """Safe no-op span fallback when Langfuse is disabled or unconfigured."""
    def __init__(self, name: str = "noop"):
        self.name = name
        self.id = "noop_span_id"

    def span(self, **kwargs):
        return self

    def end(self, **kwargs):
        pass

    def update(self, **kwargs):
        pass

    def score(self, **kwargs):
        pass

class NoopTrace(NoopSpan):
    """Safe no-op trace fallback."""
    def __init__(self, name: str = "noop"):
        super().__init__(name)
        self.id = "noop_trace_id"

class TelemetryManager:
    """
    Production telemetry and LLM observability layer powered by Langfuse.
    Traces every step of the 12-step deterministic tutoring pipeline with zero latency penalty.
    Gracefully degrades to Noop mode if Langfuse is disabled or keys are unconfigured.
    """
    def __init__(self):
        self.client = None
        self.is_enabled = False
        self._init_langfuse()

    def _init_langfuse(self):
        if not settings.LANGFUSE_ENABLED:
            logger.info("Langfuse telemetry explicitly disabled via settings.")
            return

        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            logger.info("Langfuse credentials not set in environment. Running in safe passive telemetry mode.")
            return

        try:
            from langfuse import Langfuse
            self.client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST
            )
            # Lightweight connectivity check
            if hasattr(self.client, "auth_check"):
                auth_ok = self.client.auth_check()
                if auth_ok:
                    self.is_enabled = True
                    logger.info("Connected successfully to Langfuse server at %s", settings.LANGFUSE_HOST)
                else:
                    logger.warning("Langfuse auth_check failed. Running in passive telemetry mode.")
            else:
                self.is_enabled = True
                logger.info("Initialized Langfuse client for host %s", settings.LANGFUSE_HOST)
        except Exception as e:
            logger.warning("Failed to initialize Langfuse client (%s). Telemetry running in passive mode.", str(e))
            self.client = None
            self.is_enabled = False

    def create_trace(
        self,
        name: str,
        user_id: str,
        session_id: str,
        input_query: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Initiates a high-level trace representing a single student turn.
        """
        if not self.is_enabled or not self.client:
            return NoopTrace(name=name)

        try:
            trace = self.client.trace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                input=input_query,
                metadata=metadata or {},
                tags=tags or ["education", "rag", "deterministic-pipeline"]
            )
            return trace
        except Exception as e:
            logger.debug("Telemetry error in create_trace: %s", str(e))
            return NoopTrace(name=name)

    def create_span(
        self,
        parent_trace_or_span: Any,
        name: str,
        input_data: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Creates an execution span for an individual pipeline step.
        """
        if not self.is_enabled or not parent_trace_or_span or isinstance(parent_trace_or_span, NoopSpan):
            return NoopSpan(name=name)

        try:
            if hasattr(parent_trace_or_span, "span"):
                return parent_trace_or_span.span(
                    name=name,
                    input=input_data,
                    metadata=metadata or {}
                )
        except Exception as e:
            logger.debug("Telemetry error in create_span: %s", str(e))
        return NoopSpan(name=name)

    def end_span(
        self,
        span: Any,
        output_data: Any = None,
        level: str = "DEFAULT",
        status_message: Optional[str] = None
    ):
        """
        Concludes a span with resulting output and status.
        """
        if not self.is_enabled or not span or isinstance(span, NoopSpan):
            return

        try:
            if hasattr(span, "end"):
                span.end(
                    output=output_data,
                    level=level,
                    status_message=status_message
                )
        except Exception as e:
            logger.debug("Telemetry error in end_span: %s", str(e))

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None
    ):
        """
        Records a discrete evaluation score into Langfuse for the trace.
        """
        if not self.is_enabled or not self.client or trace_id == "noop_trace_id":
            return

        try:
            self.client.score(
                trace_id=trace_id,
                name=name,
                value=float(value),
                comment=comment
            )
        except Exception as e:
            logger.debug("Telemetry error in log_score: %s", str(e))

    def flush(self):
        """Asynchronously flushes batched events."""
        if not self.is_enabled or not self.client:
            return

        try:
            if hasattr(self.client, "flush"):
                self.client.flush()
        except Exception as e:
            logger.debug("Telemetry error in flush: %s", str(e))

telemetry_manager = TelemetryManager()
