from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import os

class LLMProvider(Enum):
    OLLAMA = "ollama"
    API = "api"

class AgentName(Enum):
    SUMMARIZER = "summarizer"
    QUERY_REWRITER = "query_rewriter"
    ROUTER = "router"
    SQL_AGENT = "sql_agent"
    TABLE_DESCRIPTION = "table_description"
    IMAGE_DESCRIPTION = "image_description"
    CHAT = "chat"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=lambda: {"temperature": 0.7, "top_p": 0.9})

    # def __post_init__(self):
    def validate(self) -> bool:
        """
        Validates the configuration based on the provider.
        Returns True if valid, raises ValueError otherwise.
        """
        if self.provider == LLMProvider.API:
            if not self.api_key:
                raise ValueError(f"API key does not provided: {self.api_key}")
            if not self.api_base_url:
                raise ValueError(f"API base URL does not provided: {self.api_base_url}")
            if not self.model_name:
                raise ValueError(f"Model name does not provided: {self.model_name}")

        elif self.provider == LLMProvider.OLLAMA:
            if not self.model_name:
                raise ValueError("Ollama provider requires a model_name.")
            
        return True
 
def get_agent_config(agent_name: str) -> LLMConfig:
    AGENT_CONFIGS: Dict[AgentName, LLMConfig] = {
        AgentName.SUMMARIZER: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3",
            parameters={"temperature": 0.2}
        ),
        AgentName.QUERY_REWRITER: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3",
            parameters={"temperature": 0.5}
        ),
        AgentName.ROUTER: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3",
            parameters={"temperature": 0.1}
        ),
        AgentName.SQL_AGENT: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3", # Or a code-specific model
            parameters={"temperature": 0.1}
        ),
        AgentName.TABLE_DESCRIPTION: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llama3",
            parameters={"temperature": 0.2}
        ),
        AgentName.IMAGE_DESCRIPTION: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="llava",  # Vision Language Model for image analysis
            parameters={"temperature": 0.3}
        ),
        AgentName.CHAT: LLMConfig(
            provider=LLMProvider.OLLAMA,
            model_name="qwen2.5:32b",  # Best balance of quality and performance
            parameters={"temperature": 0.7}  # Higher temperature for creative responses
        ),
    }
    try:
        agent_enum = AgentName(agent_name)
        return AGENT_CONFIGS.get(agent_enum)
    except ValueError:
        raise ValueError(f"Unknown agent name: {agent_name}")
