from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header, BackgroundTasks, Form
from typing import List, Optional
import os
import uuid
import boto3
from botocore.client import Config
from utils.db_connection import get_db_connection
import httpx
import logging

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
ORCHESTRATION_URL = os.getenv("ORCHESTRATION_URL", "http://orchestration:8001")

# Initialize MinIO Client
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}" if not MINIO_ENDPOINT.startswith("http") else MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1" # MinIO default
)

# Ensure bucket exists
try:
    s3_client.head_bucket(Bucket=MINIO_BUCKET)
except:
    try:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)
    except Exception as e:
        logger.error(f"Failed to create bucket: {e}")

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    # In a real app, decode JWT. Here we assume the token IS the user_id for simplicity 
    # or extract from a mock token if you prefer.
    # Based on conversations.py, it expects a JWT. Let's reuse the logic if possible, 
    # but for now I'll just extract the sub claim if it's a JWT, or use it as ID.
    token = authorization.replace("Bearer ", "")
    try:
        import jwt
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "supersecretkey"), algorithms=["HS256"])
        return payload['sub'], payload.get('org_id')
    except:
        # Fallback for dev/testing if not a valid JWT
        return token, "default_org"

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    authorization: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload a file to MinIO and trigger processing.
    """
    user_id, org_id = get_current_user_id(authorization)
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_key = f"{user_id}/{file_id}{file_ext}"
    
    try:
        # 1. Upload to MinIO
        s3_client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            file_key,
            ExtraArgs={"ContentType": file.content_type}
        )
        
        # 2. Save metadata to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (id, user_id, filename, file_key, content_type, size, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (file_id, user_id, file.filename, file_key, file.content_type, 0)) # Size 0 for now
        conn.commit()
        cursor.close()
        conn.close()
        
        # 3. Trigger Orchestration Processing
        background_tasks.add_task(
            trigger_processing,
            file_key,
            file.filename,
            file.content_type,
            user_id,
            org_id,
            session_id
        )
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "file_key": file_key,
            "message": "Upload successful, processing started"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def trigger_processing(file_key, filename, content_type, user_id, org_id, session_id):
    """Call orchestration service to process document."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{ORCHESTRATION_URL}/process-document",
                json={
                    "file_key": file_key,
                    "filename": filename,
                    "content_type": content_type,
                    "user_id": user_id,
                    "org_id": org_id,
                    "session_id": session_id
                }
            )
        except Exception as e:
            logger.error(f"Failed to trigger processing: {e}")
            # Update DB status to failed
            update_doc_status(file_key, "failed")

def update_doc_status(file_key, status):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE documents SET processing_status = %s WHERE file_key = %s", (status, file_key))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass

@router.delete("/{file_id}")
async def delete_file(file_id: str, authorization: str = Header(None)):
    """Delete file from MinIO, Vector DB, and PostgreSQL."""
    user_id, org_id = get_current_user_id(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get file info
        cursor.execute("SELECT file_key FROM documents WHERE id = %s AND user_id = %s", (file_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_key = row[0]
        
        # 1. Delete from MinIO
        try:
            s3_client.delete_object(Bucket=MINIO_BUCKET, Key=file_key)
        except Exception as e:
            logger.error(f"MinIO delete failed: {e}")
            
        # 2. Delete from Vector DB (via Orchestration)
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{ORCHESTRATION_URL}/delete-document",
                    json={
                        "file_key": file_key,
                        "user_id": user_id,
                        "org_id": org_id
                    }
                )
            except Exception as e:
                logger.error(f"Vector DB delete failed: {e}")
        
        # 3. Delete from DB
        cursor.execute("DELETE FROM documents WHERE id = %s", (file_id,))
        conn.commit()
        
        return {"status": "success", "message": "File deleted"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")
    finally:
        cursor.close()
        conn.close()

@router.get("")
async def list_files(authorization: str = Header(None)):
    """List user's files."""
    user_id, _ = get_current_user_id(authorization)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, filename, created_at, size, processing_status 
            FROM documents 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        files = []
        for row in cursor.fetchall():
            files.append({
                "id": row[0],
                "filename": row[1],
                "created_at": row[2].isoformat() if row[2] else None,
                "size": row[3],
                "status": row[4]
            })
            
        return {"status": "success", "files": files}
    finally:
        cursor.close()
        conn.close()
