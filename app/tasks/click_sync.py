from sqlmodel import Session, select
from app.db.database import engine
from app.db.models import URL
from app.core.redis import redis_client


def sync_clicks_to_db(short_code: str):
    redis_key = f"clicks:{short_code}"

    clicks = redis_client.getdel(redis_key)
    clicks = int(clicks) if clicks else 0

    if clicks == 0:
        return

    with Session(engine) as session:
        url = session.exec(
            select(URL).where(URL.short_code == short_code)
        ).first()

        if url:
            url.clicks += clicks
            session.commit()

    
