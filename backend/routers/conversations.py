from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import jwt
import os
import redis_client
import httpx
import uuid
from datetime import datetime
from utils.db_connection import get_db_connection

router = APIRouter(prefix="/conversations", tags=["conversations"])

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ORCHESTRATION_URL = os.getenv("ORCHESTRATION_URL", "http://orchestration:8001")

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class AddMessageRequest(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateTitleRequest(BaseModel):
    title: str

class ChatRequest(BaseModel):
    user_message: str
    images: Optional[List[str]] = None
    model: Optional[str] = None
    provider: Optional[str] = None

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("")
def create_session(request: CreateSessionRequest, user_data: dict = Depends(get_current_user)):
    """Create a new conversation session"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        session = redis_client.create_session(user_id, org_id, request.title)
        
        return {
            "status": "success",
            "session": session
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("")
def list_sessions(user_data: dict = Depends(get_current_user)):
    """List all conversation sessions for the user"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        sessions = redis_client.list_sessions(org_id, user_id)
        
        return {
            "status": "success",
            "sessions": sessions
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")

@router.get("/{session_id}")
def get_session(session_id: str, user_data: dict = Depends(get_current_user)):
    """Get a specific conversation session with full message history"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        session = redis_client.get_session(org_id, user_id, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "success",
            "session": session
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session")

@router.post("/{session_id}/messages")
def add_message(session_id: str, request: AddMessageRequest, user_data: dict = Depends(get_current_user)):
    """Add a message to a conversation session"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        message_data = request.dict()
        
        session = redis_client.add_message(org_id, user_id, session_id, message_data)
        
        return {
            "status": "success",
            "session": session
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")

@router.put("/{session_id}/title")
def update_title(session_id: str, request: UpdateTitleRequest, user_data: dict = Depends(get_current_user)):
    """Update session title"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        session = redis_client.update_session_title(org_id, user_id, session_id, request.title)
        
        return {
            "status": "success",
            "session": session
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update title")

@router.delete("/{session_id}")
def delete_session(session_id: str, user_data: dict = Depends(get_current_user)):
    """Delete a conversation session"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        redis_client.delete_session(org_id, user_id, session_id)
        
        return {
            "status": "success",
            "message": "Session deleted"
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.put("/{session_id}/messages/{message_id}")
def update_message(session_id: str, message_id: str, request: AddMessageRequest, user_data: dict = Depends(get_current_user)):
    """Update a message's content"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        session = redis_client.update_message(org_id, user_id, session_id, message_id, request.content)
        
        return {
            "status": "success",
            "session": session
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update message")

@router.delete("/{session_id}/messages/{message_id}")
def delete_message_and_after(session_id: str, message_id: str, user_data: dict = Depends(get_current_user)):
    """Delete a message and all messages after it"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        result = redis_client.delete_message_and_after(org_id, user_id, session_id, message_id)
        
        return {
            "status": "success",
            "session": result["session"],
            "deleted_count": result["deleted_count"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete messages")

@router.post("/{session_id}/regenerate")
def regenerate_response(session_id: str, user_data: dict = Depends(get_current_user)):
    """Regenerate response from last user message (deletes last assistant message)"""
    try:
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        session = redis_client.get_session(org_id, user_id, session_id)
        
        if not session or not session["messages"]:
            raise HTTPException(status_code=404, detail="Session not found or empty")
        
        # Find last assistant message and delete it
        last_assistant_idx = None
        for i in range(len(session["messages"]) - 1, -1, -1):
            if session["messages"][i]["role"] == "assistant":
                last_assistant_idx = i
                break
        
        if last_assistant_idx is not None:
            message_id = session["messages"][last_assistant_idx]["id"]
            result = redis_client.delete_message_and_after(org_id, user_id, session_id, message_id)
            return {
                "status": "success",
                "session": result["session"],
                "message": "Last assistant message deleted. Ready to regenerate."
            }
        else:
            return {
                "status": "success",
                "session": session,
                "message": "No assistant message to regenerate"
            }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate")


@router.post("/{session_id}/chat")
async def chat_with_orchestration(
    session_id: str,
    request: ChatRequest,
    user_data: dict = Depends(get_current_user)
):
    """
    Send chat message through orchestration service.
    Handles: retrieval decision, context retrieval, chat response.
    """
    user_id = user_data['sub']
    org_id = user_data.get('org_id')
    
    # Create user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.user_message,
        "timestamp": datetime.utcnow().isoformat(),
        "model": request.model,
        "provider": request.provider
    }
    
    # Fetch API key if provider is specified
    api_key = None
    api_base_url = None
    
    if request.provider:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT api_key_encrypted, api_base_url 
                FROM user_api_keys 
                WHERE user_id = %s AND provider = %s
            """, (user_id, request.provider))
            row = cursor.fetchone()
            if row:
                from utils.encryption import decrypt_value
                api_key = decrypt_value(row[0])
                api_base_url = row[1]
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching API key: {e}")
            # Continue without key (orchestration might use system default or fail)

    try:
        # Call orchestration service
        async with httpx.AsyncClient(timeout=90.0) as client:
            orch_response = await client.post(
                f"{ORCHESTRATION_URL}/api/v1/orchestration/chat",
                json={
                    "user_message": request.user_message,
                    "images": request.images,
                    "session_id": session_id,
                    "user_id": user_id,
                    "org_id": org_id,
                    "model": request.model,
                    "provider": request.provider,
                    "api_key": api_key,
                    "api_base_url": api_base_url
                }
            )
            orch_response.raise_for_status()
            orch_data = orch_response.json()
        
        # Store user message
        redis_client.add_message(org_id, user_id, session_id, user_msg)
        
        # Create assistant message with orchestration data
        assistant_msg = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": orch_data["response"],
            "timestamp": datetime.utcnow().isoformat(),
            "model": orch_data.get("model_used", request.model),
            "provider": request.provider,
            "artifact_type": orch_data.get("artifact_type"),
            "artifact_language": orch_data.get("artifact_language"),
            "artifact_content": orch_data.get("artifact_content"),
            "retrieval_used": orch_data.get("retrieval_used", False),
            "retrieval_count": orch_data.get("retrieval_count", 0),
            "retrieval_sources": orch_data.get("retrieval_sources"),
            "model_switched": orch_data.get("model_switched", False),
            "switch_reason": orch_data.get("switch_reason")
        }
        
        # Store assistant message
        session = redis_client.add_message(org_id, user_id, session_id, assistant_msg)
        
        return {
            "status": "success",
            "session": session,
            "orchestration_response": orch_data
        }
        
    except httpx.HTTPError as e:
        print(f"Orchestration service error: {e}")
        raise HTTPException(status_code=503, detail="Orchestration service unavailable")
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
