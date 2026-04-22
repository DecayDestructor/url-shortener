from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from fastapi import BackgroundTasks
from datetime import datetime, timezone, timedelta
from collections import Counter
import re

from app.schemas.url import (
    ShortenRequest, ShortenResponse, URLStatsResponse,
    URLAnalyticsResponse, AdminURLStatsResponse, ClickEventOut,
)
from app.core.config import BASE_URL
from app.db.database import get_session
from app.db.models import URL, User, ClickEvent
from app.core.redis import redis_client
from app.core.rate_limit import rate_limiter
from app.tasks.click_sync import sync_clicks_to_db
from app.core.shortcode import base62_encode
from app.core.auth import get_current_user, get_current_admin, bearer_scheme
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional

router = APIRouter()

QR_BASE = "https://api.qrserver.com/v1/create-qr-code"

ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,30}$")

RESERVED = {
    "shorten", "stats", "urls", "admin", "auth",
    "health", "docs", "redoc", "openapi"
}


# helpers 

def _qr_url(short_url: str) -> str:
    return (
        f"{QR_BASE}?size=300x300&data={short_url}"
        "&bgcolor=0a0a0a&color=FFE500&format=svg"
    )


def _detect_device(ua: str | None) -> str:
    if not ua:
        return "unknown"
    ua_lower = ua.lower()
    bots = ["bot", "crawl", "spider", "slurp", "facebookexternalhit", "python-requests", "curl"]
    if any(b in ua_lower for b in bots):
        return "bot"
    if any(m in ua_lower for m in ["mobile", "android", "iphone", "ipad", "ipod"]):
        return "mobile"
    return "desktop"


def generate_short_code() -> str:
    counter = redis_client.incr("global:url:id")
    return base62_encode(counter)


def _is_expired(url: URL) -> bool:
    if url.expires_at is None:
        return False
    return datetime.now(timezone.utc) > url.expires_at.replace(tzinfo=timezone.utc)


#POST /shorten 

@router.post("/shorten", response_model=ShortenResponse, dependencies=[Depends(rate_limiter)])
def shorten_url(
    request: ShortenRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    alias = request.custom_alias.strip() if request.custom_alias else None

    # custom alias path 
    if alias:
        if not ALIAS_RE.match(alias):
            raise HTTPException(
                status_code=400,
                detail="Alias must be 3–30 chars: letters, digits, _ or -",
            )
        if alias.lower() in RESERVED:
            raise HTTPException(status_code=400, detail="That alias is reserved.")

        existing = session.exec(select(URL).where(URL.short_code == alias)).first()
        if existing:
            raise HTTPException(status_code=409, detail="Alias already taken.")

        short_code = alias
        is_custom = True

    #  auto-generated path
    else:
        # Dedup for same owner + same URL (no expiry requested)
        if not request.expires_in_hours:
            existing = session.exec(
                select(URL).where(
                    URL.original_url == request.original_url,
                    URL.owner_id == getattr(current_user, "id", None),
                    URL.is_custom == False,
                )
            ).first()
            if existing and not _is_expired(existing):
                full = f"{BASE_URL}/{existing.short_code}"
                return ShortenResponse(
                    short_url=full,
                    short_code=existing.short_code,
                    qr_url=_qr_url(full),
                    is_custom=False,
                    expires_at=existing.expires_at,
                )

        short_code = generate_short_code()
        is_custom = False

    #  expiry 
    expires_at = None
    if request.expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=request.expires_in_hours)

    url = URL(
        short_code=short_code,
        original_url=request.original_url,
        owner_id=getattr(current_user, "id", None),
        is_custom=is_custom,
        expires_at=expires_at,
    )
    session.add(url)
    session.commit()
    session.refresh(url)

    # Cache immediately
    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds()) if expires_at else 3600
    redis_client.setex(f"url:{short_code}", ttl, url.original_url)

    full = f"{BASE_URL}/{short_code}"
    return ShortenResponse(
        short_url=full,
        short_code=short_code,
        qr_url=_qr_url(full),
        is_custom=is_custom,
        expires_at=expires_at,
    )


