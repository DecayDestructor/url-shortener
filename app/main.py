from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from app.routes.url import router as url_router
from app.routes.auth import router as auth_router
from app.db.database import create_db_and_tables
from app.tasks.click_sync import sync_all_clicks_to_db

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    create_db_and_tables()

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(url_router)


@app.get("/health")
def health():
    return {"status": "ok"}
