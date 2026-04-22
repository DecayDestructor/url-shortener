from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import User
from app.schemas.auth import UserRegister, UserLogin, AdminLogin, TokenResponse, UserPublic
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
)

router = APIRouter(prefix="/auth", tags=["auth"])


#Register 
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, session: Session = Depends(get_session)):
    # Check duplicates
    existing_email = session.exec(select(User).where(User.email == body.email)).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = session.exec(select(User).where(User.username == body.username)).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": str(user.id), "is_admin": False})
    return TokenResponse(access_token=token, is_admin=False, username=user.username)


#  Login 
@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return TokenResponse(access_token=token, is_admin=user.is_admin, username=user.username)


# Admin Login 
@router.post("/admin/login", response_model=TokenResponse)
def admin_login(body: AdminLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "is_admin": True})
    return TokenResponse(access_token=token, is_admin=True, username=user.username)


# Me 
@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# Seed admin (one-time utility) 
@router.post("/admin/seed", include_in_schema=False)
def seed_admin(session: Session = Depends(get_session)):
    """
    Creates the default admin account if it doesn't exist.
    Hit once during setup: POST /auth/admin/seed
    Credentials: admin@snip.ly / admin123
    """
    existing = session.exec(select(User).where(User.email == "admin@snip.ly")).first()
    if existing:
        return {"detail": "Admin already exists"}
    admin = User(
        email="admin@snip.ly",
        username="admin",
        hashed_password=hash_password("admin123"),
        is_admin=True,
    )
    session.add(admin)
    session.commit()
    return {"detail": "Admin created", "email": "admin@snip.ly", "password": "admin123"}