#GET /{short_code}  (redirect) 

@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    req: Request,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    # Skip internal paths
    if short_code in RESERVED or short_code.startswith("_"):
        raise HTTPException(status_code=404, detail="Not found")

    cache_key = f"url:{short_code}"
    click_key = f"clicks:{short_code}"

    referrer = req.headers.get("referer") or req.headers.get("referrer") or None
    ua = req.headers.get("user-agent")
    device = _detect_device(ua)

    cached_url = redis_client.get(cache_key)

    if cached_url:
        count = redis_client.incr(click_key)
        if count == 1:
            redis_client.expire(click_key, 86400)
        redis_client.zincrby("trending_urls", 1, short_code)
        if redis_client.ttl("trending_urls") == -1:
            redis_client.expire("trending_urls", 86400)
        if count % 50 == 0:
            background_tasks.add_task(sync_clicks_to_db, short_code)
        background_tasks.add_task(_record_click, short_code, referrer, ua, device)
        return RedirectResponse(url=cached_url, status_code=302)

    url = session.exec(select(URL).where(URL.short_code == short_code)).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    if _is_expired(url):
        raise HTTPException(status_code=410, detail="This link has expired")

    ttl = 3600
    if url.expires_at:
        ttl = max(1, int((url.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds()))

    redis_client.setex(cache_key, ttl, url.original_url)
    redis_client.incr(click_key)
    redis_client.expire(click_key, 86400)
    redis_client.zincrby("trending_urls", 1, short_code)
    redis_client.expire("trending_urls", 86400)

    background_tasks.add_task(sync_clicks_to_db, short_code)
    background_tasks.add_task(_record_click, short_code, referrer, ua, device)

    return RedirectResponse(url=url.original_url, status_code=302)


def _record_click(short_code: str, referrer, ua, device):
    """Background: persist one ClickEvent row for analytics."""
    from app.db.database import engine
    from sqlmodel import Session as _Session
    with _Session(engine) as s:
        ev = ClickEvent(
            short_code=short_code,
            referrer=referrer,
            user_agent=ua,
            device_type=device,
        )
        s.add(ev)
        s.commit()


# GET /stats/{short_code} 

@router.get("/stats/{short_code}", response_model=URLStatsResponse)
def get_url_stats(short_code: str, session: Session = Depends(get_session)):
    url = session.exec(select(URL).where(URL.short_code == short_code)).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    redis_clicks = redis_client.get(f"clicks:{short_code}")
    redis_clicks = int(redis_clicks) if redis_clicks else 0

    return URLStatsResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        clicks=url.clicks + redis_clicks,
        created_at=url.created_at,
        expires_at=url.expires_at,
        is_custom=url.is_custom,
    )


# GET /analytics/{short_code} 

@router.get("/analytics/{short_code}", response_model=URLAnalyticsResponse)
def get_url_analytics(
    short_code: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    url = session.exec(select(URL).where(URL.short_code == short_code)).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Only owner or admin can view analytics
    if url.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    redis_clicks = redis_client.get(f"clicks:{short_code}")
    redis_clicks = int(redis_clicks) if redis_clicks else 0
    total = url.clicks + redis_clicks

    events = session.exec(
        select(ClickEvent)
        .where(ClickEvent.short_code == short_code)
        .order_by(ClickEvent.clicked_at.desc())
        .limit(200)
    ).all()

    device_breakdown = dict(Counter(e.device_type for e in events if e.device_type))
    referrer_counts = Counter(e.referrer or "Direct" for e in events)
    top_referrers = [
        {"referrer": r, "count": c}
        for r, c in referrer_counts.most_common(10)
    ]

    recent = [
        ClickEventOut(clicked_at=e.clicked_at, referrer=e.referrer, device_type=e.device_type)
        for e in events[:50]
    ]

    return URLAnalyticsResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        total_clicks=total,
        created_at=url.created_at,
        expires_at=url.expires_at,
        is_custom=url.is_custom,
        recent_clicks=recent,
        device_breakdown=device_breakdown,
        top_referrers=top_referrers,
    )


