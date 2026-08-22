from fastapi import APIRouter, Depends, HTTPException, status
from models.user import UserCreate, UserLogin, UserResponse, Token
from database import get_database
from services.auth_service import hash_password, verify_password, create_access_token
from middleware.auth_middleware import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate):
    """Register a new user account."""
    db = get_database()
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_dict = user_data.model_dump()
    user_dict["password_hash"] = hash_password(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now(timezone.utc)

    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)

    return UserResponse(**user_dict)


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login and receive a JWT access token."""
    db = get_database()
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(data={
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    })
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    current_user["id"] = str(current_user["_id"])
    return UserResponse(**current_user)
