"""Agent endpoints router."""

from fastapi import APIRouter, HTTPException
import logging

from llms_host.api.models import (
    RewriteRequest,
    SummarizeRequest,
    DescriptionRequest,
    ChatRequest,
    RetrievalDecisionRequest,
    RouterRequest,
    SQLRequest
)
from llms_host.api.dependencies import resolve_llm_config
from llms_host.agents.query_re_writer_agent import QueryReWriterAgent, QueryRewriteInput
from llms_host.agents.summarizer import SummarizerAgent
from llms_host.agents.table_description_agent import TableDescriptionAgent, TableDescriptionInput
from llms_host.agents.image_description_agent import ImageDescriptionAgent, ImageDescriptionInput
from llms_host.agents.chat_agent import ChatAgent, ChatInput
from llms_host.agents.retrieval_decision_agent import RetrievalDecisionAgent, RetrievalDecisionInput
from llms_host.agents.rag_router_agent import RouterAgent, RouterInput
from llms_host.agents.sql_agent import SQLAgent, SQLInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agents"])


@router.post("/rewrite")
async def rewrite_query(request: RewriteRequest):
    """Rewrite user query for better retrieval."""
    try:
        config = resolve_llm_config(request.llm_config, "query_rewriter")
        
        input_data = QueryRewriteInput(
            user_query=request.user_query,
            session_id=request.session_id,
            additional_context=request.additional_context
        )

        agent = QueryReWriterAgent()
        result = agent.rewrite_query(input_data, config)
        return result

    except Exception as e:
        logger.error(f"Error in rewrite_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_conversation(request: SummarizeRequest):
    """Summarize conversation history."""
    try:
        agent = SummarizerAgent()
        summary = agent.summarize(request.messages, request.session_id)
        return {"summary": summary}

    except Exception as e:
        logger.error(f"Error in summarize_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/describe")
async def generate_description(request: DescriptionRequest):
    """Generate description for table or image content."""
    try:
        if request.content_type == "table":
            config = resolve_llm_config(request.llm_config, "table_description")
            
            input_data = TableDescriptionInput(
                headers=request.data.get("headers", []),
                sample_rows=request.data.get("sample_rows", []),
                session_id=request.session_id,
                additional_context=request.data.get("additional_context")
            )
            
            agent = TableDescriptionAgent()
            result = agent.generate_description(input_data, config)
            return result
            
        elif request.content_type == "image":
            config = resolve_llm_config(request.llm_config, "image_description")
            
            input_data = ImageDescriptionInput(
                image_data=request.data.get("image_data", ""),
                session_id=request.session_id,
                additional_context=request.data.get("additional_context")
            )
            
            agent = ImageDescriptionAgent()
            result = agent.generate_description(input_data, config)
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content_type: {request.content_type}. Must be 'table' or 'image'."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """General-purpose chat with multimodal support and artifact generation."""
    try:
        config = resolve_llm_config(request.llm_config, "chat")

        input_data = ChatInput(
            user_message=request.user_message,
            images=request.images,
            session_id=request.session_id,
            additional_context=request.additional_context
        )
        
        agent = ChatAgent()
        result = agent.chat(input_data, config)
        return result

    except Exception as e:
        logger.error(f"Error in chat_with_agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieval-decision")
async def decide_retrieval(request: RetrievalDecisionRequest):
    """Determine if vector database retrieval is needed for the query."""
    try:
        config = resolve_llm_config(request.llm_config, "retrieval_decision")
        
        input_data = RetrievalDecisionInput(
            user_query=request.user_query,
            session_id=request.session_id,
            additional_context=request.additional_context
        )

        agent = RetrievalDecisionAgent()
        result = agent.decide(input_data, config)
        return result

    except Exception as e:
        logger.error(f"Error in decide_retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route")
async def route_query(request: RouterRequest):
    """Route query to SQL or vector search based on retrieved context."""
    try:
        config = resolve_llm_config(request.llm_config, "router")
        
        input_data = RouterInput(
            user_query=request.user_query,
            retrieved_context=request.retrieved_context,
            session_id=request.session_id
        )

        agent = RouterAgent()
        result = agent.route(input_data, config)
        return result

    except Exception as e:
        logger.error(f"Error in route_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sql")
async def generate_sql(request: SQLRequest):
    """Generate SQL query based on user request and context."""
    try:
        config = resolve_llm_config(request.llm_config, "sql_agent")
        
        input_data = SQLInput(
            user_query=request.user_query,
            context=request.context,
            session_id=request.session_id
        )

        agent = SQLAgent()
        result = agent.generate_sql(input_data, config)
        return result

    except Exception as e:
        logger.error(f"Error in generate_sql: {e}")
        raise HTTPException(status_code=500, detail=str(e))
