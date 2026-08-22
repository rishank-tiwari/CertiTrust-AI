from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: Literal['institution', 'student', 'employer']
    organization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    organization: Optional[str] = None
    created_at: datetime

class UserInDB(UserResponse):
    password_hash: str

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    role: str
