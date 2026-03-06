from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from utils.db_connection import get_db_connection
from utils.encryption import encrypt_value, decrypt_value
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class APIKeyRequest(BaseModel):
    provider: str = Field(..., description="Model provider (openai, anthropic, ollama)")
    api_key: str = Field(..., description="The API key")
    model_name: Optional[str] = Field(None, description="Default model for this provider")
    api_base_url: Optional[str] = Field(None, description="Base URL for provider")
    user_id: str = Field(..., description="User ID")

class APIKeyResponse(BaseModel):
    provider: str
    model_name: Optional[str]
    api_base_url: Optional[str]
    has_key: bool

@router.post("/keys")
async def save_api_key(request: APIKeyRequest):
    """Save or update a user's API key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        encrypted_key = encrypt_value(request.api_key)
        
        cursor.execute("""
            INSERT INTO user_api_keys (user_id, provider, api_key_encrypted, model_name, api_base_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, provider) 
            DO UPDATE SET 
                api_key_encrypted = EXCLUDED.api_key_encrypted,
                model_name = EXCLUDED.model_name,
                api_base_url = EXCLUDED.api_base_url,
                updated_at = CURRENT_TIMESTAMP
        """, (request.user_id, request.provider, encrypted_key, request.model_name, request.api_base_url))
        
        conn.commit()
        return {"status": "success", "message": "API key saved"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/keys/{user_id}", response_model=List[APIKeyResponse])
async def get_user_keys(user_id: str):
    """Get list of configured providers for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT provider, model_name, api_base_url 
            FROM user_api_keys 
            WHERE user_id = %s
        """, (user_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append(APIKeyResponse(
                provider=row[0],
                model_name=row[1],
                api_base_url=row[2],
                has_key=True
            ))
        
        return results
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.delete("/keys/{user_id}/{provider}")
async def delete_api_key(user_id: str, provider: str):
    """Delete a user's API key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM user_api_keys 
            WHERE user_id = %s AND provider = %s
        """, (user_id, provider))
        
        conn.commit()
        return {"status": "success", "message": "API key deleted"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
