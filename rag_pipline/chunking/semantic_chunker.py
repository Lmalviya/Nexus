import numpy as np
from typing import List, Dict, Any
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
import nltk
from .base_chunker import BaseChunker

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class SemanticChunker(BaseChunker):
    """
    Semantic chunking using sentence embeddings to group related content.
    
    This chunker:
    1. Splits text into sentences
    2. Generates embeddings for each sentence
    3. Calculates cosine similarity between consecutive sentences
    4. Creates chunk boundaries where similarity drops below threshold
    5. Ensures chunks stay within min/max token limits
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Configuration
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 512)
        self.overlap_sentences = self.config.get('overlap_sentences', 2)
        model_name = self.config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        
        # Load embedding model
        self.model = SentenceTransformer(model_name)
    
    def chunk(self, content: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Chunk text using semantic similarity.
        
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
        
        # Generate embeddings for all sentences
        embeddings = self.model.encode(sentences, convert_to_numpy=True)
        
        # Calculate cosine similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        # Find chunk boundaries where similarity drops
        chunk_boundaries = [0]  # Start with first sentence
        current_chunk_tokens = 0
        
        for i, sim in enumerate(similarities):
            sentence_tokens = self._count_tokens(sentences[i])
            current_chunk_tokens += sentence_tokens
            
            # Create boundary if:
            # 1. Similarity drops below threshold, OR
            # 2. Current chunk exceeds max size
            if (sim < self.similarity_threshold and current_chunk_tokens >= self.min_chunk_size) or \
               current_chunk_tokens >= self.max_chunk_size:
                chunk_boundaries.append(i + 1)
                current_chunk_tokens = 0
        
        # Add final boundary
        if chunk_boundaries[-1] != len(sentences):
            chunk_boundaries.append(len(sentences))
        
        # Create chunks from boundaries
        chunks = []
        for i in range(len(chunk_boundaries) - 1):
            start_idx = chunk_boundaries[i]
            end_idx = chunk_boundaries[i + 1]
            
            # Add overlap from previous chunk
            if i > 0 and self.overlap_sentences > 0:
                overlap_start = max(0, start_idx - self.overlap_sentences)
                chunk_sentences = sentences[overlap_start:end_idx]
            else:
                chunk_sentences = sentences[start_idx:end_idx]
            
            chunk_text = ' '.join(chunk_sentences)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'start_sentence': start_idx,
                'end_sentence': end_idx,
                'num_sentences': end_idx - start_idx,
                'chunking_method': 'semantic',
            })
            
            chunks.append(self._create_document(chunk_text, chunk_metadata))
        
        return chunks
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
