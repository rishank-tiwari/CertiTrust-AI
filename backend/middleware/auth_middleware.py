from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_database
from services.auth_service import decode_access_token
from bson import ObjectId

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
        
    db = get_database()
    query_id = user_id
    try:
        query_id = ObjectId(user_id)
    except Exception:
        pass
    
    user = None
    try:
        user = await db.users.find_one({"_id": query_id})
        if not user and payload.get("email"):
            user = await db.users.find_one({"email": payload.get("email")})
    except Exception:
        pass

    if not user:
        email = payload.get("email", "user@certitrust.ai")
        user = {
            "_id": str(user_id),
            "id": str(user_id),
            "email": email,
            "full_name": payload.get("full_name", email.split("@")[0] if "@" in email else "CertiTrust User"),
            "role": payload.get("role", "institution"),
            "organization": payload.get("organization")
        }
        
    return user

security_optional = HTTPBearer(auto_error=False)

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security_optional)):
    if credentials:
        try:
            return await get_current_user(credentials)
        except Exception:
            pass
    return {
        "_id": "guest_employer",
        "id": "guest_employer",
        "email": "guest@certitrust.ai",
        "full_name": "Guest Employer",
        "role": "employer",
        "organization": "Public Auditor"
    }

def require_role(*roles):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
