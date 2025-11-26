from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import logging
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import router as prompts
from llms_host.config import LLMConfig

logger = logging.getLogger(__name__)

class RouterInput(BaseModel):
    user_query: str = Field(..., description="The user's query")
    retrieved_context: List[str] = Field(..., description="Context retrieved from the vector database")
    conversation_id: str = Field(..., description="The conversation ID")

class RouterOutput(BaseModel):
    decision: str = Field(..., description="The decision: 'sql' or 'vector'")
    reason: str = Field(..., description="The explanation for the decision")

class RouterAgent(BaseAgent):
    """
    Agent responsible for routing the query based on retrieved context.
    It decides if a SQL query is needed or if the vector store context is sufficient.
    """
    def __init__(self):
        super().__init__(agent_name="router", prompts_module=prompts)
    
    def route(self, input_data: RouterInput, llm_config: LLMConfig) -> RouterOutput:
        """
        Analyzes the user query and retrieved context to decide the next step.
        """
        context_str = "\n".join(input_data.retrieved_context)
        
        response_text = self.run(
            user_input=input_data.user_query,
            conversation_id=input_data.conversation_id,
            llm_config=llm_config,
            additional_context=context_str
        )
        
        # Parse JSON response
        try:
            # Clean up potential markdown code blocks
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            data = json.loads(cleaned_response.strip())
            return RouterOutput(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Router Agent: {e}. Response: {response_text}")
            # Fallback logic if JSON parsing fails
            if "sql" in response_text.lower() and "vector" not in response_text.lower():
                 return RouterOutput(decision="sql", reason="Fallback: SQL keyword detected in malformed response")
            return RouterOutput(decision="vector", reason="Fallback: Failed to parse decision, defaulting to vector")
        except Exception as e:
            logger.error(f"Unexpected error in Router Agent: {e}")
            return RouterOutput(decision="vector", reason=f"Error: {str(e)}")
