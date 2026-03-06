"""Embedding endpoints router."""

from fastapi import APIRouter, HTTPException
import logging

from llms_host.api.models import EmbeddingRequest
from llms_host.api.dependencies import get_text_embedder, get_image_embedder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])


@router.post("/text")
async def get_text_embeddings(request: EmbeddingRequest):
    """Generate embeddings for text inputs."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        embeddings = get_text_embedder().embed(request.texts)
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Error in get_text_embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def get_image_embeddings(request: EmbeddingRequest):
    """Generate embeddings for image inputs (base64)."""
    if not request.images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    try:
        embeddings = get_image_embedder().embed_from_base64(request.images)
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Error in get_image_embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
