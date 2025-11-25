import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def call_llm(prompt: str, conversation_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Dummy function to simulate an LLM call.
    
    Args:
        prompt (str): The prompt to send to the LLM.
        conversation_id (str): The ID of the conversation.
        metadata (Optional[Dict[str, Any]]): Additional metadata for the call.
        
    Returns:
        str: A dummy response from the LLM.
    """
    if metadata is None:
        metadata = {}
        
    logger.info(f"LLM Call Initiated. Conversation ID: {conversation_id}")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Metadata: {metadata}")
    
    # Simulate processing
    response = f"Dummy response for prompt: {prompt[:50]}..."
    
    logger.info(f"LLM Response: {response}")
    
    return response
