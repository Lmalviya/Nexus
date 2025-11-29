from agents.query_re_writer_agent import QueryReWriterAgent

class QueryEnhancer:
    """
    Enhances the user query using the QueryReWriterAgent.
    """
    def __init__(self):
        self.agent = QueryReWriterAgent()

    def enhance_query(self, user_query: str, session_id: str) -> str:
        """
        Rewrites the user query to be more suitable for retrieval.
        
        Args:
            user_query (str): The original user query.
            session_id (str): The ID of the session.
            
        Returns:
            str: The enhanced query.
        """
        return self.agent.rewrite_query(user_query, session_id)
