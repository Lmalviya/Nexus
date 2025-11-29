from typing import List, Optional
from pydantic import BaseModel, Field
import re
import logging
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import chat as prompts
from llms_host.config import LLMConfig

logger = logging.getLogger(__name__)

class ChatInput(BaseModel):
    """Input model for chat agent.
    
    Attributes:
        user_message: The user's text message
        images: Optional list of base64-encoded images
        session_id: The session ID for tracking
        additional_context: Optional additional context (e.g., from vector DB)
    """
    user_message: str = Field(..., description="The user's message")
    images: Optional[List[str]] = Field(None, description="Base64-encoded images")
    session_id: str = Field(..., description="Session ID")
    additional_context: Optional[str] = Field(None, description="Additional context from retrieval")

class ChatOutput(BaseModel):
    """Output model for chat agent.
    
    Attributes:
        response: The main response text
        artifact_type: Type of artifact if generated ("code", "markdown", "diagram", or None)
        artifact_language: Language/format of artifact (e.g., "python", "mermaid")
        artifact_content: The actual artifact content
    """
    response: str = Field(..., description="The main response text")
    artifact_type: Optional[str] = Field(None, description="Type of artifact: code, markdown, diagram")
    artifact_language: Optional[str] = Field(None, description="Language or format of the artifact")
    artifact_content: Optional[str] = Field(None, description="The artifact content")

class ChatAgent(BaseAgent):
    """General-purpose chat agent with multimodal support and artifact generation.
    
    This agent can:
    - Accept text and images as input
    - Generate various output types: chat messages, code, markdown, diagrams
    - Intelligently decide output format based on user intent
    - Maintain conversation context
    """
    
    def __init__(self):
        super().__init__(agent_name="chat", prompts_module=prompts)

    def chat(self, input_data: ChatInput, llm_config: LLMConfig) -> ChatOutput:
        """Process a chat message and generate an appropriate response.
        
        Args:
            input_data: ChatInput containing message, optional images, and context
            llm_config: LLM configuration to use
            
        Returns:
            ChatOutput containing response and optional artifact
        """
        
        # Prepare the user input
        user_input = input_data.user_message
        
        # If images are provided, indicate multimodal input
        # Note: Full multimodal support requires BaseAgent enhancement
        if input_data.images and len(input_data.images) > 0:
            user_input = f"[User provided {len(input_data.images)} image(s)]\n\n{user_input}"
        
        # Call the base agent's run method
        response_text = self.run(
            user_input=user_input,
            session_id=input_data.session_id,
            llm_config=llm_config,
            additional_context=input_data.additional_context
        )
        
        # Parse the response for artifacts
        artifact_type, artifact_language, artifact_content, clean_response = self._extract_artifact(response_text)
        
        return ChatOutput(
            response=clean_response,
            artifact_type=artifact_type,
            artifact_language=artifact_language,
            artifact_content=artifact_content
        )

    def _extract_artifact(self, response: str) -> tuple:
        """Extract artifact from response if present.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            Tuple of (artifact_type, artifact_language, artifact_content, clean_response)
        """
        
        # Pattern to match artifact blocks: ```artifact:type:language
        artifact_pattern = r'```artifact:(code|markdown|diagram):(\w+)\n(.*?)```'
        
        match = re.search(artifact_pattern, response, re.DOTALL)
        
        if match:
            artifact_type = match.group(1)
            artifact_language = match.group(2)
            artifact_content = match.group(3).strip()
            
            # Remove the artifact block from the response
            clean_response = re.sub(artifact_pattern, '', response, flags=re.DOTALL).strip()
            
            logger.info(f"Extracted {artifact_type} artifact in {artifact_language}")
            return artifact_type, artifact_language, artifact_content, clean_response
        
        # No artifact found
        return None, None, None, response
