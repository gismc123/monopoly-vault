from fastapi import FastAPI

app = FastAPI(title="Monopoly Vault API", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.get("/api/health")
def health():
    return {"status": "ok"}
