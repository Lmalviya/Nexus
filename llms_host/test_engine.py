import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add workspace to path
sys.path.append("C:\\Users\\23add\\workspace\\Nexus")

from llms_host.engine import LLMEngine
from llms_host.config import AgentName

class TestLLMEngine(unittest.TestCase):
    
    @patch('llms_host.memory.conversation.redis.Redis')
    @patch('llms_host.engine.ollama.chat')
    def test_ollama_generation(self, mock_ollama_chat, mock_redis):
        # Setup Redis mock
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        # Mock lrange to return empty list initially
        mock_redis_instance.lrange.return_value = []
        
        # Setup Ollama mock
        mock_ollama_chat.return_value = {
            'message': {'content': 'Mocked response'}
        }
        
        engine = LLMEngine()
        response = engine.generate_response(
            agent_name=AgentName.SUMMARIZER.value,
            message="Hello",
            session_id="test_id"
        )
        
        self.assertEqual(response, "Mocked response")
        
        # Verify Redis was called to save
        self.assertTrue(mock_redis_instance.rpush.called)
        # Should be called twice (user msg + assistant msg)
        self.assertEqual(mock_redis_instance.rpush.call_count, 2)

if __name__ == '__main__':
    unittest.main()
