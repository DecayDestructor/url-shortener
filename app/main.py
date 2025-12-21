from fastapi import FastAPI
from app.routes.url import router as url_router

app = FastAPI(title="URL Shortener API")

app.include_router(url_router)
