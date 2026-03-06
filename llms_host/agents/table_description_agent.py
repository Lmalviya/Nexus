from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import table_description as prompts
from llms_host.config import LLMConfig

class TableDescriptionInput(BaseModel):
    """Input model for table description generation.
    
    Attributes:
        headers: List of column names from the table
        sample_rows: Sample rows from the table (list of lists or list of dicts)
        session_id: The session ID for tracking
        additional_context: Optional context about the table source or purpose
    """
    headers: List[str] = Field(..., description="Column headers from the table")
    sample_rows: List[List[Any]] = Field(..., description="Sample rows from the table")
    session_id: str = Field(..., description="The session ID")
    additional_context: Optional[str] = Field(None, description="Additional context about the table")

class TableDescriptionOutput(BaseModel):
    """Output model for table description.
    
    Attributes:
        description: The generated semantic description of the table
    """
    description: str = Field(..., description="The generated semantic description")

class TableDescriptionAgent(BaseAgent):
    """Agent specialized in generating semantic descriptions for tabular data.
    
    This agent analyzes CSV/table structures (headers and sample rows) and generates
    concise, semantic descriptions optimized for information retrieval and search.
    """
    
    def __init__(self):
        super().__init__(agent_name="table_description", prompts_module=prompts)

    def generate_description(
        self, 
        input_data: TableDescriptionInput, 
        llm_config: LLMConfig
    ) -> TableDescriptionOutput:
        """Generate a semantic description for the given table data.
        
        Args:
            input_data: TableDescriptionInput containing headers and sample rows
            llm_config: LLM configuration to use for generation
            
        Returns:
            TableDescriptionOutput containing the generated description
        """
        
        # Format the table data for the LLM
        headers_str = ", ".join(input_data.headers)
        rows_str = "\n".join([", ".join(map(str, row)) for row in input_data.sample_rows[:5]])
        
        user_query = f"""Describe this table:
Headers: {headers_str}
Sample rows:
{rows_str}"""
        
        if input_data.additional_context:
            user_query += f"\n\nAdditional context: {input_data.additional_context}"

        response_text = self.run(
            user_input=user_query,
            session_id=input_data.session_id,
            llm_config=llm_config,
            output_model=TableDescriptionOutput
        )
        
        return TableDescriptionOutput(description=response_text)
