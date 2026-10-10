from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import auth, codes, collection, ocr, season, session, vault
from app.services.codes import AppError

app = FastAPI(title="Monopoly Vault API", docs_url="/api/docs", openapi_url="/api/openapi.json")

for module in (auth, season, session, codes, collection, vault, ocr):
    app.include_router(module.router)


@app.exception_handler(AppError)
def app_error(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/health")
def health():
    return {"status": "ok"}
