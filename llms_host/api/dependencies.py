"""Shared dependencies for API endpoints."""

import logging
from llms_host.config import LLMConfig, LLMProvider, get_agent_config
from llms_host.embedding_models.text import TextEmbeddingModel
from llms_host.embedding_models.image import ImageEmbeddingModel

logger = logging.getLogger(__name__)

# Lazy loading for embedding models
_text_embedder = None
_image_embedder = None


def get_text_embedder() -> TextEmbeddingModel:
    """Get or initialize text embedding model (singleton)."""
    global _text_embedder
    if _text_embedder is None:
        logger.info("Initializing text embedding model...")
        _text_embedder = TextEmbeddingModel()
    return _text_embedder


def get_image_embedder() -> ImageEmbeddingModel:
    """Get or initialize image embedding model (singleton)."""
    global _image_embedder
    if _image_embedder is None:
        logger.info("Initializing image embedding model...")
        _image_embedder = ImageEmbeddingModel()
    return _image_embedder


def resolve_llm_config(llm_config_dict: dict, default_agent: str) -> LLMConfig:
    """Resolve LLM configuration from request or use default.
    
    Args:
        llm_config_dict: Optional LLM config from request
        default_agent: Default agent name to get config for
        
    Returns:
        LLMConfig instance
    """
    if llm_config_dict:
        return LLMConfig(
            provider=LLMProvider(llm_config_dict.get("provider", "ollama")),
            model_name=llm_config_dict.get("model_name", "llama3"),
            api_key=llm_config_dict.get("api_key"),
            api_base_url=llm_config_dict.get("api_base_url"),
            parameters=llm_config_dict.get("parameters", {})
        )
    return get_agent_config(default_agent)
