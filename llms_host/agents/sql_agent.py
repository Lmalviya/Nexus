from typing import List, Optional
from pydantic import BaseModel, Field
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import sql as prompts
from llms_host.config import LLMConfig

class SQLInput(BaseModel):
    user_query: str = Field(..., description="The user's query")
    context: List[str] = Field(..., description="Relevant context to help generate the SQL")
    conversation_id: str = Field(..., description="The conversation ID")

class SQLOutput(BaseModel):
    sql_query: str = Field(..., description="The generated SQL query")

class SQLAgent(BaseAgent):
    """
    Agent responsible for generating SQL queries based on user request and context.
    """
    def __init__(self):
        super().__init__(agent_name="sql_agent", prompts_module=prompts)
    
    def generate_sql(self, input_data: SQLInput, llm_config: LLMConfig) -> SQLOutput:
        """
        Generates a SQL query.
        """
        context_str = "\n".join(input_data.context)
        
        response_text = self.run(
            user_input=input_data.user_query,
            conversation_id=input_data.conversation_id,
            llm_config=llm_config,
            additional_context=context_str
        )
        
        # Clean up potential markdown code blocks
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```sql"):
            cleaned_response = cleaned_response[6:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
            
        return SQLOutput(sql_query=cleaned_response.strip())
