from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import summarizer as prompts
from llms_host.config import LLMConfig, get_agent_config

class SummarizerInput(BaseModel):
    messages: List[Dict[str, Any]] = Field(..., description="List of messages to summarize")
    session_id: str = Field(..., description="The session ID")

class SummarizerOutput(BaseModel):
    summary: str = Field(..., description="The generated summary")

class SummarizerAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="summarizer", prompts_module=prompts)

    def summarize(self, messages: List[Dict[str, Any]], session_id: str = "internal_summary") -> str:
        """
        Summarizes the list of messages.
        Note: This method signature is slightly different because it's often called internally
        by Conversation.py which might not pass full config every time.
        We'll fetch default config if needed.
        """
        # Convert messages to a string representation for the prompt
        messages_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        # Get default config for summarizer
        llm_config = get_agent_config("summarizer")
        
        response_text = self.run(
            user_input=f"Summarize these messages:\n{messages_text}",
            session_id=session_id,
            llm_config=llm_config
        )
        
        return response_text
