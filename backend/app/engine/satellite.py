"""Crop health from space: NDVI from Sentinel-2 and Landsat 8, and satellite
soil moisture/temperature, per field, via AgroMonitoring (OpenWeather's agro API).

Each farm gets a field polygon (a square of its area around the farm point,
at least MIN_HA — the provider's minimum). From the NDVI history only clear
scenes count (cloud <= MAX_CLOUD, coverage >= MIN_COVERAGE): a cloudy scene's
NDVI is the cloud's, not the crop's.

The early-warning signal is a DROP in the field's mean NDVI between two clear
scenes close in time, while the crop should be green or greening — pests,
disease, water stress and lodging all show up this way before a farmer walks
past the spot. Early growth and ripening are excluded: NDVI is naturally low
or falling then.

The provider's image URLs carry our API key, so only numbers ever leave the
server. Cached (Redis/disk) because scenes arrive every few days, not minutes.
"""

from __future__ import annotations

import json
import math
import time
from datetime import UTC, date, datetime, timedelta

import httpx

from app import cache
from app.config import AGRO_API_KEY, DATA_DIR

BASE = "https://api.agromonitoring.com/agro/1.0"
MIN_HA = 1.2
MAX_CLOUD = 30
MIN_COVERAGE = 70
DROP = 0.10           # a fall in mean NDVI this large between two clear scenes...
DROP_WITHIN_DAYS = 20  # ...no more than this far apart is worth a walk
HISTORY_DAYS = 90
NDVI_TTL_S = 12 * 3600
SOIL_TTL_S = 3 * 3600
QUIET_STAGES = {  # NDVI is naturally low (emerging) or falling (ripening) here
    "rice": {"nursery", "maturity"}, "maize": {"seedling", "maturity"},
    "cotton": {"emergence", "boll_opening"}, "soybean": {"emergence", "maturity"},
}
BANDS = [(0.2, "sparse"), (0.4, "low"), (0.6, "moderate"), (9, "dense")]
_FILE_CACHE = DATA_DIR / "satellite"


class SatelliteUnavailable(RuntimeError):
    pass


def configured() -> bool:
    return bool(AGRO_API_KEY)


def square(lat: float, lon: float, area_ha: float) -> dict:
    """GeoJSON square of the farm's area (min MIN_HA) centred on the farm point."""
    half = math.sqrt(max(area_ha, MIN_HA) * 10_000) / 2
    dlat = half / 111_320
    dlon = half / (111_320 * math.cos(math.radians(lat)))
    ring = [[lon - dlon, lat - dlat], [lon + dlon, lat - dlat], [lon + dlon, lat + dlat],
            [lon - dlon, lat + dlat], [lon - dlon, lat - dlat]]
    return {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [[
        [round(x, 6), round(y, 6)] for x, y in ring]]}}


def _get(path: str, params: dict, client: httpx.Client | None = None, timeout: float = 45):
    if not AGRO_API_KEY:
        raise SatelliteUnavailable("AGRO_API_KEY is not set")
    own = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        r = client.get(f"{BASE}{path}", params=params | {"appid": AGRO_API_KEY})
        if r.status_code != 200:
            raise SatelliteUnavailable(f"{path}: HTTP {r.status_code}")
        return r.json()
    except (httpx.HTTPError, ValueError) as e:
        raise SatelliteUnavailable(f"{path}: {type(e).__name__}") from e
    finally:
        if own:
            client.close()


def create_polygon(name: str, lat: float, lon: float, area_ha: float, client: httpx.Client | None = None) -> dict:
    if not AGRO_API_KEY:
        raise SatelliteUnavailable("AGRO_API_KEY is not set")
    own = client is None
    client = client or httpx.Client(timeout=45)
    try:
        r = client.post(f"{BASE}/polygons", params={"appid": AGRO_API_KEY, "duplicated": "true"},
                        json={"name": name, "geo_json": square(lat, lon, area_ha)})
        if r.status_code not in (200, 201):
            raise SatelliteUnavailable(f"polygon: HTTP {r.status_code} {r.text[:120]}")
        return r.json()
    except httpx.HTTPError as e:
        raise SatelliteUnavailable(f"polygon: {type(e).__name__}") from e
    finally:
        if own:
            client.close()


def _cached(key: str, ttl: int, fetch):
    hit = cache.get_json(key)
    if hit is not None:
        return hit
    f = _FILE_CACHE / f"{key.replace(':', '_')}.json"
    if f.exists():
        d = json.loads(f.read_text())
        if time.time() - d["_ts"] < ttl:
            return d["value"]
    value = fetch()
    cache.set_json(key, value, ttl)
    _FILE_CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"_ts": time.time(), "value": value}))
    return value


def parse_history(rows: list[dict]) -> list[dict]:
    """Clear scenes only, oldest first, one per day (the clearer one wins)."""
    by_day: dict[str, dict] = {}
    for r in rows:
        data = r.get("data") or {}
        if (r.get("cl") or 0) > MAX_CLOUD or (r.get("dc") or 0) < MIN_COVERAGE or data.get("mean") is None:
            continue
        on = datetime.fromtimestamp(r["dt"], UTC).date().isoformat()
        row = {"on": on, "mean": round(data["mean"], 3), "p25": round(data.get("p25", data["mean"]), 3),
               "p75": round(data.get("p75", data["mean"]), 3),
               "source": {"s2": "Sentinel-2", "l8": "Landsat 8"}.get(r.get("type"), r.get("type") or "satellite"),
               "cloud": r.get("cl")}
        if on not in by_day or row["cloud"] < by_day[on]["cloud"]:
            by_day[on] = row
    return [by_day[k] for k in sorted(by_day)]


def ndvi_series(polyid: str, today: date | None = None) -> list[dict]:
    today = today or date.today()
    end = int(time.time())
    start = int((datetime.combine(today - timedelta(days=HISTORY_DAYS), datetime.min.time())).timestamp())
    return _cached(f"sat:ndvi:{polyid}:{today}", NDVI_TTL_S,
                   lambda: parse_history(_get("/ndvi/history", {"polyid": polyid, "start": start, "end": end})))


def soil(polyid: str) -> dict:
    def fetch():
        s = _get("/soil", {"polyid": polyid})
        return {"moisture_pct": round(s["moisture"] * 100, 1), "t0_c": round(s["t0"] - 273.15, 1),
                "t10_c": round(s["t10"] - 273.15, 1),
                "observed_at": datetime.fromtimestamp(s["dt"], UTC).isoformat()}
    return _cached(f"sat:soil:{polyid}", SOIL_TTL_S, fetch)


def band(ndvi: float | None) -> str | None:
    if ndvi is None:
        return None
    return next(k for hi, k in BANDS if ndvi < hi)


def summarize(series: list[dict], crop: str, stage: str, today: date | None = None) -> dict:
    """Latest clear scene, the change since the one before, and whether it is
    a drop worth a notice."""
    if not series:
        return {"available": False}
    last = series[-1]
    prev = series[-2] if len(series) > 1 else None
    change = round(last["mean"] - prev["mean"], 3) if prev else None
    gap = (date.fromisoformat(last["on"]) - date.fromisoformat(prev["on"])).days if prev else None
    quiet = stage in QUIET_STAGES.get(crop, set())
    drop = bool(prev and change is not None and change <= -DROP and gap is not None and gap <= DROP_WITHIN_DAYS
                and not quiet)
    age = ((today or date.today()) - date.fromisoformat(last["on"])).days
    return {"available": True, "latest": last, "previous": prev, "change": change, "days_between": gap,
            "band": band(last["mean"]), "drop": drop, "quiet_stage": quiet, "age_days": age,
            "series": series[-12:]}


def evaluate(summary: dict, now: datetime) -> dict | None:
    """The greenness-drop notice (an agromet-style advisory), or None."""
    if not summary.get("available") or not summary["drop"] or summary["age_days"] > 10:
        return None
    last, prev = summary["latest"], summary["previous"]
    return {"rule": "greenness_drop", "severity": "advice", "category": "crop", "notify": True,
            "key": f"greenness_drop:{last['on']}",
            "values": {"before": prev["mean"], "after": last["mean"], "d1": prev["on"], "d2": last["on"],
                       "source": last["source"]},
            "valid_until": (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")}
