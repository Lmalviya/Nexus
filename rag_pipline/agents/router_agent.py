from typing import List, Dict, Any
from utils.llm_call import call_llm
import json

class RouterAgent:
    """
    Agent responsible for routing the query based on retrieved context.
    It decides if a SQL query is needed or if the vector store context is sufficient.
    """
    
    def route(self, user_query: str, retrieved_context: List[str], conversation_id: str) -> Dict[str, Any]:
        """
        Analyzes the user query and retrieved context to decide the next step.
        
        Args:
            user_query (str): The user's query.
            retrieved_context (List[str]): Context retrieved from the vector database.
            conversation_id (str): The ID of the conversation.
            
        Returns:
            Dict[str, Any]: A dictionary containing the decision ("sql" or "vector") and relevant info.
        """
        context_str = "\n".join(retrieved_context)
        prompt = f"""
        You are a router agent. Your task is to analyze the user query and the retrieved context to determine if we need to query a structured database (SQL) or if the retrieved text context is sufficient.
        
        User Query: {user_query}
        
        Retrieved Context:
        {context_str}
        
        Decide if we need to query a SQL database to get MORE information or if we have enough.
        If you see SQL results in the context that answer the query, you should probably stop (decision: vector).
        If the context is missing specific data that is likely in a database, choose SQL.
        
        If yes (need SQL), return JSON: {{"decision": "sql", "reason": "explanation"}}
        If no (context sufficient), return JSON: {{"decision": "vector", "reason": "explanation"}}
        """
        
        metadata = {
            "agent": "RouterAgent",
            "action": "route"
        }
        
        response = call_llm(prompt, conversation_id, metadata)
        
        # In a real implementation, we would parse the JSON response.
        # For now, since it's a dummy LLM, we'll return a dummy decision.
        # We'll simulate a decision based on the prompt length or random, but let's just default to vector for now unless "table" is in query.
        
        if "table" in user_query.lower() or "database" in user_query.lower():
             return {"decision": "sql", "reason": "User asked for table data"}
        else:
             return {"decision": "vector", "reason": "Context is sufficient"}
