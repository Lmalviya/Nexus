"""
Chunking module for RAG pipeline.

This module provides intelligent chunking strategies for different file types:
- Code files: Function/class-based chunking
- Markdown: Structure-aware chunking
- JSON/XML: Structure-aware chunking
- Text: Semantic or sentence-based chunking
- Unknown: Fixed-size chunking (fallback)

Usage:
    from rag_pipline.chunking import ChunkingFactory
    
    # Create factory with configuration
    factory = ChunkingFactory(config={
        'semantic': {'similarity_threshold': 0.7},
        'code': {'include_imports': True},
    })
    
    # Chunk a file
    with open('example.py', 'r') as f:
        content = f.read()
    chunks = factory.chunk_file('example.py', content)
    
    # Chunk raw text
    chunks = factory.chunk_text("Some text...", chunker_type='semantic')
"""

from .base_chunker import BaseChunker
from .code_chunker import CodeChunker
from .semantic_chunker import SemanticChunker
from .sentence_chunker import SentenceChunker
from .markdown_chunker import MarkdownChunker
from .fixed_chunker import FixedChunker
from .structure_chunker import StructureChunker
from .chunking_factory import ChunkingFactory
from .config import ChunkingConfig

__all__ = [
    'BaseChunker',
    'CodeChunker',
    'SemanticChunker',
    'SentenceChunker',
    'MarkdownChunker',
    'FixedChunker',
    'StructureChunker',
    'ChunkingFactory',
    'ChunkingConfig',
]
