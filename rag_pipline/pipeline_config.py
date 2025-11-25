"""Configuration for the document processing pipeline."""

import torch


class PipelineConfig:
    """Configuration for document processing pipeline."""
    
    # Chunking settings
    default_chunker = "semantic"  # For text files
    chunk_tables = True  # Whether to chunk table descriptions
    
    # Embedding settings
    text_embedding_dim = 384  # Dimension for text embeddings (all-MiniLM-L6-v2)
    image_embedding_dim = 512  # Dimension for image embeddings (CLIP)
    
    # Storage settings
    cleanup_temp_files = True
    temp_dir = "./temp_processing"
    
    # Qdrant settings
    text_collection_suffix = "_text_embeddings"
    image_collection_suffix = "_image_embeddings"
    
    # Processing settings
    batch_size = 16
    device = "cuda" if torch.cuda.is_available() else "cpu"
