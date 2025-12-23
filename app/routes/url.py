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
from app.schemas.url import AdminURLStatsResponse
from app.core.shortcode import base62_encode

router = APIRouter()


def generate_short_code() -> str:
    """
    Redis-backed global counter → Base62 encoded short code
    """
    counter = redis_client.incr("global:url:id")
    return base62_encode(counter)



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
    redis_clicks = int(redis_clicks) if redis_clicks else 0


    return URLStatsResponse(
    short_code=url.short_code,
    original_url=url.original_url,
    clicks=url.clicks + redis_clicks,
    created_at=url.created_at
)
    
    

@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    print("REDIRECT HIT:", short_code)
    cache_key = f"url:{short_code}"
    click_key = f"clicks:{short_code}"

    cached_url = redis_client.get(cache_key)

    if cached_url:
        # Increment click counter
        count = redis_client.incr(click_key)
        if count == 1:
            redis_client.expire(click_key, 86400)

        # Trending 
        redis_client.zincrby("trending_urls", 1, short_code)

        if redis_client.ttl("trending_urls") == -1:
            redis_client.expire("trending_urls", 86400)
        if count % 50 == 0:
            background_tasks.add_task(sync_clicks_to_db, short_code)

        return RedirectResponse(url=cached_url, status_code=302)

    # Cache miss → DB
    url = session.exec(
        select(URL).where(URL.short_code == short_code)
    ).first()

    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Cache URL
    redis_client.setex(cache_key, 3600, url.original_url)

    # Init click count
    redis_client.incr(click_key)
    redis_client.expire(click_key, 86400)

    # Trending
    redis_client.zincrby("trending_urls", 1, short_code)
    redis_client.expire("trending_urls", 86400)

    background_tasks.add_task(sync_clicks_to_db, short_code)

    return RedirectResponse(url=url.original_url, status_code=302)


@router.get("/admin/urls", response_model=AdminURLStatsResponse)
def get_all_urls_stats(session: Session = Depends(get_session), top: int = None):
    urls = session.exec(select(URL)).all()
    result = []

    for url in urls:
        # Get Redis pending clicks
        redis_clicks = redis_client.get(f"clicks:{url.short_code}")
        redis_clicks = int(redis_clicks) if redis_clicks else 0

        total_clicks = url.clicks + redis_clicks

        result.append({
            "short_code": url.short_code,
            "original_url": url.original_url,
            "clicks": total_clicks,
            "created_at": url.created_at
        })

    # Sort by clicks if top N requested
    if top:
        result.sort(key=lambda x: x["clicks"], reverse=True)
        result = result[:top]

    return {"urls": result}



@router.get("/admin/trending", response_model=AdminURLStatsResponse)
def get_trending_urls(session: Session = Depends(get_session), top: int = 5):
    trending = redis_client.zrevrange(
        "trending_urls",
        0,
        top - 1,
        withscores=True
    )

    result = []
    for short_code, score in trending:
        url = session.exec(
            select(URL).where(URL.short_code == short_code)
        ).first()

        if url:
            result.append({
                "short_code": url.short_code,
                "original_url": url.original_url,
                "clicks": int(score),
                "created_at": url.created_at
            })

    return {"urls": result}
