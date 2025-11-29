"""Pydantic models for RAG pipeline API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DocumentUploadRequest(BaseModel):
    """Request model for uploading documents to vector database."""
    minio_url: str = Field(..., description="MinIO URL of the document")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
    use_ocr: bool = Field(False, description="Whether to use OCR for text extraction")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool
    text_chunks_stored: Optional[int] = None
    images_stored: Optional[int] = None
    text_collection: Optional[str] = None
    image_collection: Optional[str] = None
    error: Optional[str] = None


class TextRetrievalRequest(BaseModel):
    """Request model for text-based retrieval from vector database."""
    user_query: str = Field(..., description="User's search query")
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    top_k: int = Field(5, description="Number of results to return")


class ImageRetrievalRequest(BaseModel):
    """Request model for image-based retrieval from vector database."""
    image_data: str = Field(..., description="Base64 encoded image")
    user_id: str = Field(..., description="User ID")
    top_k: int = Field(5, description="Number of results to return")


class RetrievalResponse(BaseModel):
    """Response model for retrieval operations."""
    success: bool
    results: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    error: Optional[str] = None


class DocumentDeleteRequest(BaseModel):
    """Request model for deleting documents from vector database."""
    file_key: str = Field(..., description="MinIO file key")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
