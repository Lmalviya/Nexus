import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path so we can import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rag_pipline.utils.llm_call import call_llm, get_text_embeddings, get_image_embeddings, generate_description

class TestLLMCall(unittest.TestCase):

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_call_llm_rewrite(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"rewritten_query": "rewritten query"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = call_llm("original query", "conv_123", {"agent": "query_rewriter"})
        
        self.assertEqual(result, "rewritten query")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/agent/rewrite", args[0])
        self.assertEqual(kwargs['json']['user_query'], "original query")
        self.assertEqual(kwargs['json']['conversation_id'], "conv_123")

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_call_llm_summarize(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"summary": "summary text"}
        mock_post.return_value = mock_response

        result = call_llm("text to summarize", "conv_123", {"agent": "summarizer"})
        
        self.assertEqual(result, "summary text")
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/agent/summarize", args[0])
        self.assertEqual(kwargs['json']['messages'][0]['content'], "text to summarize")

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_call_llm_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "chat response"}
        mock_post.return_value = mock_response

        result = call_llm("hello", "conv_123", {"agent": "chat", "images": ["img_base64"]})
        
        self.assertEqual(result, "chat response")
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/agent/chat", args[0])
        self.assertEqual(kwargs['json']['user_message'], "hello")
        self.assertEqual(kwargs['json']['images'], ["img_base64"])

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_get_text_embeddings(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [[0.1, 0.2]]}
        mock_post.return_value = mock_response

        result = get_text_embeddings(["text1"])
        
        self.assertEqual(result, [[0.1, 0.2]])
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/embeddings/text", args[0])
        self.assertEqual(kwargs['json']['texts'], ["text1"])

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_get_image_embeddings(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": [[0.3, 0.4]]}
        mock_post.return_value = mock_response

        result = get_image_embeddings(["img_base64"])
        
        self.assertEqual(result, [[0.3, 0.4]])
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/embeddings/image", args[0])
        self.assertEqual(kwargs['json']['images'], ["img_base64"])

    @patch('rag_pipline.utils.llm_call.requests.post')
    def test_generate_description(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"description": "desc"}
        mock_post.return_value = mock_response

        result = generate_description("image", {"image_data": "base64"}, "conv_123")
        
        self.assertEqual(result, "desc")
        args, kwargs = mock_post.call_args
        self.assertIn("/api/v1/agent/describe", args[0])
        self.assertEqual(kwargs['json']['content_type'], "image")
        self.assertEqual(kwargs['json']['data']['image_data'], "base64")

if __name__ == '__main__':
    unittest.main()
