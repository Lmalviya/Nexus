"""Pydantic models for orchestration service."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatOrchestrationRequest(BaseModel):
    """Request model for chat orchestration."""
    user_message: str = Field(..., description="User's text message")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
    model: Optional[str] = Field(None, description="Selected model ID (e.g., 'gpt-4')")
    provider: Optional[str] = Field(None, description="Provider (e.g., 'openai')")
    api_key: Optional[str] = Field(None, description="User provided API key")
    api_base_url: Optional[str] = Field(None, description="Custom API base URL")
    model_capabilities: Optional[Dict[str, bool]] = Field(None, description="Model capabilities (vision, etc.)")


class ChatOrchestrationResponse(BaseModel):
    """Response model for chat orchestration."""
    response: str = Field(..., description="Chat response text")
    artifact_type: Optional[str] = Field(None, description="code|markdown|diagram")
    artifact_language: Optional[str] = Field(None, description="python|javascript|mermaid|etc")
    artifact_content: Optional[str] = Field(None, description="Artifact content")
    retrieval_used: bool = Field(False, description="Whether retrieval was used")
    retrieval_count: int = Field(0, description="Number of documents retrieved")
    retrieval_sources: Optional[List[str]] = Field(None, description="Document names")
    model_used: Optional[str] = Field(None, description="Model that generated response")
    model_switched: bool = Field(False, description="Whether model was automatically switched")
    switch_reason: Optional[str] = Field(None, description="Reason for model switch")


class DocumentProcessRequest(BaseModel):
    """Request model for document processing."""
    file_key: str = Field(..., description="MinIO file key")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
    session_id: Optional[str] = Field(None, description="Session ID for context")


class DocumentDeleteRequest(BaseModel):
    """Request model for document deletion."""
    file_key: str = Field(..., description="MinIO file key")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
