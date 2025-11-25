from utils.llm_call import call_llm

class QueryReWriterAgent:
    """
    Agent responsible for rewriting user queries to enhance vector database retrieval.
    """
    
    def rewrite_query(self, user_query: str, conversation_id: str) -> str:
        """
        Rewrites the user query to be more suitable for vector database retrieval.
        
        Args:
            user_query (str): The original user query.
            conversation_id (str): The ID of the conversation.
            
        Returns:
            str: The rewritten query.
        """
        prompt = f"""
        You are a helpful assistant that rewrites user queries to be more specific and suitable for retrieval from a vector database.
        
        Original Query: {user_query}
        
        Rewritten Query:
        """
        
        metadata = {
            "agent": "QueryReWriterAgent",
            "action": "rewrite_query"
        }
        
        response = call_llm(prompt, conversation_id, metadata)
        return response
