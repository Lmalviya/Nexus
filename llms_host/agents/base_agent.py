import time
import random
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
import logging
import json
from llms_host.memory.conversation import Conversation
from llms_host.config import LLMConfig, LLMProvider
import ollama
import requests

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, agent_name: str, prompts_module: Any):
        self.agent_name = agent_name
        self.prompts = prompts_module
        self.max_retries = 3
        self.base_delay = 1  # Initial delay in seconds

    def run(self, 
            user_input: str, 
            session_id: str, 
            llm_config: LLMConfig, 
            additional_context: Optional[str] = None,
            output_model: Optional[Type[BaseModel]] = None) -> Any:
        """
        Executes the agent's main logic.
        """
        conversation = Conversation(self.agent_name, session_id)
        
        # 1. Assemble Prompt
        messages = self._assemble_prompt(conversation, user_input, additional_context)
        
        # 2. Log the flow (before execution)
        conversation.log_flow(messages)
        
        # 3. Call LLM with Retry Logic
        response_content = ""
        
        for attempt in range(self.max_retries): 
            try:
                response_content = self._call_llm(llm_config, messages, output_model)
                break
            except (requests.exceptions.HTTPError, ollama.ResponseError) as e:
                # Determine if we should retry based on the error type
                if not self._is_retriable_error(e):
                    logger.error(f"Fatal error on attempt {attempt + 1}: {e}")
                    return f"Error: {str(e)}"
                
                logger.warning(f"Attempt {attempt + 1} failed with retriable error: {e}")
                
                if attempt == self.max_retries - 1:
                    return f"Error: Failed to generate response after {self.max_retries} attempts. Last error: {str(e)}"
                
                # Exponential backoff with jitter
                delay = (self.base_delay * (2 ** attempt)) + random.uniform(0, 1)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return f"Error: An unexpected error occurred: {str(e)}"
                
                # For unknown exceptions, we might still want to retry cautiously
                time.sleep(self.base_delay)

        conversation.save_turn(user_input, response_content)
        return response_content

    def _is_retriable_error(self, e: Exception) -> bool:
        """
        Determines if an error is retriable.
        """
        if isinstance(e, requests.exceptions.HTTPError):
            status_code = e.response.status_code
            # 429 (Too Many Requests) and 5xx (Server Errors) are retriable
            if status_code == 429 or 500 <= status_code < 600:
                return True
            # 400, 401, 403, 404 are client errors and usually not retriable without change
            return False
            
        if isinstance(e, ollama.ResponseError):
            # Ollama errors might need specific checking, but generally connection issues are retriable
            # Assuming status code is available or parsing message
            if hasattr(e, 'status_code'):
                 if e.status_code == 429 or 500 <= e.status_code < 600:
                    return True
            return False # Default to false for unknown Ollama errors to be safe, or check message
            
        return False

    def _assemble_prompt(self, conversation: Conversation, user_input: str, additional_context: Optional[str]) -> List[Dict[str, Any]]:
        messages = []
        
        # 1. System Prompt
        if hasattr(self.prompts, 'SYSTEM_PROMPT'):
            messages.append({"role": "system", "content": self.prompts.SYSTEM_PROMPT})
            
        # 2. Previous Conversation (Context Window)
        history = conversation.get_context()
        messages.extend(history)
        
        # 3. Few-Shot Examples
        if hasattr(self.prompts, 'FEW_SHOT_EXAMPLES'):
            messages.extend(self.prompts.FEW_SHOT_EXAMPLES)
            
        # 4. Additional Context (Vector DB)
        if additional_context:
            messages.append({"role": "user", "content": f"Additional Context from Knowledge Base:\n{additional_context}"})
            
        # 5. Latest Task
        messages.append({"role": "user", "content": user_input})
        
        return messages

    def _call_llm(self, config: LLMConfig, messages: List[Dict[str, Any]], output_model: Optional[Type[BaseModel]]) -> str:
        if config.provider == LLMProvider.OLLAMA:
            return self._call_ollama(config, messages, output_model)
        elif config.provider == LLMProvider.API:
            return self._call_api(config, messages, output_model)
        else:
            raise ValueError("Unsupported provider")

    def _call_ollama(self, config: LLMConfig, messages: List[Dict[str, Any]], output_model: Optional[Type[BaseModel]]) -> str:
        # If output_model is provided, we might want to enforce JSON mode or format instructions
        # For now, we'll just call chat.
        try:
            response = ollama.chat(
                model=config.model_name, 
                messages=messages,
                options=config.parameters
            )
            return response['message']['content']
        except ollama.ResponseError as e:
            # Re-raise to be caught by the run loop
            raise e
        except Exception as e:
             # Wrap other ollama connection errors if needed or let them bubble up
             raise e

    def _call_api(self, config: LLMConfig, messages: List[Dict[str, Any]], output_model: Optional[Type[BaseModel]]) -> str:
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model_name,
            "messages": messages,
            **config.parameters
        }
        
        url = config.api_base_url
        response = requests.post(url, headers=headers, json=payload)
        
        # Raise HTTPError for bad responses (4xx, 5xx)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