# GET /urls/me 

@router.get("/urls/me", response_model=AdminURLStatsResponse)
def get_my_urls(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    urls = session.exec(
        select(URL).where(URL.owner_id == current_user.id).order_by(URL.created_at.desc())
    ).all()
    result = []
    for url in urls:
        redis_clicks = redis_client.get(f"clicks:{url.short_code}")
        redis_clicks = int(redis_clicks) if redis_clicks else 0
        result.append({
            "short_code": url.short_code,
            "original_url": url.original_url,
            "clicks": url.clicks + redis_clicks,
            "created_at": url.created_at,
            "expires_at": url.expires_at,
            "is_custom": url.is_custom,
            "owner_id": url.owner_id,
        })
    return {"urls": result}


# DELETE /urls/{short_code} 

@router.delete("/urls/{short_code}")
def delete_url(
    short_code: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    url = session.exec(select(URL).where(URL.short_code == short_code)).first()
    if not url:
        raise HTTPException(status_code=404, detail="Not found")
    if url.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised")

    # Clean Redis caches
    redis_client.delete(f"url:{short_code}")
    redis_client.delete(f"clicks:{short_code}")
    redis_client.zrem("trending_urls", short_code)

    session.delete(url)
    session.commit()
    return {"detail": "Deleted"}


#GET /admin/urls 

@router.get("/admin/urls", response_model=AdminURLStatsResponse)
def get_all_urls_stats(
    session: Session = Depends(get_session),
    top: int = None,
    _admin: User = Depends(get_current_admin),
):
    urls = session.exec(select(URL).order_by(URL.created_at.desc())).all()
    result = []
    for url in urls:
        redis_clicks = redis_client.get(f"clicks:{url.short_code}")
        redis_clicks = int(redis_clicks) if redis_clicks else 0
        result.append({
            "short_code": url.short_code,
            "original_url": url.original_url,
            "clicks": url.clicks + redis_clicks,
            "created_at": url.created_at,
            "expires_at": url.expires_at,
            "is_custom": url.is_custom,
            "owner_id": url.owner_id,
        })
    if top:
        result.sort(key=lambda x: x["clicks"], reverse=True)
        result = result[:top]
    return {"urls": result}


# GET /admin/trending 

@router.get("/admin/trending", response_model=AdminURLStatsResponse)
def get_trending_urls(
    session: Session = Depends(get_session),
    top: int = 5,
    _admin: User = Depends(get_current_admin),
):
    trending = redis_client.zrevrange("trending_urls", 0, top - 1, withscores=True)
    result = []
    for short_code, score in trending:
        url = session.exec(select(URL).where(URL.short_code == short_code)).first()
        if url:
            result.append({
                "short_code": url.short_code,
                "original_url": url.original_url,
                "clicks": int(score),
                "created_at": url.created_at,
                "expires_at": url.expires_at,
                "is_custom": url.is_custom,
                "owner_id": url.owner_id,
            })
    return {"urls": result}


# GET /trending/public 
# Open endpoint – used on the home page live leaderboard

@router.get("/trending/public")
def get_trending_public(session: Session = Depends(get_session), top: int = 5):
    trending = redis_client.zrevrange("trending_urls", 0, top - 1, withscores=True)
    result = []
    for short_code, score in trending:
        url = session.exec(select(URL).where(URL.short_code == short_code)).first()
        if url:
            result.append({
                "short_code": short_code,
                "clicks": int(score),
                "short_url": f"{BASE_URL}/{short_code}",
            })
    return {"trending": result}
