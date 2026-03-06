from fastapi import HTTPException, Header
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

def get_current_user(authorization: str = Header(None)):
    """
    Dependency to extract and validate JWT token from Authorization header.
    Returns the decoded token payload containing user information.
    
    Raises:
        HTTPException: If token is missing, expired, or invalid
    """
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
