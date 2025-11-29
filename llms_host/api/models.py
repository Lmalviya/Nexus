"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AgentRequest(BaseModel):
    """Base request model for agent endpoints."""
    session_id: str  # Changed from conversation_id for consistency
    llm_config: Optional[Dict[str, Any]] = Field(None, description="Optional override for LLM config")


class RewriteRequest(AgentRequest):
    """Request model for query rewriting."""
    user_query: str
    additional_context: Optional[str] = None


class SummarizeRequest(AgentRequest):
    """Request model for conversation summarization."""
    messages: List[Dict[str, Any]]


class DescriptionRequest(AgentRequest):
    """Request model for content description (table or image)."""
    content_type: str
    data: Dict[str, Any]


class ChatRequest(AgentRequest):
    """Request model for general chat."""
    user_message: str
    images: Optional[List[str]] = None
    additional_context: Optional[str] = None


class RetrievalDecisionRequest(AgentRequest):
    """Request model for retrieval decision."""
    user_query: str
    additional_context: Optional[str] = None


class RouterRequest(AgentRequest):
    """Request model for RAG routing decision."""
    user_query: str
    retrieved_context: List[str]


class SQLRequest(AgentRequest):
    """Request model for SQL query generation."""
    user_query: str
    context: List[str]


class EmbeddingRequest(BaseModel):
    """Request model for embeddings."""
    texts: Optional[List[str]] = None
    images: Optional[List[str]] = None  # Base64 strings
