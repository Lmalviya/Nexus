from pydantic import BaseModel, Field
from typing import Optional
from llms_host.agents.base_agent import BaseAgent
from llms_host.prompts import query_re_writer as prompts
from llms_host.config import LLMConfig

class QueryRewriteInput(BaseModel):
    user_query: str = Field(..., description="The original user query")
    session_id: str = Field(..., description="The session ID")
    additional_context: Optional[str] = Field(None, description="Any additional context from vector DB")

class QueryRewriteOutput(BaseModel):
    rewritten_query: str = Field(..., description="The rewritten query")

class QueryReWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="query_rewriter", prompts_module=prompts)

    def rewrite_query(self, input_data: QueryRewriteInput, llm_config: LLMConfig) -> QueryRewriteOutput:
        """
        Rewrites the user query.
        """
        response_text = self.run(
            user_input=input_data.user_query,
            session_id=input_data.session_id,
            llm_config=llm_config,
            additional_context=input_data.additional_context,
            output_model=QueryRewriteOutput
        )
        
        return QueryRewriteOutput(rewritten_query=response_text)
