"""Nexus RAG Pipeline - Main FastAPI Application"""

from fastapi import FastAPI
import logging
import uvicorn

from rag_pipline.api.router import router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nexus RAG Pipeline",
    version="1.0.0",
    description="RAG Pipeline Service for Document Processing and Retrieval"
)

# Include router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Nexus RAG Pipeline",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "rag": "/api/v1/rag/*",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    logger.info("Starting Nexus RAG Pipeline...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
