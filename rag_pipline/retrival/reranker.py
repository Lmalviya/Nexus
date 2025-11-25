from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import torch

class Reranker:
    """
    Reranks retrieved documents using a CrossEncoder model.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks the documents based on their relevance to the query.
        
        Args:
            query (str): The search query.
            documents (List[Dict[str, Any]]): List of document payloads.
            top_k (int): Number of top documents to return.
            
        Returns:
            List[Dict[str, Any]]: The top_k reranked documents.
        """
        if not documents:
            return []
            
        # Prepare pairs for CrossEncoder
        # Assuming payload has a 'content' field. If not, we might need to adjust.
        # Fallback to str(payload) if content is missing.
        pairs = []
        for doc in documents:
            content = doc.get("content", str(doc))
            pairs.append([query, content])
            
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Combine docs with scores
        doc_scores = list(zip(documents, scores))
        
        # Sort by score descending
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k docs
        return [doc for doc, score in doc_scores[:top_k]]
