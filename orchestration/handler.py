"""Orchestration handler with /chat, /process-document, and /delete-document endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
import os
import logging
from typing import List, Dict, Any, Optional
from models import (
    ChatOrchestrationRequest, ChatOrchestrationResponse,
    DocumentProcessRequest, DocumentDeleteRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Service URLs from environment
LLMS_HOST_URL = os.getenv("LLMS_HOST_URL", "http://llms_host:8002")
RAG_PIPELINE_URL = os.getenv("RAG_PIPELINE_URL", "http://rag_pipeline:8003")


@router.post("/chat", response_model=ChatOrchestrationResponse)
async def orchestrate_chat(request: ChatOrchestrationRequest):
    """
    Main orchestration endpoint for chat flow.
    """
    logger.info(f"Chat request for session {request.session_id}")
    
    # 1. Resolve Model (Multimodal Check)
    model_config, switch_info = resolve_model_for_multimodal(
        request.model,
        request.provider,
        request.images is not None and len(request.images) > 0,
        request.model_capabilities
    )
    
    # Add API key/base URL if provided
    if request.api_key:
        model_config["api_key"] = request.api_key
    if request.api_base_url:
        model_config["api_base_url"] = request.api_base_url

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # 2. Retrieval Decision
            # We pass the resolved model config so the agent uses the correct model
            retrieval_decision = await call_retrieval_decision(
                client, request.user_message, request.session_id, model_config
            )
            
            needs_retrieval = retrieval_decision.get("needs_retrieval", False)
            logger.info(f"Retrieval decision: {needs_retrieval}")
            
            # 3. Retrieve context if needed
            context = []
            retrieval_count = 0
            retrieval_sources = []
            
            if needs_retrieval:
                # Text retrieval
                if request.user_message:
                    text_results = await call_text_retrieval(
                        client, request.user_message, request.user_id, request.session_id
                    )
                    context.extend(text_results.get("results", []))
                    retrieval_count += text_results.get("count", 0)
                
                # Image retrieval
                if request.images:
                    for img_data in request.images:
                        img_results = await call_image_retrieval(
                            client, img_data, request.user_id
                        )
                        context.extend(img_results.get("results", []))
                        retrieval_count += img_results.get("count", 0)
                
                # Extract source names
                retrieval_sources = [
                    ctx.get("metadata", {}).get("filename", "Unknown")
                    for ctx in context
                ]
            
            # 4. Call chat agent
            context_text = format_context(context) if context else None
            chat_response = await call_chat_agent(
                client,
                request.user_message,
                request.images,
                request.session_id,
                context_text,
                model_config
            )
            
            # 5. Build response
            return ChatOrchestrationResponse(
                response=chat_response.get("response", ""),
                artifact_type=chat_response.get("artifact_type"),
                artifact_language=chat_response.get("artifact_language"),
                artifact_content=chat_response.get("artifact_content"),
                retrieval_used=needs_retrieval,
                retrieval_count=retrieval_count,
                retrieval_sources=retrieval_sources[:5] if retrieval_sources else None,
                model_used=model_config["model"],
                model_switched=switch_info["switched"],
                switch_reason=switch_info["reason"]
            )
            
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-document")
async def process_document(request: DocumentProcessRequest, background_tasks: BackgroundTasks):
    """
    Trigger document processing in RAG pipeline.
    """
    logger.info(f"Processing document: {request.filename} ({request.file_key})")
    
    # We use background tasks to avoid blocking the upload response
    background_tasks.add_task(call_rag_processing, request)
    
    return {"status": "processing_started", "file_key": request.file_key}


@router.post("/delete-document")
async def delete_document(request: DocumentDeleteRequest):
    """
    Delete document from RAG pipeline (vector DB).
    """
    logger.info(f"Deleting document: {request.file_key}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{RAG_PIPELINE_URL}/api/v1/rag/delete",
                json={
                    "file_key": request.file_key,
                    "user_id": request.user_id,
                    "org_id": request.org_id
                }
            )
            response.raise_for_status()
            return {"status": "deleted", "details": response.json()}
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            # We don't raise 500 here to allow partial cleanup (MinIO/DB) to proceed
            return {"status": "failed", "error": str(e)}


# --- Helper Functions ---

def resolve_model_for_multimodal(model: str, provider: str, has_images: bool, capabilities: Optional[Dict[str, bool]]) -> tuple:
    """
    Determines the appropriate model to use, switching to a vision model if needed.
    Returns (model_config, switch_info).
    """
    config = {"model": model, "provider": provider}
    switch_info = {"switched": False, "reason": None}
    
    if not has_images:
        return config, switch_info
        
    # Check if current model supports vision
    supports_vision = False
    if capabilities and capabilities.get("vision"):
        supports_vision = True
    elif "vision" in model.lower() or "llava" in model.lower() or "gpt-4o" in model.lower() or "claude-3" in model.lower():
        # Heuristic fallback if capabilities not provided
        supports_vision = True
        
    if supports_vision:
        return config, switch_info
        
    # Switch needed
    switch_info["switched"] = True
    switch_info["reason"] = f"Model '{model}' does not support vision. Switched to fallback vision model."
    
    # Fallback logic
    if provider == "openai":
        config["model"] = "gpt-4-vision-preview" # Or gpt-4o
    elif provider == "anthropic":
        config["model"] = "claude-3-opus-20240229"
    elif provider == "ollama":
        config["model"] = "llava"
    else:
        # Default fallback
        config["provider"] = "ollama"
        config["model"] = "llava"
        
    return config, switch_info


async def call_rag_processing(request: DocumentProcessRequest):
    """Call RAG pipeline to process document."""
    async with httpx.AsyncClient(timeout=300.0) as client: # Long timeout for processing
        try:
            response = await client.post(
                f"{RAG_PIPELINE_URL}/api/v1/rag/process",
                json=request.dict()
            )
            response.raise_for_status()
            logger.info(f"RAG processing completed for {request.file_key}")
        except Exception as e:
            logger.error(f"RAG processing failed for {request.file_key}: {e}")
            # TODO: Update status in DB to failed via backend callback?


async def call_retrieval_decision(client, query, session_id, llm_config):
    """Call retrieval decision agent."""
    try:
        response = await client.post(
            f"{LLMS_HOST_URL}/api/v1/agent/retrieval-decision",
            json={
                "user_query": query,
                "session_id": session_id,
                "llm_config": llm_config
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Retrieval decision failed: {e}, defaulting to True")
        return {"needs_retrieval": True, "reason": "Fallback due to error"}


async def call_text_retrieval(client, query, user_id, session_id):
    """Call RAG text retrieval."""
    try:
        response = await client.post(
            f"{RAG_PIPELINE_URL}/api/v1/rag/retrieve/text",
            json={
                "user_query": query,
                "user_id": user_id,
                "session_id": session_id,
                "top_k": 5
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Text retrieval failed: {e}")
        return {"results": [], "count": 0}


async def call_image_retrieval(client, image_data, user_id):
    """Call RAG image retrieval."""
    try:
        response = await client.post(
            f"{RAG_PIPELINE_URL}/api/v1/rag/retrieve/image",
            json={
                "image_data": image_data,
                "user_id": user_id,
                "top_k": 3
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Image retrieval failed: {e}")
        return {"results": [], "count": 0}


async def call_chat_agent(client, message, images, session_id, context, llm_config):
    """Call chat agent."""
    try:
        response = await client.post(
            f"{LLMS_HOST_URL}/api/v1/agent/chat",
            json={
                "user_message": message,
                "images": images,
                "session_id": session_id,
                "additional_context": context,
                "llm_config": llm_config
            },
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Chat agent failed: {e}")
        raise


def format_context(context_list: List[Dict]) -> str:
    """Format retrieved context for chat agent."""
    if not context_list:
        return None
    
    formatted = "Retrieved Context:\n\n"
    for i, ctx in enumerate(context_list, 1):
        text = ctx.get("text", ctx.get("content", ""))
        metadata = ctx.get("metadata", {})
        source = metadata.get("filename", "Unknown")
        formatted += f"[{i}] Source: {source}\n{text}\n\n"
    
    return formatted
