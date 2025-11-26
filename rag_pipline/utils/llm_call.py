import logging
import requests
import os
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LLMS_HOST_URL = os.getenv("LLMS_HOST_URL", "http://localhost:8002")

def call_llm(prompt: str, conversation_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Calls the LLM Host service to generate a response.
    This function might need to be adapted depending on which agent you want to call.
    If it's a generic LLM call, we might need a generic endpoint or map to a specific agent.
    Assuming this is for general query rewriting or similar, we might default to query_rewriter or a generic agent.
    However, the previous implementation was a dummy.
    Let's assume this maps to a generic 'chat' or specific agent based on metadata.
    """
    if metadata is None:
        metadata = {}
        
    agent_name = metadata.get("agent", "query_rewriter") # Default to query_rewriter if not specified
    
    endpoint = f"{LLMS_HOST_URL}/api/v1/agent/rewrite" # Default endpoint for now
    
    # Map agent names to endpoints if needed
    if agent_name == "summarizer":
        endpoint = f"{LLMS_HOST_URL}/api/v1/agent/summarize"
        payload = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": prompt}] # Summarizer expects messages
        }
    elif agent_name == "description":
        endpoint = f"{LLMS_HOST_URL}/api/v1/agent/describe"
        payload = {
            "conversation_id": conversation_id,
            "content_type": metadata.get("content_type", "text"),
            "data": {"content": prompt}
        }
    else:
        # Default to rewrite
        payload = {
            "conversation_id": conversation_id,
            "user_query": prompt,
            "additional_context": metadata.get("context")
        }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if agent_name == "summarizer":
            return result.get("summary", "")
        elif agent_name == "description":
            return result.get("description", "")
        elif hasattr(result, "get"):
             # Query rewriter returns string directly or dict? 
             # The agent returns QueryRewriteOutput object which is Pydantic.
             # FastAPI returns it as JSON.
             return result.get("rewritten_query", str(result))
        else:
            return str(result)
            
    except Exception as e:
        logger.error(f"Error calling LLM Host: {e}")
        return f"Error: {str(e)}"

def get_text_embeddings(texts: List[str]) -> List[List[float]]:
    endpoint = f"{LLMS_HOST_URL}/api/v1/embeddings/text"
    try:
        response = requests.post(endpoint, json={"texts": texts})
        response.raise_for_status()
        return response.json()["embeddings"]
    except Exception as e:
        logger.error(f"Error getting text embeddings: {e}")
        return []

def get_image_embeddings(base64_images: List[str]) -> List[List[float]]:
    endpoint = f"{LLMS_HOST_URL}/api/v1/embeddings/image"
    try:
        response = requests.post(endpoint, json={"images": base64_images})
        response.raise_for_status()
        return response.json()["embeddings"]
    except Exception as e:
        logger.error(f"Error getting image embeddings: {e}")
        return []

def generate_description(content_type: str, data: Dict[str, Any], conversation_id: str = "desc_gen") -> str:
    endpoint = f"{LLMS_HOST_URL}/api/v1/agent/describe"
    payload = {
        "conversation_id": conversation_id,
        "content_type": content_type,
        "data": data
    }
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()["description"]
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        return f"Error: {str(e)}"
