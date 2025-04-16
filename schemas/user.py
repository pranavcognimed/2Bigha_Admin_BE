from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserProfileOut(BaseModel):
    user_id: int
    email_verified: bool

    class Config:
        orm_mode = True


class RoleOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class UserOut(UserBase):
    user_id: int
    profile: Optional[UserProfileOut]

    class Config:
        orm_mode = True
