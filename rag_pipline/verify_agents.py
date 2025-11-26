import sys
import os
from unittest.mock import MagicMock

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock dependencies
sys.modules['llms_host.memory.conversation'] = MagicMock()
# Mock Ollama with ResponseError
class MockOllamaModule:
    class ResponseError(Exception):
        pass
    def chat(self, *args, **kwargs):
        # Return a dummy response structure that matches what BaseAgent expects
        return {'message': {'content': '{"decision": "vector", "reason": "mocked response"}'}}

sys.modules['ollama'] = MockOllamaModule()

from llms_host.agents.query_re_writer_agent import QueryReWriterAgent, QueryRewriteInput
from llms_host.agents.rag_router_agent import RouterAgent, RouterInput
from llms_host.agents.sql_agent import SQLAgent, SQLInput
from llms_host.config import get_agent_config

def test_agents():
    conversation_id = "test_conv_123"
    
    print("--- Testing QueryReWriterAgent ---")
    rewriter = QueryReWriterAgent()
    config_rewriter = get_agent_config("query_rewriter")
    user_query = "show me sales data"
    
    input_rewrite = QueryRewriteInput(
        user_query=user_query,
        conversation_id=conversation_id
    )
    
    rewritten = rewriter.rewrite_query(input_rewrite, config_rewriter)
    print(f"Original: {user_query}")
    print(f"Rewritten: {rewritten.rewritten_query}")
    print("-" * 30)
    
    print("--- Testing RouterAgent ---")
    router = RouterAgent()
    config_router = get_agent_config("router")
    context = ["Sales data is stored in the 'sales' table.", "Revenue for 2023 was $1M."]
    
    input_router = RouterInput(
        user_query=user_query,
        retrieved_context=context,
        conversation_id=conversation_id
    )
    
    decision = router.route(input_router, config_router)
    print(f"Context: {context}")
    print(f"Decision: {decision.decision}")
    print(f"Reason: {decision.reason}")
    print("-" * 30)
    
    print("--- Testing SQLAgent ---")
    sql_agent = SQLAgent()
    config_sql = get_agent_config("sql_agent")
    
    input_sql = SQLInput(
        user_query=user_query,
        context=context,
        conversation_id=conversation_id
    )
    
    sql_query = sql_agent.generate_sql(input_sql, config_sql)
    print(f"SQL Query: {sql_query.sql_query}")
    print("-" * 30)

if __name__ == "__main__":
    test_agents()
