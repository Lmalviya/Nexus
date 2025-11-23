from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from database import get_db_connection
from cryptography.fernet import Fernet
import jwt
import os
import base64
import hashlib

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

# Generate encryption key from JWT_SECRET (for consistency)
def get_encryption_key():
    # Use SHA256 to create a 32-byte key from JWT_SECRET
    key = hashlib.sha256(JWT_SECRET.encode()).digest()
    return base64.urlsafe_b64encode(key)

cipher = Fernet(get_encryption_key())

class AddKeyRequest(BaseModel):
    provider: str
    key_name: str
    api_key: str

class UpdateKeyRequest(BaseModel):
    key_name: str = None
    api_key: str = None

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
def add_api_key(request: AddKeyRequest, user_data: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        # Encrypt the API key
        encrypted_key = cipher.encrypt(request.api_key.encode()).decode()
        
        # Insert into database
        cur.execute(
            """INSERT INTO api_keys (organization_id, user_id, provider, key_name, encrypted_key) 
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (org_id, user_id, request.provider, request.key_name, encrypted_key)
        )
        
        key_record = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "key": {
                "id": str(key_record['id']),
                "provider": key_record['provider'],
                "key_name": key_record['key_name'],
                "created_at": key_record['created_at'].isoformat()
            }
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add API key")

@router.get("")
def list_api_keys(user_data: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        user_id = user_data['sub']
        org_id = user_data.get('org_id')
        
        # Get all keys for this organization
        cur.execute(
            """SELECT id, provider, key_name, encrypted_key, created_at 
               FROM api_keys 
               WHERE organization_id = %s 
               ORDER BY created_at DESC""",
            (org_id,)
        )
        
        keys = cur.fetchall()
        cur.close()
        conn.close()
        
        # Return keys (without decrypting for security)
        return {
            "status": "success",
            "keys": [
                {
                    "id": str(k['id']),
                    "provider": k['provider'],
                    "key_name": k['key_name'],
                    "created_at": k['created_at'].isoformat(),
                    # Only return masked key
                    "key_preview": "••••••••"
                }
                for k in keys
            ]
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch API keys")

@router.put("/{key_id}")
def update_api_key(key_id: str, request: UpdateKeyRequest, user_data: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        org_id = user_data.get('org_id')
        
        # Check if key exists and belongs to organization
        cur.execute(
            "SELECT * FROM api_keys WHERE id = %s AND organization_id = %s",
            (key_id, org_id)
        )
        
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Build update query dynamically
        updates = []
        params = []
        
        if request.key_name:
            updates.append("key_name = %s")
            params.append(request.key_name)
        
        if request.api_key:
            encrypted_key = cipher.encrypt(request.api_key.encode()).decode()
            updates.append("encrypted_key = %s")
            params.append(encrypted_key)
        
        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = NOW()")
        params.append(key_id)
        
        query = f"UPDATE api_keys SET {', '.join(updates)} WHERE id = %s RETURNING *"
        cur.execute(query, params)
        
        updated_key = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "key": {
                "id": str(updated_key['id']),
                "provider": updated_key['provider'],
                "key_name": updated_key['key_name'],
                "updated_at": updated_key['updated_at'].isoformat()
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update API key")

@router.delete("/{key_id}")
def delete_api_key(key_id: str, user_data: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        org_id = user_data.get('org_id')
        
        # Delete key (only if belongs to organization)
        cur.execute(
            "DELETE FROM api_keys WHERE id = %s AND organization_id = %s RETURNING id",
            (key_id, org_id)
        )
        
        deleted = cur.fetchone()
        
        if not deleted:
            conn.close()
            raise HTTPException(status_code=404, detail="API key not found")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "message": "API key deleted"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")

@router.get("/{key_id}/decrypt")
def get_decrypted_key(key_id: str, user_data: dict = Depends(get_current_user)):
    """Get decrypted API key (use with caution, only when needed)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        org_id = user_data.get('org_id')
        
        cur.execute(
            "SELECT encrypted_key FROM api_keys WHERE id = %s AND organization_id = %s",
            (key_id, org_id)
        )
        
        result = cur.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Decrypt the key
        decrypted_key = cipher.decrypt(result['encrypted_key'].encode()).decode()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "api_key": decrypted_key
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to decrypt API key")
