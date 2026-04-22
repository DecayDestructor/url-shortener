from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional


class ShortenRequest(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None   # user-defined short code
    expires_in_hours: Optional[int] = None  # e.g. 24 → expires after 24 h

class ShortenResponse(BaseModel):
    short_url: str
    short_code: str
    qr_url: str
    is_custom: bool
    expires_at: Optional[datetime] = None

class URLStatsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_custom: bool = False

class ClickEventOut(BaseModel):
    clicked_at: datetime
    referrer: Optional[str]
    device_type: Optional[str]

class URLAnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    created_at: datetime
    expires_at: Optional[datetime]
    is_custom: bool
    recent_clicks: List[ClickEventOut]
    device_breakdown: dict  # e.g. {"mobile": 10, "desktop": 5, "bot": 1}
    top_referrers: List[dict]  # [{"referrer": "...", "count": n}]

class AdminURLStats(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_custom: bool = False
    owner_id: Optional[int] = None

class AdminURLStatsResponse(BaseModel):
    urls: List[AdminURLStats]
