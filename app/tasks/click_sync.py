from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import URL
from app.core.redis import redis_client


def sync_clicks_to_db(short_code: str):
    """Atomically move Redis click count to PostgreSQL."""
    redis_key = f"clicks:{short_code}"
    clicks = redis_client.getdel(redis_key)
    clicks = int(clicks) if clicks else 0
    if clicks == 0:
        return

    with Session(engine) as session:
        url = session.exec(select(URL).where(URL.short_code == short_code)).first()
        if url:
            url.clicks += clicks
            session.commit()


def sync_all_clicks_to_db():
    """
    Full sweep: called by the APScheduler periodic job.
    Finds every clicks:* key in Redis and flushes them to Postgres.
    """
    keys = redis_client.keys("clicks:*")
    if not keys:
        return

    with Session(engine) as session:
        for key in keys:
            short_code = key.split(":", 1)[1]
            clicks_raw = redis_client.getdel(key)
            if not clicks_raw:
                continue
            clicks = int(clicks_raw)
            if clicks == 0:
                continue
            url = session.exec(select(URL).where(URL.short_code == short_code)).first()
            if url:
                url.clicks += clicks
        session.commit()
