from typing import List
from utils.llm_call import call_llm

class SQLAgent:
    """
    Agent responsible for generating SQL queries based on user request and context.
    """
    
    def generate_sql(self, user_query: str, context: List[str], conversation_id: str) -> str:
        """
        Generates a SQL query.
        
        Args:
            user_query (str): The user's query.
            context (List[str]): Relevant context to help generate the SQL.
            conversation_id (str): The ID of the conversation.
            
        Returns:
            str: The generated SQL query.
        """
        context_str = "\n".join(context)
        prompt = f"""
        You are a SQL agent. Your task is to generate a SQL query based on the user's request and the provided context.
        
        User Query: {user_query}
        
        Context:
        {context_str}
        
        If the context contains a previous failed SQL query and an error message, FIX the query.
        Generate a valid SQL query (PostgreSQL dialect).
        Return ONLY the SQL query string, no markdown formatting.
        """
        
        metadata = {
            "agent": "SQLAgent",
            "action": "generate_sql"
        }
        
        response = call_llm(prompt, conversation_id, metadata)
        return response
