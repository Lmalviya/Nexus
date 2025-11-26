from typing import List, Dict, Any
from llms_host.agents.rag_router_agent import RouterAgent, RouterInput
from llms_host.agents.sql_agent import SQLAgent, SQLInput
from utils.db_connection import PostgresConnector
from llms_host.config import get_agent_config
import json

class ContextOrchestrator:
    """
    Orchestrates the iterative retrieval process involving Router and SQL Agents.
    """
    def __init__(self, postgres_connector: PostgresConnector):
        self.rag_router_agent = RouterAgent()
        self.sql_agent = SQLAgent()
        self.postgres = postgres_connector
        # Load configs
        self.router_config = get_agent_config("router")
        self.sql_config = get_agent_config("sql_agent")

    def orchestrate(self, user_query: str, initial_context: List[Dict[str, Any]], conversation_id: str, max_iterations: int = 10) -> List[Dict[str, Any]]:
        """
        Iteratively enhances context by querying SQL database if needed.
        
        Args:
            user_query (str): The user's query.
            initial_context (List[Dict[str, Any]]): Initial context from vector DB.
            conversation_id (str): The ID of the conversation.
            max_iterations (int): Maximum number of iterations.
            
        Returns:
            List[Dict[str, Any]]: The final aggregated context.
        """
        current_context = initial_context.copy()
        # Convert dict context to string list for agents
        context_strs = [str(c) for c in current_context]
        
        for i in range(max_iterations):
            print(f"Iteration {i+1}/{max_iterations}")
            
            # 1. Router Decision
            router_input = RouterInput(
                user_query=user_query,
                retrieved_context=context_strs,
                conversation_id=conversation_id
            )
            
            decision_output = self.rag_router_agent.route(router_input, self.router_config)
            
            if decision_output.decision != "sql":
                print(f"Router decided to stop (Vector sufficient). Reason: {decision_output.reason}")
                break
                
            # 2. SQL Generation
            sql_input = SQLInput(
                user_query=user_query,
                context=context_strs,
                conversation_id=conversation_id
            )
            
            sql_output = self.sql_agent.generate_sql(sql_input, self.sql_config)
            sql_query = sql_output.sql_query
            print(f"Generated SQL: {sql_query}")
            
            # 3. Execute SQL
            try:
                # Basic sanitation/validation could go here
                results = self.postgres.execute_raw_sql(sql_query)
                
                # Format results as context
                sql_context = {
                    "source": "postgresql",
                    "query": sql_query,
                    "results": str(results)
                }
                
                current_context.append(sql_context)
                context_strs.append(str(sql_context))
                print("SQL executed successfully. Context updated.")
                
            except Exception as e:
                print(f"SQL Execution Error: {e}")
                # Feed error back to context so agent knows
                error_context = {
                    "source": "system_error",
                    "error": str(e),
                    "failed_query": sql_query
                }
                current_context.append(error_context)
                context_strs.append(str(error_context))
        
        return current_context
