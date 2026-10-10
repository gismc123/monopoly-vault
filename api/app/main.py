import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import SessionLocal
from app.routers import auth, codes, collection, legal, ocr, season, session, vault
from app.services import photos
from app.services.codes import AppError

log = logging.getLogger("uvicorn.error")
SWEEP_EVERY_SECONDS = 3600


def sweep_photos_once() -> None:
    try:
        with SessionLocal() as db:
            removed = photos.sweep_unclaimed(db, get_settings().unclaimed_photo_hours)
        if removed:
            log.info("Removed %d unsaved photo(s)", removed)
    except Exception:
        log.exception("Photo cleanup failed")


async def sweep_photos_forever() -> None:
    while True:
        await asyncio.to_thread(sweep_photos_once)
        await asyncio.sleep(SWEEP_EVERY_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(sweep_photos_forever()) if get_settings().photo_sweep_enabled else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Monopoly Vault API", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)

for module in (auth, season, session, codes, collection, vault, ocr, legal):
    app.include_router(module.router)


@app.exception_handler(AppError)
def app_error(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/health")
def health():
    return {"status": "ok"}
