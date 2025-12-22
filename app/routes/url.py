from fastapi import APIRouter, HTTPException,Depends
from fastapi.responses import RedirectResponse
import string, random
from sqlmodel import Session,select
from fastapi import BackgroundTasks

from app.schemas.url import ShortenRequest, ShortenResponse
from app.core.config import BASE_URL
from app.db.database import get_session
from app.db.models import URL
from app.schemas.url import URLStatsResponse
from app.core.redis import redis_client
from app.core.rate_limit import rate_limiter
from app.tasks.click_sync import sync_clicks_to_db

router = APIRouter()


def generate_short_code(length: int = 6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@router.post(
        "/shorten", 
        response_model=ShortenResponse,
        dependencies=[Depends(rate_limiter)]
)
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



@router.get("/stats/{short_code}", response_model = URLStatsResponse)
def get_url_stats(
    short_code: str,
    session: Session = Depends(get_session)
):
    url = session.exec(
        select(URL).where(URL.short_code == short_code)).first()

    if not url:
        raise HTTPException(status_code = 404, detail="Short URL not found")
    
    redis_clicks = redis_client.get(f"clicks:{short_code}")
    total_clicks = int(redis_clicks) if redis_clicks else 0

    #Merge Redis clicks into DB
    if redis_clicks > 0:
        url.clicks += redis_clicks
        session.add(url)
        session.commit()

        #Clear Redis counter
        redis_client.delete(f"clicks:{short_code}")

    return URLStatsResponse(
        short_code = url.short_code,
        original_url= url.original_url,
        clicks = url.clicks,
        created_at= url.created_at
    )
    
    


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    # Check Redis cache for URL
    cached_url = redis_client.get(f"url:{short_code}")

    if cached_url:
        # Increment clicks in Redis (FAST)
        redis_client.incr(f"clicks:{short_code}")

        # Increment clicks in DB (SLOW)
        background_tasks.add_task(sync_clicks_to_db, short_code)

        return RedirectResponse(url=cached_url, status_code=302)

    # Cache miss → check DB
    url = session.exec(
        select(URL).where(URL.short_code == short_code)
    ).first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Save URL in Redis
    redis_client.setex(
        f"url:{short_code}",
        3600,  # 1 hour
        url.original_url
    )

    # Initialize click counter
    redis_client.incr(f"clicks:{short_code}")
    background_tasks.add_task(sync_clicks_to_db, short_code)

    return RedirectResponse(
        url=url.original_url,
        status_code=302
    )


