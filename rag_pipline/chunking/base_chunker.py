from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.documents import Document


class BaseChunker(ABC):
    """
    Abstract base class for all chunking strategies.
    
    All chunkers must implement the chunk() method which takes text content
    and returns a list of LangChain Document objects with appropriate metadata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the chunker with optional configuration.
        
        Args:
            config: Dictionary of configuration parameters specific to the chunker
        """
        self.config = config or {}
    
    @abstractmethod
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk the content into smaller pieces.
        
        Args:
            content: The text content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects, each representing a chunk
        """
        pass
    
    def _create_document(self, text: str, metadata: Dict[str, Any]) -> Document:
        """
        Helper method to create a Document with metadata.
        
        Args:
            text: The chunk text
            metadata: Metadata for the chunk
            
        Returns:
            Document object
        """
        return Document(page_content=text, metadata=metadata)
    
    def _add_overlap(self, chunks: List[str], overlap_size: int) -> List[str]:
        """
        Add overlap between consecutive chunks.
        
        Args:
            chunks: List of chunk strings
            overlap_size: Number of characters/tokens to overlap
            
        Returns:
            List of chunks with overlap
        """
        if overlap_size <= 0 or len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                # Add end of previous chunk to beginning of current chunk
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-overlap_size:] if len(prev_chunk) > overlap_size else prev_chunk
                overlapped_chunks.append(overlap_text + " " + chunk)
        
        return overlapped_chunks
    
    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count (simple word-based approximation).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate token count
        """
        # Simple approximation: split by whitespace
        # More accurate would be to use a tokenizer like tiktoken
        return len(text.split())
