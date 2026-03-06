from typing import List, Dict, Any
from langchain_core.documents import Document
import nltk
from .base_chunker import BaseChunker

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class SentenceChunker(BaseChunker):
    """
    Simple sentence-based chunking with configurable overlap.
    
    This chunker:
    1. Splits text into sentences using NLTK
    2. Groups sentences into chunks based on token count
    3. Adds overlap by including last N sentences from previous chunk
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Configuration
        self.chunk_size = self.config.get('chunk_size', 512)
        self.overlap_sentences = self.config.get('overlap_sentences', 2)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk text by sentences with overlap.
        
        Args:
            content: The text content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects
        """
        if metadata is None:
            metadata = {}
        
        # Split into sentences
        sentences = nltk.sent_tokenize(content)
        
        if len(sentences) == 0:
            return []
        
        if len(sentences) == 1:
            return [self._create_document(content, metadata)]
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        overlap_buffer = []
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self._count_tokens(sentence)
            
            # Check if adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': len(chunks),
                    'start_sentence': i - len(current_chunk),
                    'end_sentence': i,
                    'num_sentences': len(current_chunk),
                    'chunking_method': 'sentence',
                })
                chunks.append(self._create_document(chunk_text, chunk_metadata))
                
                # Keep last N sentences for overlap
                overlap_buffer = current_chunk[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                
                # Start new chunk with overlap
                current_chunk = overlap_buffer + [sentence]
                current_tokens = sum(self._count_tokens(s) for s in current_chunk)
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk if not empty
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': len(chunks),
                'start_sentence': len(sentences) - len(current_chunk),
                'end_sentence': len(sentences),
                'num_sentences': len(current_chunk),
                'chunking_method': 'sentence',
            })
            chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        return chunks
