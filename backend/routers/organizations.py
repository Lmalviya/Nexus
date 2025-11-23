from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection
import jwt
import datetime
import os

router = APIRouter(prefix="/organizations", tags=["organizations"])

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

class CreateOrgRequest(BaseModel):
    name: str
    slug: str
    domain: str
    user_email: str
    user_name: str
    user_picture: str

@router.post("/")
def create_organization(request: CreateOrgRequest):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create Organization
        cur.execute(
            "INSERT INTO organizations (name, slug, domain, plan_tier, max_users) VALUES (%s, %s, %s, 'free', 10) RETURNING id",
            (request.name, request.slug, request.domain)
        )
        org_id = cur.fetchone()['id']
        
        # Create Admin User
        cur.execute(
            "INSERT INTO users (organization_id, email, full_name, avatar_url, role) VALUES (%s, %s, %s, %s, 'admin') RETURNING *",
            (org_id, request.user_email, request.user_name, request.user_picture)
        )
        user = cur.fetchone()
        
        conn.commit()
        
        # Generate JWT
        payload = {
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "org_id": str(user['organization_id']),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "token": token,
            "user": {
                "id": str(user['id']),
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role'],
                "organization_id": str(user['organization_id'])
            }
        }
        
    except Exception as e:
        print(f"Error: {e}")
        # Rollback? Psycopg2 usually handles transaction blocks, but simple here.
        raise HTTPException(status_code=500, detail=str(e))
