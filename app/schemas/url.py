from pydantic import BaseModel
from datetime import datetime
from typing import List

class ShortenRequest(BaseModel):
    original_url: str

class ShortenResponse(BaseModel):
    short_url: str

class URLStatsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime

class AdminURLStats(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime

class AdminURLStatsResponse(BaseModel):
    urls: List[AdminURLStats]

