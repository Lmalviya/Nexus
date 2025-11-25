from typing import List, Dict, Any
from langchain_core.documents import Document
from .base_chunker import BaseChunker


class FixedChunker(BaseChunker):
    """
    Simple fixed-size chunking with overlap (fallback method).
    
    This chunker:
    1. Splits text into fixed-size chunks by token count
    2. Adds configurable overlap between chunks
    3. Preserves word boundaries
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Configuration
        self.chunk_size = self.config.get('chunk_size', 512)
        self.overlap_tokens = self.config.get('overlap_tokens', 50)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk text into fixed-size pieces with overlap.
        
        Args:
            content: The text content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        # Split into words (preserving whitespace info)
        words = content.split()
        
        if len(words) == 0:
            return []
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Get chunk of words
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Create document
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'start_token': start_idx,
                'end_token': end_idx,
                'num_tokens': len(chunk_words),
                'chunking_method': 'fixed',
            })
            chunks.append(self._create_document(chunk_text, chunk_metadata))
            
            # Move to next chunk with overlap
            if end_idx >= len(words):
                break
            
            start_idx = end_idx - self.overlap_tokens
            
            # Ensure we make progress
            if start_idx <= chunks[-1].metadata.get('start_token', 0):
                start_idx = end_idx
        
        return chunks
