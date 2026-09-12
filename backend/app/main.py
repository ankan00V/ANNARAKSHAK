from fastapi import FastAPI

app = FastAPI(title="AnnRakshak API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "annrakshak-api"}
