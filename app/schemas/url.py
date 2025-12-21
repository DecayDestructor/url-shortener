from pydantic import BaseModel

class ShortenRequest(BaseModel):
    original_url: str

class ShortenResponse(BaseModel):
    short_url: str