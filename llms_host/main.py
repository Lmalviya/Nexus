"""Nexus LLM Host - Main FastAPI Application"""

from fastapi import FastAPI
import logging

from llms_host.api.routers import agents, embeddings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nexus LLM Host",
    version="2.0.0",
    description="AI Agent and Embedding Service with Ollama backend"
)

# Include routers
app.include_router(agents.router)
app.include_router(embeddings.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Nexus LLM Host",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "agents": "/api/v1/agent/*",
            "embeddings": "/api/v1/embeddings/*",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Nexus LLM Host...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
