from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db_connection
from passlib.context import CryptContext
import jwt
import datetime
import os
import re

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    organization_name: str
    organization_slug: str = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

@router.post("/register")
def register(request: RegisterRequest):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute("SELECT * FROM users WHERE email = %s", (request.email,))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate slug if not provided
        org_slug = request.organization_slug if request.organization_slug else slugify(request.organization_name)
        
        # Check if slug is taken
        cur.execute("SELECT * FROM organizations WHERE slug = %s", (org_slug,))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Organization slug already taken. Please choose a different one.")
        
        # Extract domain from email
        domain = request.email.split('@')[1] if '@' in request.email else None
        
        # Create Organization
        cur.execute(
            "INSERT INTO organizations (name, slug, domain, plan_tier, max_users) VALUES (%s, %s, %s, 'free', 10) RETURNING id",
            (request.organization_name, org_slug, domain)
        )
        org_id = cur.fetchone()['id']
        
        # Hash password
        hashed_password = get_password_hash(request.password)
        
        # Create User as Admin (first user of organization)
        cur.execute(
            "INSERT INTO users (organization_id, email, password_hash, full_name, role) VALUES (%s, %s, %s, %s, 'admin') RETURNING *",
            (org_id, request.email, hashed_password, request.full_name)
        )
        user = cur.fetchone()
        
        conn.commit()
        
        # Generate Token
        token = create_access_token({
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "org_id": str(user['organization_id'])
        })
        
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
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/login")
def login(request: LoginRequest):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE email = %s", (request.email,))
        user = cur.fetchone()
        
        if not user or not user['password_hash'] or not verify_password(request.password, user['password_hash']):
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        token = create_access_token({
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role'],
            "org_id": str(user['organization_id']) if user['organization_id'] else None
        })
        
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
                "organization_id": str(user['organization_id']) if user['organization_id'] else None
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
