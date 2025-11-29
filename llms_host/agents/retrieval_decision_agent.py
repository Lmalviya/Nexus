from pydantic import BaseModel, Field
from typing import Optional
import json
import logging
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import retrieval_decision as prompts
from llms_host.config import LLMConfig

logger = logging.getLogger(__name__)

class RetrievalDecisionInput(BaseModel):
    user_query: str = Field(..., description="The user's query to analyze")
    session_id: str = Field(..., description="The session ID")
    additional_context: Optional[str] = Field(None, description="Any additional context")

class RetrievalDecisionOutput(BaseModel):
    needs_retrieval: bool = Field(..., description="True if vector DB retrieval is needed, False otherwise")
    reason: str = Field(..., description="Explanation for the decision")

class RetrievalDecisionAgent(BaseAgent):
    """
    Agent that determines whether a user query requires retrieving data from the vector database.
    Returns True if retrieval is needed, False if the query can be answered directly.
    """
    def __init__(self):
        super().__init__(agent_name="retrieval_decision", prompts_module=prompts)
    
    def decide(self, input_data: RetrievalDecisionInput, llm_config: LLMConfig) -> RetrievalDecisionOutput:
        """
        Analyzes the user query and decides if vector database retrieval is needed.
        
        Args:
            input_data: The input containing user query and context
            llm_config: LLM configuration
            
        Returns:
            RetrievalDecisionOutput with needs_retrieval boolean and reason
        """
        response_text = self.run(
            user_input=input_data.user_query,
            session_id=input_data.session_id,
            llm_config=llm_config,
            additional_context=input_data.additional_context
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
            return RetrievalDecisionOutput(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Retrieval Decision Agent: {e}. Response: {response_text}")
            # Fallback logic: if we can't parse, assume retrieval is needed to be safe
            return RetrievalDecisionOutput(
                needs_retrieval=True, 
                reason=f"Fallback: Failed to parse decision, defaulting to retrieval for safety. Error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Retrieval Decision Agent: {e}")
            return RetrievalDecisionOutput(
                needs_retrieval=True, 
                reason=f"Error: {str(e)}. Defaulting to retrieval for safety."
            )
