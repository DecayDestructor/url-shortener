from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import os

from app.routes.url import router as url_router
from app.routes.auth import router as auth_router
from app.db.database import create_db_and_tables, engine
from app.tasks.click_sync import sync_all_clicks_to_db
from sqlmodel import Session, select
from sqlalchemy import func
from app.db.models import URL
from app.core.redis import redis_client

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    create_db_and_tables()

    # Sync Redis counter with existing Postgres DB to prevent duplicate short_codes
    with Session(engine) as session:
        max_id = session.exec(select(func.max(URL.id))).first()
        if max_id:
            current = redis_client.get("global:url:id")
            if not current or int(current) < max_id:
                redis_client.set("global:url:id", max_id)

    # Periodic Redis → Postgres sync every 5 minutes
    scheduler.add_job(sync_all_clicks_to_db, "interval", minutes=5, id="click_sync")
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="snip.ly URL Shortener API",
    description="Base62 URL shortening with Redis caching, analytics, and JWT auth.",
    version="2.0.0",
    lifespan=lifespan,
)

# Build allowed origins: local dev + Docker (port 80) + any BASE_URL set via env
_base_url = os.getenv("BASE_URL", "")
_allowed_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # Alt dev port
    "http://localhost",        # Docker / Nginx on port 80
    "http://localhost:80",
]
if _base_url and _base_url not in _allowed_origins:
    _allowed_origins.append(_base_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(url_router)
