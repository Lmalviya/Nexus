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
    Routes to specific agents based on metadata['agent'].
    """
    if metadata is None:
        metadata = {}
        
    agent_name = metadata.get("agent", "query_rewriter")
    
    try:
        if agent_name == "query_rewriter":
            endpoint = f"{LLMS_HOST_URL}/api/v1/agent/rewrite"
            payload = {
                "conversation_id": conversation_id,
                "user_query": prompt,
                "additional_context": metadata.get("context")
            }
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("rewritten_query", "")

        elif agent_name == "summarizer":
            endpoint = f"{LLMS_HOST_URL}/api/v1/agent/summarize"
            # Summarizer expects a list of messages. 
            # If prompt is a single string, we wrap it, but usually this agent expects history.
            # Assuming prompt here is the raw text to summarize or we need to pass messages in metadata.
            # For now, let's assume the prompt is the content to summarize if messages aren't provided.
            messages = metadata.get("messages", [{"role": "user", "content": prompt}])
            payload = {
                "conversation_id": conversation_id,
                "messages": messages
            }
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("summary", "")

        elif agent_name == "description":
            # This maps to generate_description but exposed via call_llm for convenience?
            # It's better to use generate_description directly, but we support it here.
            return generate_description(
                content_type=metadata.get("content_type", "text"),
                data={"content": prompt, **metadata.get("data", {})},
                conversation_id=conversation_id
            )
            
        elif agent_name == "chat":
            endpoint = f"{LLMS_HOST_URL}/api/v1/agent/chat"
            payload = {
                "conversation_id": conversation_id,
                "user_message": prompt,
                "images": metadata.get("images"), # List of base64 strings
                "additional_context": metadata.get("context")
            }
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("response", "") # ChatAgent returns 'response' field? Need to check ChatAgent return.

        else:
            # Default fallback or error
            logger.warning(f"Unknown agent: {agent_name}, defaulting to chat")
            endpoint = f"{LLMS_HOST_URL}/api/v1/agent/chat"
            payload = {
                "conversation_id": conversation_id,
                "user_message": prompt,
                "additional_context": metadata.get("context")
            }
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")

    except Exception as e:
        logger.error(f"Error calling LLM Host ({agent_name}): {e}")
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
    
    # Ensure data has the correct fields for the agent
    # TableDescriptionInput: headers, sample_rows, additional_context
    # ImageDescriptionInput: image_data (base64), additional_context
    
    payload = {
        "conversation_id": conversation_id,
        "content_type": content_type,
        "data": data
    }
    
    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("description", "")
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        return f"Error: {str(e)}"
