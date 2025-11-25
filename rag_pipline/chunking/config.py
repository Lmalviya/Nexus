"""Configuration for chunking methods."""


class ChunkingConfig:
    """Configuration for different chunking methods."""
    
    # Semantic chunking (for text files)
    semantic_similarity_threshold = 0.7
    semantic_min_chunk_size = 100
    semantic_max_chunk_size = 512
    semantic_overlap_sentences = 2
    semantic_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Sentence chunking (simple sentence-based)
    sentence_chunk_size = 512
    sentence_overlap = 2
    
    # Fixed chunking (fallback)
    fixed_chunk_size = 512
    fixed_overlap = 50
    
    # Code chunking
    code_include_imports = True
    code_min_function_lines = 3
    
    # Markdown chunking
    markdown_max_heading_level = 3
    markdown_max_chunk_size = 1000
    
    # Structure chunking (JSON/XML)
    structure_max_chunk_size = 1000
    structure_preserve_structure = True
    
    # General settings
    default_text_chunker = "semantic"  # Options: "semantic", "sentence"
