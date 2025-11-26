import ollama
from typing import List
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

class ImageEmbeddingModel:
    """Image embedding model using Ollama's multimodal embedding API.
    
    Uses nomic-embed-text-v1.5 model which supports both text and image embeddings,
    aligning vision and text in the same embedding space.
    This replaces the previous CLIP implementation.
    Supports parallel embedding generation for improved performance.
    """
    
    def __init__(self, model_name: str = "nomic-embed-text-v1.5", max_workers: int = 5):
        """Initialize the image embedding model.
        
        Args:
            model_name: Ollama multimodal embedding model to use (default: nomic-embed-text-v1.5)
            max_workers: Maximum number of parallel workers for embedding generation
        """
        self.model_name = model_name
        self.max_workers = max_workers

    def _embed_single(self, b64_image: str) -> List[float]:
        """Generate embedding for a single image.
        
        Args:
            b64_image: Base64-encoded image string
            
        Returns:
            Embedding vector as a list of floats
        """
        response = ollama.embed(
            model=self.model_name,
            input=b64_image
        )
        return response['embeddings'][0]

    def embed_from_base64(self, base64_images: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of base64-encoded images in parallel.
        
        Args:
            base64_images: List of base64-encoded image strings
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if len(base64_images) == 1:
            # For single image, no need for parallelization
            return [self._embed_single(base64_images[0])]
        
        # Use ThreadPoolExecutor for parallel processing
        embeddings = [None] * len(base64_images)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._embed_single, b64_image): i 
                for i, b64_image in enumerate(base64_images)
            }
            
            # Collect results in order
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                embeddings[index] = future.result()
        
        return embeddings
