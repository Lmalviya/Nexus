import logging
import requests
from unittest.mock import MagicMock
import sys

# Mock Conversation before importing BaseAgent to avoid redis import if it's at top level
sys.modules['llms_host.memory.conversation'] = MagicMock()

# Create a proper mock for ollama that includes an Exception class
class MockOllamaModule:
    class ResponseError(Exception):
        pass
    
    def chat(self, *args, **kwargs):
        pass

sys.modules['ollama'] = MockOllamaModule()

from llms_host.agents.base_agent import BaseAgent
from llms_host.config import LLMConfig, LLMProvider

# Mock config
config = LLMConfig(
    provider=LLMProvider.API,
    model_name="test-model",
    api_key="test-key",
    api_base_url="http://test-url"
)

class MockAgent(BaseAgent):
    def __init__(self):
        # Bypass super init to avoid prompts module issues if any, 
        # but we need to set the basics manually
        self.agent_name = "test_agent"
        self.prompts = None
        self.max_retries = 3
        self.base_delay = 0.1 # Speed up tests

    def _call_llm(self, config, messages, output_model):
        self.attempt_count += 1
        print(f"Call attempt {self.attempt_count}")
        
        if self.attempt_count < 3:
            # Simulate 500 error
            response = requests.Response()
            response.status_code = 500
            raise requests.exceptions.HTTPError("Server Error", response=response)
        
        return "Success!"

    # Override run to avoid Conversation instantiation if needed, 
    # but since we mocked the module, it should return a mock object.
    # However, BaseAgent.run calls Conversation(name, id). 
    # Our mock module will return a MagicMock when Conversation is called.

def test_retry_logic():
    print("Testing Retry Logic...")
    agent = MockAgent()
    agent.attempt_count = 0
    
    # We need to ensure _assemble_prompt doesn't fail on the mock conversation
    # The mock conversation will return mocks for get_context, log_flow, save_turn
    
    result = agent.run("test input", "test-id", config)
    print(f"Result: {result}")
    
    if result == "Success!" and agent.attempt_count == 3:
        print("PASS: Retried correctly and succeeded.")
    else:
        print(f"FAIL: Attempts: {agent.attempt_count}, Result: {result}")

class FatalErrorAgent(BaseAgent):
    def __init__(self):
        self.agent_name = "fatal_agent"
        self.prompts = None
        self.max_retries = 3
        self.base_delay = 0.1

    def _call_llm(self, config, messages, output_model):
        print("Calling LLM (Fatal Error Test)")
        response = requests.Response()
        response.status_code = 400 # Bad Request
        raise requests.exceptions.HTTPError("Bad Request", response=response)

def test_fatal_error():
    print("\nTesting Fatal Error...")
    agent = FatalErrorAgent()
    result = agent.run("test input", "test-id", config)
    print(f"Result: {result}")
    
    if "Error: Bad Request" in result:
        print("PASS: Failed fast on fatal error.")
    else:
        print(f"FAIL: Result was {result}")

if __name__ == "__main__":
    test_retry_logic()
    test_fatal_error()
