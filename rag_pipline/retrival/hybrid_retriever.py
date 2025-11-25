from typing import List, Dict, Any
from utils.db_connection import QdrantConnector
from utils.embeddings import TextEmbeddings
from rag_pipline.config import TextEmbeddingsConfig

class HybridRetriever:
    """
    Combines semantic search (Vector) and keyword search (BM25/Text Match).
    """
    def __init__(self, qdrant_connector: QdrantConnector):
        self.qdrant = qdrant_connector
        # Initialize embeddings model
        config = TextEmbeddingsConfig()
        self.embeddings = TextEmbeddings(config)

    def retrieve(self, user_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves documents using both semantic and keyword search.
        
        Args:
            user_id (str): The user ID.
            query (str): The search query.
            top_k (int): Number of documents to retrieve per method.
            
        Returns:
            List[Dict[str, Any]]: A list of unique retrieved documents (payloads).
        """
        # 1. Semantic Search
        query_vector = self.embeddings.embed_query(query)
        semantic_results = self.qdrant.search_text(user_id, query_vector, top_k=top_k)
        
        # 2. Keyword Search
        keyword_results = self.qdrant.search_keyword(user_id, query, top_k=top_k)
        
        # 3. Combine Results (Deduplicate based on ID or content)
        combined_results = {}
        
        for point in semantic_results:
            combined_results[point.id] = point.payload
            
        for point in keyword_results:
            if point.id not in combined_results:
                combined_results[point.id] = point.payload
                
        return list(combined_results.values())
