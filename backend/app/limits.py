"""Rate limits (fixed windows, shared across instances through Redis when it is
up). They protect what costs money or reaches people: paid Sarvam calls, emails
and phone notifications — not ordinary reads."""

from __future__ import annotations

from fastapi import HTTPException, Request

from app import cache


def limit(key: str, max_hits: int, window_s: int) -> None:
    if cache.hit(key, window_s) > max_hits:
        raise HTTPException(429, "too many requests — please wait a moment and try again",
                            headers={"Retry-After": str(window_s)})


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return (fwd.split(",")[0].strip() if fwd else None) or (request.client.host if request.client else "unknown")
