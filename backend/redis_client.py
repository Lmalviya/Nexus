import redis
import json
import os
from datetime import datetime
import uuid

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def create_session(user_id: str, org_id: str, title: str = None):
    """Create a new conversation session"""
    session_id = str(uuid.uuid4())
    
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "organization_id": org_id,
        "title": title or "New Conversation",
        "messages": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tokens": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Store conversation
    key = f"conversation:{session_id}"
    redis_client.set(key, json.dumps(session_data))
    
    # Add to user's session list
    sessions_key = f"sessions:{org_id}:{user_id}"
    redis_client.lpush(sessions_key, session_id)
    
    return session_data

def get_session(org_id: str, user_id: str, session_id: str):
    """Get a conversation session"""
    key = f"conversation:{session_id}"
    data = redis_client.get(key)
    
    if data:
        return json.loads(data)
    return None

def list_sessions(org_id: str, user_id: str, limit: int = 50):
    """List all sessions for a user"""
    sessions_key = f"sessions:{org_id}:{user_id}"
    session_ids = redis_client.lrange(sessions_key, 0, limit - 1)
    
    sessions = []
    for session_id in session_ids:
        session = get_session(org_id, user_id, session_id)
        if session:
            # Return summary without full message history
            sessions.append({
                "session_id": session["session_id"],
                "title": session["title"],
                "message_count": len(session["messages"]),
                "total_tokens": session["total_tokens"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            })
    
    return sessions

def add_message(org_id: str, user_id: str, session_id: str, message_data: dict):
    """Add a message to a conversation"""
    session = get_session(org_id, user_id, session_id)
    
    if not session:
        raise ValueError("Session not found")
    
    # Add message ID and timestamp if not present
    if "id" not in message_data:
        message_data["id"] = str(uuid.uuid4())
    if "timestamp" not in message_data:
        message_data["timestamp"] = datetime.utcnow().isoformat()
    
    # Add message to session
    session["messages"].append(message_data)
    
    # Update token counts
    if "input_tokens" in message_data:
        session["total_input_tokens"] += message_data["input_tokens"]
    if "output_tokens" in message_data:
        session["total_output_tokens"] += message_data["output_tokens"]
    if "total_tokens" in message_data:
        session["total_tokens"] += message_data["total_tokens"]
    
    # Update timestamp
    session["updated_at"] = datetime.utcnow().isoformat()
    
    # Auto-generate title from first user message if not set
    if session["title"] == "New Conversation" and message_data["role"] == "user":
        # Use first 50 chars of first message as title
        session["title"] = message_data["content"][:50] + ("..." if len(message_data["content"]) > 50 else "")
    
    # Save updated session
    key = f"conversation:{session_id}"
    redis_client.set(key, json.dumps(session))
    
    return session

def delete_session(org_id: str, user_id: str, session_id: str):
    """Delete a conversation session"""
    # Remove from conversation store
    key = f"conversation:{session_id}"
    redis_client.delete(key)
    
    # Remove from user's session list
    sessions_key = f"sessions:{org_id}:{user_id}"
    redis_client.lrem(sessions_key, 0, session_id)
    
    return True

def update_session_title(org_id: str, user_id: str, session_id: str, title: str):
    """Update session title"""
    session = get_session(org_id, user_id, session_id)
    
    if not session:
        raise ValueError("Session not found")
    
    session["title"] = title
    session["updated_at"] = datetime.utcnow().isoformat()
    
    key = f"conversation:{session_id}"
    redis_client.set(key, json.dumps(session))
    
    return session

def update_message(org_id: str, user_id: str, session_id: str, message_id: str, new_content: str):
    """Update a message's content"""
    session = get_session(org_id, user_id, session_id)
    
    if not session:
        raise ValueError("Session not found")
    
    # Find and update the message
    message_found = False
    for msg in session["messages"]:
        if msg["id"] == message_id:
            msg["content"] = new_content
            msg["timestamp"] = datetime.utcnow().isoformat()
            message_found = True
            break
    
    if not message_found:
        raise ValueError("Message not found")
    
    session["updated_at"] = datetime.utcnow().isoformat()
    
    key = f"conversation:{session_id}"
    redis_client.set(key, json.dumps(session))
    
    return session

def delete_message_and_after(org_id: str, user_id: str, session_id: str, message_id: str):
    """Delete a message and all messages after it (for editing/regeneration)"""
    session = get_session(org_id, user_id, session_id)
    
    if not session:
        raise ValueError("Session not found")
    
    # Find message index
    message_index = None
    for i, msg in enumerate(session["messages"]):
        if msg["id"] == message_id:
            message_index = i
            break
    
    if message_index is None:
        raise ValueError("Message not found")
    
    # Remove message and all after it
    deleted_messages = session["messages"][message_index:]
    session["messages"] = session["messages"][:message_index]
    
    # Recalculate token counts
    session["total_input_tokens"] = sum(msg.get("input_tokens", 0) for msg in session["messages"])
    session["total_output_tokens"] = sum(msg.get("output_tokens", 0) for msg in session["messages"])
    session["total_tokens"] = sum(msg.get("total_tokens", 0) for msg in session["messages"])
    
    session["updated_at"] = datetime.utcnow().isoformat()
    
    key = f"conversation:{org_id}:{user_id}:{session_id}"
    redis_client.set(key, json.dumps(session))
    
    return {
        "session": session,
        "deleted_count": len(deleted_messages)
    }
