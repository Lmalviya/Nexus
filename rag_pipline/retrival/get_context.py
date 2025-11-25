from typing import List, Dict, Any
from retrival.query_enhancer import QueryEnhancer
from retrival.hybrid_retriever import HybridRetriever
from retrival.reranker import Reranker
from retrival.context_orchestrator import ContextOrchestrator
from utils.db_connection import QdrantConnector, PostgresConnector

class RetrievalPipeline:
    def __init__(self):
        # Initialize connectors
        self.qdrant = QdrantConnector()
        self.postgres = PostgresConnector()
        
        # Initialize components
        self.query_enhancer = QueryEnhancer()
        self.hybrid_retriever = HybridRetriever(self.qdrant)
        self.reranker = Reranker()
        self.orchestrator = ContextOrchestrator(self.postgres)

    def get_context(self, user_query: str, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Main entry point for the retrieval pipeline.
        
        Args:
            user_query (str): The user's query.
            user_id (str): The user ID.
            conversation_id (str): The conversation ID.
            
        Returns:
            List[Dict[str, Any]]: The final context.
        """
        print(f"Starting retrieval for query: {user_query}")
        
        # 1. Enhance Query
        enhanced_query = self.query_enhancer.enhance_query(user_query, conversation_id)
        print(f"Enhanced Query: {enhanced_query}")
        
        # 2. Hybrid Retrieval (Semantic + Keyword)
        # Top 10 for each, so potentially 20 docs
        retrieved_docs = self.hybrid_retriever.retrieve(user_id, enhanced_query, top_k=10)
        print(f"Retrieved {len(retrieved_docs)} documents from vector DB.")
        
        # 3. Reranking
        # Re-rank and take top 5
        top_docs = self.reranker.rerank(enhanced_query, retrieved_docs, top_k=5)
        print(f"Reranked to top {len(top_docs)} documents.")
        
        # 4. Context Orchestration (Iterative SQL)
        final_context = self.orchestrator.orchestrate(user_query, top_docs, conversation_id, max_iterations=10)
        print(f"Final context size: {len(final_context)}")
        
        return final_context

# Helper function for easy import
def get_context(user_query: str, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
    pipeline = RetrievalPipeline()
    return pipeline.get_context(user_query, user_id, conversation_id)
