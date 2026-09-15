from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BACKEND_DIR, UPLOAD_DIR
from app.db import init_db
from app.engine import vision
from app.kb import get_kb
from app import voice
from app.routers import expert, farmer, officials


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_kb()  # refuse to start on a broken knowledge base
    init_db()
    yield


app = FastAPI(title="AnnRakshak API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=UPLOAD_DIR), name="media")
_SAMPLES = BACKEND_DIR.parent / "data" / "processed" / "icar_640"
if _SAMPLES.exists():  # held-out demo images; absent on machines without the dataset
    app.mount("/samples", StaticFiles(directory=_SAMPLES), name="samples")
_EXTRA = BACKEND_DIR.parent / "data" / "processed" / "extra_640"
if _EXTRA.exists():  # held-out photos from the extra sources (blast, rust, field FAW)
    app.mount("/samples-extra", StaticFiles(directory=_EXTRA), name="samples-extra")

app.include_router(farmer.router)
app.include_router(expert.router)
app.include_router(officials.router)
app.include_router(voice.router)


@app.get("/health")
def health():
    kb = get_kb()
    return {
        "status": "ok",
        "service": "annrakshak-api",
        "kb": {"targets": len(kb.targets), "cues": len(kb.cues), "rules": len(kb.rules)},
        "model": vision.model_status(),
        "voice": voice.status(),
    }
