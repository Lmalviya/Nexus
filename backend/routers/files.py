from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.storage import StorageService
from auth_dependency import get_current_user
from database import get_db_connection
import uuid
import os
import requests
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/files", tags=["files"])
storage_service = StorageService()

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

@router.post("/presigned-url")
async def generate_upload_url(request: PresignedUrlRequest, user_data: dict = Depends(get_current_user)):
    """
    Generate a presigned URL for client-side upload to MinIO.
    Requires authentication. Files are stored in user-specific folders.
    """
    # Extract user information from JWT token
    user_id = user_data['sub']
    org_id = user_data.get('org_id')
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID not found in token")
    
    # Generate a unique filename to prevent collisions
    file_extension = request.filename.split('.')[-1] if '.' in request.filename else 'bin'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Generate user-specific folder prefix
    prefix = storage_service.get_user_file_prefix(org_id, user_id)
    
    # Get presigned URL with user-specific prefix
    # Note: We do NOT include content_type in signature to allow flexibility
    url = storage_service.get_presigned_url(unique_filename, prefix=prefix)
    
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
    
    # Full file key includes the prefix
    file_key = f"{prefix}{unique_filename}"
    
    public_url = storage_service.get_file_url(file_key)
    
    return {
        "upload_url": url,
        "file_key": file_key,
        "public_url": public_url,
    }

@router.post("/confirm-upload")
async def confirm_upload(request: dict, user_data: dict = Depends(get_current_user)):
    """
    Confirm that a file was uploaded and save metadata to database.
    Called by the frontend after successful upload.
    """
    file_key = request.get("file_key")
    filename = request.get("filename")
    session_id = request.get("session_id", "default-session")
    content_type = request.get("content_type", "application/octet-stream")
    
    print(f"Confirm upload request: file_key={file_key}, filename={filename}")
    
    if not all([file_key, filename]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    user_id = user_data['sub']
    org_id = user_data.get('org_id')
    expected_prefix = storage_service.get_user_file_prefix(org_id, user_id)
    
    if not file_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Unauthorized: File does not belong to user")
    
    # Get file size from MinIO
    try:
        obj_info = storage_service.s3_client.head_object(Bucket=storage_service.bucket_name, Key=file_key)
        file_size = obj_info['ContentLength']
    except Exception as e:
        print(f"Failed to get file info from MinIO: {e}")
        file_size = 0
    
    # Save metadata to database
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO documents (user_id, organization_id, file_key, filename, content_type, size)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, org_id, file_key, filename, content_type, file_size)
        )
        result = cur.fetchone()
        doc_id = result['id']
        conn.commit()
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save document metadata: {e}")
    finally:
        cur.close()
        conn.close()
    
    # Call orchestration service
    orchestration_result = {}
    try:
        orchestration_url = os.getenv("ORCHESTRATION_URL", "http://orchestration:8001")
        response = requests.post(
            f"{orchestration_url}/process-document",
            json={
                "document_id": str(doc_id),
                "file_key": file_key,
                "filename": filename,
                "session_id": session_id,
                "content_type": content_type,
                "size": file_size
            },
            timeout=5
        )
        # We don't raise error here to avoid failing the upload if orchestration is down
        if response.status_code == 200:
            orchestration_result = response.json()
    except Exception as e:
        print(f"Failed to call orchestration service: {e}")
        orchestration_result = {"status": "error", "message": str(e)}
    
    return {
        "status": "success",
        "document_id": str(doc_id),
        "file_key": file_key,
        "filename": filename,
        "orchestration": orchestration_result
    }

@router.get("")
async def list_files(user_data: dict = Depends(get_current_user)):
    """
    List all files for the authenticated user from the database.
    """
    user_id = user_data['sub']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT file_key, filename, size, created_at as last_modified, content_type
            FROM documents
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        files = cur.fetchall()
        
        # Add public URL to each file
        for file in files:
            file['url'] = storage_service.get_file_url(file['file_key'])
            # Ensure datetime is serialized
            if file['last_modified']:
                file['last_modified'] = file['last_modified'].isoformat()
                
        return files
    finally:
        cur.close()
        conn.close()

@router.delete("/{file_key:path}")
async def delete_file(file_key: str, user_data: dict = Depends(get_current_user), session_id: str = None):
    """
    Delete a file from storage and database.
    """
    user_id = user_data['sub']
    org_id = user_data.get('org_id')
    expected_prefix = storage_service.get_user_file_prefix(org_id, user_id)
    
    if not file_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Delete from MinIO
    success = storage_service.delete_file(file_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")
    
    # Delete from Database
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM documents WHERE file_key = %s AND user_id = %s",
            (file_key, user_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database delete error: {e}")
        # We continue even if DB delete fails (orphan record is better than zombie file)
    finally:
        cur.close()
        conn.close()
    
    # Call orchestration service for cleanup
    if session_id:
        try:
            orchestration_url = os.getenv("ORCHESTRATION_URL", "http://orchestration:8001")
            requests.post(
                f"{orchestration_url}/delete-document",
                json={
                    "file_key": file_key,
                    "session_id": session_id
                },
                timeout=5
            )
        except Exception as e:
            print(f"Failed to call orchestration service for delete: {e}")
    
    return {"status": "success"}
