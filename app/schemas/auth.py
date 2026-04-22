from pydantic import BaseModel
from typing import Optional


class UserRegister(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class AdminLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool = False
    username: str


class UserPublic(BaseModel):
    id: int
    email: str
    username: str
    is_admin: bool
    is_active: bool
