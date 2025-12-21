from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime,timezone

class URL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    short_code: str = Field(index=True, unique=True)
    original_url: str
    clicks: int = Field(default = 0)
    created_at: datetime= Field(
        default_factory= lambda: datetime.now(timezone.utc)
    )