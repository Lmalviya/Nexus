"""RAG Pipeline API endpoints router."""

from fastapi import APIRouter, HTTPException
import logging
import base64
import io
from PIL import Image

from rag_pipline.api.models import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    TextRetrievalRequest,
    ImageRetrievalRequest,
    RetrievalResponse,
    DocumentDeleteRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(request: DocumentUploadRequest):
    """
    Upload and process a document to the vector database.
    """
    try:
        from rag_pipline.document_pipeline import DocumentPipeline
        
        pipeline = DocumentPipeline()
        result = pipeline.process_document(
            minio_url=request.minio_url,
            user_id=request.user_id,
            org_id=request.org_id,
            use_ocr=request.use_ocr
        )
        
        return DocumentUploadResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in upload_document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve/text", response_model=RetrievalResponse)
async def retrieve_by_text(request: TextRetrievalRequest):
    """
    Retrieve relevant context from vector database using text query.
    """
    try:
        from rag_pipline.retrival.get_context import RetrievalPipeline
        
        pipeline = RetrievalPipeline()
        results = pipeline.get_context(
            user_query=request.user_query,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Limit to top_k results
        limited_results = results[:request.top_k] if results else []
        
        return RetrievalResponse(
            success=True,
            results=limited_results,
            count=len(limited_results)
        )
    
    except Exception as e:
        logger.error(f"Error in retrieve_by_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve/image", response_model=RetrievalResponse)
async def retrieve_by_image(request: ImageRetrievalRequest):
    """
    Retrieve similar images from vector database using image query.
    """
    try:
        from rag_pipline.utils.embeddings import ImageEmbeddings
        from rag_pipline.config import ImageEmbeddingsConfig
        from rag_pipline.utils.db_connection import ConnectionManager
        
        # Decode base64 image
        image_bytes = base64.b64decode(request.image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Generate embedding
        image_embedder = ImageEmbeddings(ImageEmbeddingsConfig())
        embedding = image_embedder.embed_images([image])[0]
        
        # Search in Qdrant
        connection_manager = ConnectionManager()
        qdrant = connection_manager.get_qdrant()
        
        # Search in user's image collection
        collection_name = f"user_{request.user_id}_images"
        search_results = qdrant.client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=request.top_k
        )
        
        # Format results
        results = []
        for hit in search_results:
            results.append({
                "score": hit.score,
                "metadata": hit.payload,
                "id": hit.id
            })
        
        return RetrievalResponse(
            success=True,
            results=results,
            count=len(results)
        )
    
    except Exception as e:
        logger.error(f"Error in retrieve_by_image: {e}")
        return RetrievalResponse(
            count=0
        )


@router.post("/delete")
async def delete_document(request: DocumentDeleteRequest):
    """
    Delete document chunks from vector database.
    """
    try:
        from rag_pipline.utils.db_connection import ConnectionManager
        from qdrant_client.http import models
        
        connection_manager = ConnectionManager()
        qdrant = connection_manager.get_qdrant()
        
        # Delete from text collection
        text_collection = f"user_{request.user_id}_docs"
        try:
            qdrant.client.delete(
                collection_name=text_collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.file_key",
                                match=models.MatchValue(value=request.file_key)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            logger.warning(f"Failed to delete from text collection: {e}")
            
        # Delete from image collection
        image_collection = f"user_{request.user_id}_images"
        try:
            qdrant.client.delete(
                collection_name=image_collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.file_key",
                                match=models.MatchValue(value=request.file_key)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            logger.warning(f"Failed to delete from image collection: {e}")
            
        return {"status": "success", "message": "Document deleted from vector DB"}
        
    except Exception as e:
        logger.error(f"Error in delete_document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
