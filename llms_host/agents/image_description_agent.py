from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import image_description as prompts
from llms_host.config import LLMConfig

class ImageDescriptionInput(BaseModel):
    """Input model for image description generation.
    
    Attributes:
        image_data: Base64 encoded image string or image path
        conversation_id: The conversation ID for tracking
        additional_context: Optional context about the image (e.g., source, purpose)
    """
    image_data: str = Field(..., description="Base64 encoded image or image path")
    conversation_id: str = Field(..., description="The conversation ID")
    additional_context: Optional[str] = Field(None, description="Additional context about the image")

class ImageDescriptionOutput(BaseModel):
    """Output model for image description.
    
    Attributes:
        description: The generated detailed description of the image
    """
    description: str = Field(..., description="The generated detailed image description")

class ImageDescriptionAgent(BaseAgent):
    """Agent specialized in generating detailed descriptions for images using VLM.
    
    This agent uses Vision Language Models (VLM) to analyze images and generate
    comprehensive, semantic descriptions optimized for retrieval and understanding.
    """
    
    def __init__(self):
        super().__init__(agent_name="image_description", prompts_module=prompts)

    def generate_description(
        self, 
        input_data: ImageDescriptionInput, 
        llm_config: LLMConfig
    ) -> ImageDescriptionOutput:
        """Generate a detailed description for the given image.
        
        Args:
            input_data: ImageDescriptionInput containing image data
            llm_config: LLM configuration to use (should be a VLM model)
            
        Returns:
            ImageDescriptionOutput containing the generated description
        """
        
        # For VLM models, we need to format the request differently
        # The image_data could be base64 or a path
        # The BaseAgent's run method will need to handle multimodal input
        # For now, we'll pass the image reference in the user query
        
        user_query = "Describe this image in detail."
        
        if input_data.additional_context:
            user_query += f"\n\nContext: {input_data.additional_context}"

        # Note: The actual image passing mechanism depends on how BaseAgent.run
        # handles multimodal inputs. This might need adjustment based on the
        # LLM provider's API (Ollama's vision API format)
        
        response_text = self.run(
            user_input=user_query,
            conversation_id=input_data.conversation_id,
            llm_config=llm_config,
            output_model=ImageDescriptionOutput,
            # We may need to add image_data as a separate parameter
            # or modify the run method to accept multimodal inputs
            image=input_data.image_data  # This parameter might need to be added to BaseAgent.run
        )
        
        return ImageDescriptionOutput(description=response_text)
