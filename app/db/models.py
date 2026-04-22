from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class URL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    short_code: str = Field(index=True, unique=True)
    original_url: str
    clicks: int = Field(default=0)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    is_custom: bool = Field(default=False)                         # True if user-defined alias
    expires_at: Optional[datetime] = Field(default=None)          # NULL = never expires
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ClickEvent(SQLModel, table=True):
    """Each row = one redirect event for device/referrer analytics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    short_code: str = Field(index=True, foreign_key="url.short_code")
    clicked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    referrer: Optional[str] = Field(default=None)      # HTTP Referer header
    user_agent: Optional[str] = Field(default=None)    # raw UA string
    device_type: Optional[str] = Field(default=None)  # "mobile" | "desktop" | "bot"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )