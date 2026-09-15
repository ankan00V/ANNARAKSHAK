"""Sarvam AI voice layer: Bulbul TTS (read advisories aloud), Saaras STT
(speak instead of type) and Sarvam-Translate (expert notes → farmer's
language). Server-side only — the API key never reaches the browser.

TTS audio is cached on disk by (text, language): advisories repeat, and every
repeat would otherwise cost a paid call and a network round trip in the field.

Pesticide-verdict strings are the one thing we never re-phrase or translate
at runtime; they are read out exactly as authored in labelcheck.VERDICTS.
"""

from __future__ import annotations

import base64
import hashlib

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.config import (
    DATA_DIR,
    SARVAM_API_KEY,
    SARVAM_LANG,
    SARVAM_SPEAKER,
    SARVAM_STT_MODEL,
    SARVAM_TRANSLATE_MODEL,
    SARVAM_TTS_MODEL,
)

TTS_CACHE = DATA_DIR / "tts"
MAX_TTS_CHARS = 2400  # REST limit is 2,500

router = APIRouter(prefix="/api/voice", tags=["voice"])


class VoiceUnavailable(RuntimeError):
    pass


def _client():
    if not SARVAM_API_KEY:
        raise VoiceUnavailable("SARVAM_API_KEY is not set")
    from sarvamai import SarvamAI  # noqa: PLC0415  optional dependency

    return SarvamAI(api_subscription_key=SARVAM_API_KEY, timeout=30)


def tts(text: str, lang: str, pace: float = 0.95) -> bytes:
    text = " ".join(text.split())[:MAX_TTS_CHARS]
    key = hashlib.sha256(f"{SARVAM_TTS_MODEL}|{SARVAM_SPEAKER}|{lang}|{pace}|{text}".encode()).hexdigest()
    path = TTS_CACHE / f"{key}.wav"
    if path.exists():
        return path.read_bytes()
    resp = _client().text_to_speech.convert(
        text=text, language_code=SARVAM_LANG[lang], model=SARVAM_TTS_MODEL,
        speaker=SARVAM_SPEAKER, pace=pace,
    )
    audio = base64.b64decode("".join(resp.audios))
    TTS_CACHE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return audio


def stt(audio: bytes, filename: str, lang: str | None) -> dict:
    kwargs = {"model": SARVAM_STT_MODEL, "mode": "transcribe"}
    if lang:
        kwargs["language_code"] = SARVAM_LANG[lang]
    resp = _client().speech_to_text.transcribe(file=(filename, audio), **kwargs)
    return {"transcript": resp.transcript, "language_code": getattr(resp, "language_code", None)}


def translate(text: str, source: str, target: str) -> str:
    if source == target or not text.strip():
        return text
    resp = _client().text.translate(
        input=text[:1900], source_language_code=SARVAM_LANG[source],
        target_language_code=SARVAM_LANG[target], model=SARVAM_TRANSLATE_MODEL, mode="formal",
    )
    return resp.translated_text


def status() -> dict:
    return {"configured": bool(SARVAM_API_KEY), "tts": SARVAM_TTS_MODEL, "stt": SARVAM_STT_MODEL,
            "translate": SARVAM_TRANSLATE_MODEL}


class TTSIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    lang: str = Field(pattern="^(en|hi|mr)$")


@router.get("/status")
def voice_status():
    return status()


@router.post("/tts")
def tts_endpoint(body: TTSIn):
    try:
        return Response(tts(body.text, body.lang), media_type="audio/wav")
    except VoiceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:  # upstream failure: say so, don't pretend
        raise HTTPException(502, f"speech service failed: {type(exc).__name__}") from exc


@router.post("/stt")
async def stt_endpoint(audio: UploadFile = File(...), lang: str | None = Form(None)):
    data = await audio.read()
    if not data:
        raise HTTPException(422, "empty audio")
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "audio too long — keep it under 30 seconds")
    try:
        return stt(data, audio.filename or "speech.webm", lang if lang in SARVAM_LANG else None)
    except VoiceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"speech service failed: {type(exc).__name__}") from exc


class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=1900)
    source: str = Field(pattern="^(en|hi|mr)$")
    target: str = Field(pattern="^(en|hi|mr)$")


@router.post("/translate")
def translate_endpoint(body: TranslateIn):
    try:
        return {"text": translate(body.text, body.source, body.target)}
    except VoiceUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"translation service failed: {type(exc).__name__}") from exc
