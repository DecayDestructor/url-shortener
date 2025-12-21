from fastapi import APIRouter, HTTPException,Depends
from fastapi.responses import RedirectResponse
import string, random
from sqlmodel import Session,select

from app.schemas.url import ShortenRequest, ShortenResponse
from app.core.config import BASE_URL
from app.db.database import get_session
from app.db.models import URL

router = APIRouter()


def generate_short_code(length: int = 6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@router.post("/shorten", response_model=ShortenResponse)
def shorten_url(
    request: ShortenRequest,
    session: Session = Depends(get_session)
):
    
   #avoid collision
    existing_url = session.exec(
       select(URL).where(URL.original_url == request.original_url)
    ).first()

    if existing_url:
         return {
            "short_url": f"{BASE_URL}/{existing_url.short_code}"
        }

    short_code = generate_short_code()

    existing = session.exec(
        select(URL).where(URL.short_code == short_code)
    ).first()

    while existing:
        short_code = generate_short_code()
        existing = session.exec(
            select(URL).where(URL.short_code == short_code)
        ).first()

    url = URL(
        short_code=short_code,
        original_url=request.original_url
    )

    session.add(url)
    session.commit()
    session.refresh(url)

    return {
        "short_url": f"{BASE_URL}/{short_code}"
    }


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    session: Session = Depends(get_session)
):
    url = session.exec(
        select(URL).where(URL.short_code== short_code)
    ).first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    url.clicks = url.clicks+1
    session.add(url)
    session.commit()

    return RedirectResponse(
        url=url.original_url,
        status_code=302
    )
