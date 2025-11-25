from PIL import Image
from transformers import CLIPProcessor, CLIPModel

import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer

from rag_pipline.config import TextEmbeddingsConfig, ImageEmbeddingsConfig


class TextEmbeddings:
    def __init__(self, config: TextEmbeddingsConfig):
        self.batch_size = config.batch_size
        self.device = config.device
        self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer)
        self.model = SentenceTransformer(config.model, device=self.device)

    def embed(self, texts: List[str]) -> List[float]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        ln = len(documents)
        embeddings = []
        for i in range(0, ln, self.batch_size): 
            embeddings.extend(self.embed(documents[i:i + self.batch_size]))
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        return self.embed([query])[0]


class ImageEmbeddings:
    def __init__(self, config: ImageEmbeddingsConfig, device: str = "cuda"):
        self.device = device
        self.batch_size = getattr(config, 'batch_size', 16)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)

    def embed(self, images: List[Image]):
        """Generate embeddings for a batch of images."""
        inputs = self.processor(images=images, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.get_image_features(**inputs)
        
        # Convert to numpy and normalize
        embeddings = outputs.cpu().numpy()
        return embeddings

    def embed_images(self, images: List[Image]) -> List[List[float]]:
        """Generate embeddings for multiple images with batching."""
        ln = len(images)
        embeddings = []
        for i in range(0, ln, self.batch_size): 
            batch_embeddings = self.embed(images[i:i + self.batch_size])
            embeddings.extend(batch_embeddings.tolist())
        return embeddings

    def embed_query(self, image: Image) -> List[float]:
        """Generate embedding for a single image."""
        return self.embed([image])[0].tolist()
