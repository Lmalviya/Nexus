import sys
import os

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.query_re_writer_agent import QueryReWriterAgent
from agents.router_agent import RouterAgent
from agents.sql_agent import SQLAgent

def test_agents():
    conversation_id = "test_conv_123"
    
    print("--- Testing QueryReWriterAgent ---")
    rewriter = QueryReWriterAgent()
    user_query = "show me sales data"
    rewritten = rewriter.rewrite_query(user_query, conversation_id)
    print(f"Original: {user_query}")
    print(f"Rewritten: {rewritten}")
    print("-" * 30)
    
    print("--- Testing RouterAgent ---")
    router = RouterAgent()
    context = ["Sales data is stored in the 'sales' table.", "Revenue for 2023 was $1M."]
    decision = router.route(user_query, context, conversation_id)
    print(f"Context: {context}")
    print(f"Decision: {decision}")
    print("-" * 30)
    
    print("--- Testing SQLAgent ---")
    sql_agent = SQLAgent()
    sql_query = sql_agent.generate_sql(user_query, context, conversation_id)
    print(f"SQL Query: {sql_query}")
    print("-" * 30)

if __name__ == "__main__":
    test_agents()
