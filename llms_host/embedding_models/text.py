import ollama
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

class TextEmbeddingModel:
    """Text embedding model using Ollama's embedding API.
    
    Uses nomic-embed-text model (768 dimensions) for high-quality text embeddings.
    This replaces the previous sentence-transformers implementation.
    Supports parallel embedding generation for improved performance.
    """
    
    def __init__(self, model_name: str = "nomic-embed-text", max_workers: int = 5):
        """Initialize the text embedding model.
        
        Args:
            model_name: Ollama embedding model to use (default: nomic-embed-text)
            max_workers: Maximum number of parallel workers for embedding generation
        """
        self.model_name = model_name
        self.max_workers = max_workers

    def _embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        response = ollama.embed(
            model=self.model_name,
            input=text
        )
        return response['embeddings'][0]

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts in parallel.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if len(texts) == 1:
            # For single text, no need for parallelization
            return [self._embed_single(texts[0])]
        
        # Use ThreadPoolExecutor for parallel processing
        embeddings = [None] * len(texts)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._embed_single, text): i 
                for i, text in enumerate(texts)
            }
            
            # Collect results in order
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                embeddings[index] = future.result()
        
        return embeddings
