import ollama
import requests
import json
from typing import Optional, Dict, Any, Generator
from llms_host.config import get_agent_config, LLMProvider, LLMConfig
from llms_host.memory.conversation import Conversation

class LLMEngine:
    def __init__(self):
        pass

    def generate_response(self, agent_name: str, message: str, role: str = "user", conversation_id: str = "default", metadata: Dict[str, Any] = None) -> str:
        """
        Generates a response for the given agent and message.
        Manages context retrieval and memory updates.
        """
        # 1. Get Configuration
        try:
            config = get_agent_config(agent_name)
            config.validate()
        except ValueError as e:
            return f"Configuration Error: {str(e)}"

        # 2. Initialize Conversation Memory
        conversation = Conversation(agent_name, conversation_id)
        
        # 3. Get Context (History + Summary if needed)
        # We append the current message to the context temporarily for the LLM call
        # But we don't save it to Redis yet, we save it after we get the response to ensure atomic-like turn
        # Or we can save user message first. Let's save user message first? 
        # Actually, get_context pulls from Redis. So if we want the current message to be in context, 
        # we should probably pass it to the LLM call directly or append it to the context list returned by get_context.
        
        context_messages = conversation.get_context()
        
        # Add the current new message to the context list for the LLM
        current_message_obj = {"role": role, "content": message}
        context_messages.append(current_message_obj)

        response_content = ""

        # 4. Generate Response
        if config.provider == LLMProvider.OLLAMA:
            response_content = self._call_ollama(config, context_messages)
        elif config.provider == LLMProvider.API:
            response_content = self._call_external_api(config, context_messages)
        else:
            return "Error: Unsupported provider."

        # 5. Save Turn to Memory (Persist full history)
        # We save the user message and the assistant response
        conversation.save_turn(message, response_content, metadata)

        return response_content

    def _call_ollama(self, config: LLMConfig, messages: list) -> str:
        try:
            # Ollama python library expects 'model' and 'messages'
            # Messages should be list of dicts with 'role' and 'content'
            response = ollama.chat(
                model=config.model_name,
                messages=messages,
                options=config.parameters
            )
            return response['message']['content']
        except Exception as e:
            return f"Ollama Error: {str(e)}"

    def _call_external_api(self, config: LLMConfig, messages: list) -> str:
        try:
            # Assuming OpenAI-compatible API
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config.model_name,
                "messages": messages,
                **config.parameters
            }
            
            url = config.api_base_url or "https://api.openai.com/v1/chat/completions"
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            return f"API Error: {str(e)}"
