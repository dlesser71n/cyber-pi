"""
TQAKB V4 Event Schemas
Defines all event types and data structures for the knowledge pipeline
"""

from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import uuid

# Event Types
class EventType(str, Enum):
    """Core event types in the knowledge pipeline"""
    KNOWLEDGE_RAW = "knowledge.raw"
    KNOWLEDGE_VALIDATED = "knowledge.validated"
    KNOWLEDGE_ENRICHED = "knowledge.enriched"
    KNOWLEDGE_QUERY = "knowledge.query"
    KNOWLEDGE_FEEDBACK = "knowledge.feedback"
    SYSTEM_METRIC = "system.metric"
    SYSTEM_ERROR = "system.error"
    SYSTEM_AUDIT = "system.audit"

class SourceType(str, Enum):
    """Source systems that generate events"""
    USER = "user"
    API = "api"
    WEB_CRAWLER = "web_crawler"
    FILE_IMPORT = "file_import"
    STREAM = "stream"
    NEO4J = "neo4j"
    WEAVIATE = "weaviate"
    REDIS = "redis"
    KAFKA = "kafka"
    OLLAMA = "ollama"
    VALIDATION_ENGINE = "validation_engine"
    ENRICHMENT_SERVICE = "enrichment_service"

class ConfidenceLevel(float, Enum):
    """Standard confidence levels"""
    CERTAIN = 1.0
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    UNCERTAIN = 0.3

# Base Event Schema
class BaseEvent(BaseModel):
    """Base schema for all events in the system"""
    
    # Required fields
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event ID")
    type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event creation time")
    source: SourceType = Field(..., description="System that generated this event")
    
    # Optional metadata
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    version: str = Field(default="4.0.0", description="Schema version")
    
    # Tracing
    correlation_id: Optional[str] = Field(default=None, description="For tracing related events")
    parent_id: Optional[str] = Field(default=None, description="Parent event ID")
    user_id: Optional[str] = Field(default=None, description="User who triggered the event")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Knowledge Events
class KnowledgeContent(BaseModel):
    """Content structure for knowledge events"""
    subject: str = Field(..., description="Subject of the knowledge")
    predicate: str = Field(..., description="Relationship or property")
    object: str = Field(..., description="Object or value")
    context: Optional[str] = Field(default=None, description="Context or domain")
    temporal: Optional[Dict[str, Any]] = Field(default=None, description="Temporal information")
    spatial: Optional[Dict[str, Any]] = Field(default=None, description="Spatial information")
    
class KnowledgeEvent(BaseEvent):
    """Event for knowledge data"""
    content: KnowledgeContent = Field(..., description="Knowledge content")
    embeddings: Optional[List[float]] = Field(default=None, description="Vector embeddings")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = [EventType.KNOWLEDGE_RAW, EventType.KNOWLEDGE_VALIDATED, EventType.KNOWLEDGE_ENRICHED]
        if v not in allowed:
            raise ValueError(f"Type must be one of {allowed}")
        return v

# Query Events
class QueryContent(BaseModel):
    """Content structure for query events"""
    query: str = Field(..., description="Query text")
    intent: Optional[str] = Field(default=None, description="Detected intent")
    entities: Optional[List[Dict[str, Any]]] = Field(default=None, description="Extracted entities")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Query filters")
    limit: int = Field(default=10, ge=1, le=100, description="Result limit")
    
class QueryEvent(BaseEvent):
    """Event for search queries"""
    type: Literal[EventType.KNOWLEDGE_QUERY] = EventType.KNOWLEDGE_QUERY
    content: QueryContent = Field(..., description="Query content")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Query results")

# Feedback Events
class FeedbackContent(BaseModel):
    """Content structure for feedback events"""
    target_id: str = Field(..., description="ID of the item being rated")
    rating: float = Field(..., ge=0.0, le=1.0, description="Feedback rating")
    comment: Optional[str] = Field(default=None, description="Feedback comment")
    action: Optional[str] = Field(default=None, description="User action")
    
class FeedbackEvent(BaseEvent):
    """Event for user feedback"""
    type: Literal[EventType.KNOWLEDGE_FEEDBACK] = EventType.KNOWLEDGE_FEEDBACK
    content: FeedbackContent = Field(..., description="Feedback content")

# System Events
class MetricContent(BaseModel):
    """Content structure for metric events"""
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(default=None, description="Metric unit")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")
    
class MetricEvent(BaseEvent):
    """Event for system metrics"""
    type: Literal[EventType.SYSTEM_METRIC] = EventType.SYSTEM_METRIC
    content: MetricContent = Field(..., description="Metric content")

class ErrorContent(BaseModel):
    """Content structure for error events"""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    
class ErrorEvent(BaseEvent):
    """Event for system errors"""
    type: Literal[EventType.SYSTEM_ERROR] = EventType.SYSTEM_ERROR
    content: ErrorContent = Field(..., description="Error content")

class AuditContent(BaseModel):
    """Content structure for audit events"""
    action: str = Field(..., description="Audit action")
    resource: str = Field(..., description="Resource affected")
    result: str = Field(..., description="Action result")
    details: Dict[str, Any] = Field(default_factory=dict, description="Audit details")
    
class AuditEvent(BaseEvent):
    """Event for audit logging"""
    type: Literal[EventType.SYSTEM_AUDIT] = EventType.SYSTEM_AUDIT
    content: AuditContent = Field(..., description="Audit content")

# Response Models
class HealthStatus(BaseModel):
    """Health check response"""
    service: str
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Search result item"""
    id: str
    score: float
    content: Dict[str, Any]
    source: str
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[SearchResult]
    total: int
    took_ms: float
    metadata: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    """Validation result"""
    is_valid: bool
    confidence: float
    reasons: List[str]
    suggestions: Optional[List[str]] = None

class EnrichmentResult(BaseModel):
    """Enrichment result"""
    original: Dict[str, Any]
    enriched: Dict[str, Any]
    added_fields: List[str]
    confidence: float

# Batch Processing
class BatchRequest(BaseModel):
    """Batch processing request"""
    events: List[BaseEvent]
    processing_mode: Literal["parallel", "sequential"] = "parallel"
    continue_on_error: bool = True

class BatchResponse(BaseModel):
    """Batch processing response"""
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]] = None