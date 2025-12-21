from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.url import router as url_router
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="URL Shortener API",
    lifespan=lifespan

)


app.include_router(url_router)
