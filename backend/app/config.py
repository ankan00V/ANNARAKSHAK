"""Every tunable constant lives here and nowhere else.

The decision thresholds are module constants, not environment settings, so
nobody can quietly loosen them before a demo. A threshold literal in another
file is a bug.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR.parent / ".env")  # secrets only (API keys); never thresholds

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
SARVAM_API_KEYS = list(dict.fromkeys(
    k.strip() for k in [*(os.environ.get("SARVAM_API_KEYS") or "").split(","), SARVAM_API_KEY or ""] if k.strip()))
"""Every Sarvam key we may use, rotated; one out of credits is benched and the next takes over."""
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")  # optional; Open-Meteo is the keyless fallback
SARVAM_TTS_MODEL = "bulbul:v3"
SARVAM_STT_MODEL = "saaras:v3"
SARVAM_TRANSLATE_MODEL = "sarvam-translate:v1"
SARVAM_SPEAKER = "shubh"  # bulbul:v3 default; v2 voices are rejected by v3
SARVAM_LANG = {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}
KB_DIR = BACKEND_DIR / "kb"
DATA_DIR = Path(os.environ.get("ANNRAKSHAK_DATA_DIR", BACKEND_DIR / ".data"))
UPLOAD_DIR = DATA_DIR / "uploads"
WEATHER_CACHE_DIR = DATA_DIR / "weather"
DB_URL = os.environ.get("ANNRAKSHAK_DB_URL", f"sqlite:///{DATA_DIR / 'annrakshak.db'}")

# --- Confidence gate -------------------------------------------------------
# Starting values, to be re-fit once the trained model's calibrated confidence
# distribution on a held-out field set is known.

GATE = 0.70
"""Top-1 at or above this, and clear of the runner-up by MARGIN → advise."""

FLOOR = 0.40
"""Top-1 below this → the model has nothing useful to say; escalate."""

MARGIN = 0.15
"""Minimum top-1 minus top-2 gap to call a prediction clear. Below → ask."""

MIN_VEGETATION_FRACTION = 0.08
"""Below this share of plant-coloured pixels the photo is not a crop photo and
is rejected before the classifier's softmax is trusted. A softmax with no
reject class always puts its mass somewhere, even on a photo of a shoe.
Measured on the 835 ICAR images: 10 (1.2%) fall below it, mostly insects shot
off the plant; flat wood, cardboard, soil, skin and grey all score 0."""

# --- Learning from field confirmations -------------------------------------

PRIOR_FULL_COUNT = 10
"""Net expert confirmations (confirmed minus corrected) that earn the full
PRIOR_MAX_BIAS nudge for a label in a district."""

PRIOR_MAX_BIAS = 0.05
"""Cap on the additive nudge a label's local confirmation history may apply to
a model confidence before the gate sees it."""

# The nudge must never move a prediction across a gate band on its own:
# smaller than MARGIN, it cannot turn an ambiguous pair into a clear one;
# smaller than GATE - FLOOR, it cannot carry an escalation to advice.
assert PRIOR_MAX_BIAS < MARGIN
assert PRIOR_MAX_BIAS < GATE - FLOOR

# --- Risk, spread and follow-up --------------------------------------------

SPREAD_RADIUS_KM = 5.0
"""Same-crop farms within this radius of a confirmed case get a spread alert."""

MAX_RISK_ALERTS_PER_FARM_PER_DAY = 3
"""Weather/phenology alerts per farm per day. Spread and trap alerts bypass
this: a confirmed neighbour or a trap over threshold is stronger evidence."""

WEATHER_PAST_DAYS = 7
WEATHER_FORECAST_DAYS = 7
WEATHER_TIMEOUT_S = 10
WEATHER_CACHE_MAX_AGE_H = 12
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

REDIS_URL = os.environ.get("REDIS_URL")
"""Upstash/any Redis: shared cache, rate limits, one-watcher lease, cross-instance events. Optional."""

AGRO_CACHE_MINUTES = 30
"""Hour-by-hour agro-weather is re-fetched at most this often per location."""

# --- Notifications: in-app (SSE), phone (Web Push) and email ---------------

WATCH_ENABLED = os.environ.get("ANNRAKSHAK_WATCH", "on") != "off"
"""The background watcher (weather rules, risk run, pushes, emails). Tests turn it off."""
WATCH_MINUTES = 30
QUIET_HOURS = (21, 6)
"""Local hours [start, end) when only warnings are delivered; the rest wait for morning."""
MAX_PUSH_PER_FARM_PER_DAY = 4
"""Non-warning phone notifications per farm per day. Warnings are never held back."""
MAX_ALERT_EMAILS_PER_FARM_PER_DAY = 3
DIGEST_HOUR = 6
"""Local hour after which the daily farm summary email goes out."""
PUBLIC_APP_URL = os.environ.get("ANNRAKSHAK_PUBLIC_URL", "http://localhost:5173").rstrip("/")

# Secrets and delivery settings (from .env; see .env.example)
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")  # PEM; generated into DATA_DIR if unset
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:alerts@annrakshak.in")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT") or 587)
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SECURITY = os.environ.get("SMTP_SECURITY", "starttls")  # starttls | ssl | none
EMAIL_FROM = os.environ.get("EMAIL_FROM") or (f"AnnRakshak <{SMTP_USER}>" if SMTP_USER else "AnnRakshak <alerts@localhost>")
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND") or ("smtp" if SMTP_HOST else "outbox")
"""'smtp' sends; 'outbox' writes .eml files to DATA_DIR/outbox (dev and tests)."""

FOLLOWUP_DUE_DAYS = 4
CASE_ETA_MINUTES_PER_POSITION = 20
