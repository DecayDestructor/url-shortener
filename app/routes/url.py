from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import string, random

from app.schemas.url import ShortenRequest, ShortenResponse
from app.core.config import BASE_URL

router = APIRouter()

url_store = {}

def generate_short_code(length: int = 6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@router.post("/shorten", response_model=ShortenResponse)
def shorten_url(request: ShortenRequest):
    short_code = generate_short_code()

    while short_code in url_store:
        short_code = generate_short_code()

    url_store[short_code] = request.original_url

    return {
        "short_url": f"{BASE_URL}/{short_code}"
    }


@router.get("/{short_code}")
def redirect_to_original(short_code: str):
    original_url = url_store.get(short_code)

    if not original_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return RedirectResponse(url=original_url, status_code=302)
