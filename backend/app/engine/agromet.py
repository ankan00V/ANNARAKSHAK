"""Weather -> what the farmer should do. Pure functions over an agro-weather
bundle (app.engine.agroweather) and the KB's agromet.json; no I/O.

- evaluate(): every rule that fires now, each with a dedupe key (one notice
  per farm, rule and day — or per spray) and the values its text needs;
- spray_hours() / spray_windows(): hour-by-hour spraying verdicts and the
  good windows (calm, dry for the rain-free period after, not too hot, daylight);
- water_balance(): FAO-56 crop water use (ET0 x Kc) against effective rain;
- view(): everything the weather screen shows, in one dict.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from app.kb import tr, trl

UV_BANDS = [(3, "low"), (6, "moderate"), (8, "high"), (11, "very_high"), (99, "extreme")]
SEVERITY_ORDER = {"warning": 0, "advice": 1, "info": 2}


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _hour_floor(now: datetime) -> datetime:
    return now.replace(minute=0, second=0, microsecond=0)


def upcoming(b: dict, now: datetime, hours: int) -> list[dict]:
    start, end = _hour_floor(now), _hour_floor(now) + timedelta(hours=hours)
    return [h for h in b["hours"] if start <= _t(h["t"]) < end]


def between(b: dict, start: datetime, end: datetime) -> list[dict]:
    return [h for h in b["hours"] if start <= _t(h["t"]) < end]


def days_ahead(b: dict, today: date, n: int) -> list[dict]:
    return [d for d in b["days"] if 0 <= (date.fromisoformat(d["on"]) - today).days < n]


def past_days(b: dict, today: date, n: int) -> list[dict]:
    return [d for d in b["days"] if 0 < (today - date.fromisoformat(d["on"])).days <= n]


def uv_band(uv: float | None) -> str | None:
    if uv is None:
        return None
    return next(k for hi, k in UV_BANDS if uv < hi)


def day_word(on: date, today: date, words: dict, lang: str) -> str:
    delta = (on - today).days
    if delta == 0:
        return tr(words["today"], lang)
    if delta == 1:
        return tr(words["tomorrow"], lang)
    return trl(words["weekdays"], lang)[on.weekday()]


def when(t: datetime, now: datetime, words: dict, lang: str) -> str:
    return f"{day_word(t.date(), now.date(), words, lang)} {t:%H:%M}"


def _r(x: float | None, nd: int = 0):
    if x is None:
        return None
    return round(x) if nd == 0 else round(x, nd)


# --------------------------------------------------------------------------
# Spraying
# --------------------------------------------------------------------------

def spray_hours(b: dict, now: datetime, cfg: dict, horizon: int = 48) -> list[dict]:
    """Each coming hour: good / caution / avoid, with the reasons."""
    out = []
    for h in upcoming(b, now, horizon):
        t = _t(h["t"])
        ahead = between(b, t, t + timedelta(hours=cfg["rain_free_hours"] + 1))
        prob = max((x.get("prob") or 0 for x in ahead), default=0)
        rain = max((x.get("precip") or 0 for x in ahead), default=0)
        wind, gust, temp = h.get("wind") or 0, h.get("gust") or 0, h.get("temp")
        avoid, caution = [], []
        if not h.get("is_day"):
            avoid.append(("night", None))
        if wind > cfg["wind_avoid_kmh"]:
            avoid.append(("wind", _r(wind)))
        elif wind > cfg["wind_max_kmh"]:
            caution.append(("wind", _r(wind)))
        elif wind < cfg["wind_min_kmh"]:
            caution.append(("calm", None))
        if gust > cfg["gust_avoid_kmh"]:
            avoid.append(("gust", _r(gust)))
        elif gust > cfg["gust_max_kmh"]:
            caution.append(("gust", _r(gust)))
        if prob >= cfg["rain_prob_avoid"] or rain >= 2 * cfg["rain_mm_max"] + 0.3:
            avoid.append(("rain", _r(prob)))
        elif prob >= cfg["rain_prob_max"] or rain > cfg["rain_mm_max"]:
            caution.append(("rain", _r(prob)))
        if temp is not None and temp > cfg["t_avoid_c"]:
            avoid.append(("heat", _r(temp)))
        elif temp is not None and temp > cfg["t_max_c"]:
            caution.append(("heat", _r(temp)))
        if (h.get("vis") is not None and h["vis"] < cfg["fog_visibility_m"]) or (h.get("rh") or 0) >= cfg["rh_wet_leaf"]:
            caution.append(("wet", None))
        status = "avoid" if avoid else "caution" if caution else "good"
        out.append({"t": h["t"], "status": status, "reasons": avoid or caution,
                    "wind": _r(wind), "gust": _r(gust), "prob": _r(prob), "temp": _r(temp, 1)})
    return out


def spray_windows(scored: list[dict], min_hours: int) -> list[dict]:
    windows, run = [], []
    for h in scored + [{"status": "end"}]:
        if h["status"] == "good":
            run.append(h)
            continue
        if len(run) >= min_hours:
            end = _t(run[-1]["t"]) + timedelta(hours=1)
            windows.append({"start": run[0]["t"], "end": end.strftime("%Y-%m-%dT%H:%M"),
                            "hours": len(run), "wind": round(sum(x["wind"] for x in run) / len(run))})
        run = []
    return windows


def reason_text(reasons: list[tuple[str, float | None]], words: dict, lang: str) -> str:
    parts = []
    for key, v in reasons:
        tpl = tr(words["reasons"][key], lang)
        parts.append(tpl.format(v=v) if "{v}" in tpl else tpl)
    s = ", ".join(parts)
    return s[:1].upper() + s[1:] if lang == "en" else s


# --------------------------------------------------------------------------
# Water balance (FAO-56)
# --------------------------------------------------------------------------

def water_balance(b: dict, today: date, kc: float | None, th: dict, crop: str, stop: bool) -> dict:
    week = past_days(b, today, 7)
    if kc is None or len(week) < 5 or any(d.get("et0") is None or d.get("rain") is None for d in week):
        return {"available": False}
    et0 = sum(d["et0"] for d in week)
    rain = sum(d["rain"] for d in week)
    eff = sum(max(0.0, d["rain"] - th["effective_rain_floor_mm"]) * th["effective_rain_fraction"] for d in week)
    etc = et0 * kc
    deficit = max(0.0, etc - eff)
    nxt = days_ahead(b, today, 3)
    useful = [d for d in nxt if (d.get("rain") or 0) >= th["useful_rain_mm_day"]
              and (d.get("prob") or 100) >= th["useful_rain_min_prob"]]
    today_row = next((d for d in b["days"] if d["on"] == today.isoformat()), None)
    need = th["irrigate_deficit_mm"].get(crop, 25)
    verdict = ("stop_stage" if stop else "hold_rain" if useful else "irrigate" if deficit >= need else "ok")
    return {
        "available": True, "days": len(week), "kc": kc, "et0_week": round(et0, 1), "etc_week": round(etc, 1),
        "rain_week": round(rain, 1), "eff_rain_week": round(eff, 1), "deficit": round(deficit, 1),
        "deficit_threshold": need,
        "et0_today": _r(today_row.get("et0"), 1) if today_row else None,
        "etc_today": _r(today_row["et0"] * kc, 1) if today_row and today_row.get("et0") is not None else None,
        "next3_rain": round(sum(d.get("rain") or 0 for d in nxt), 1), "next3_useful_days": len(useful),
        "verdict": verdict,
    }


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

def _adv(rule: dict, key: str, values: dict, valid_until: datetime, **extra) -> dict:
    return {"rule": rule["id"], "severity": rule["severity"], "category": rule["category"],
            "notify": rule["notify"], "key": key, "values": values,
            "valid_until": valid_until.strftime("%Y-%m-%dT%H:%M")} | extra


def evaluate(b: dict, am: dict, crop: str, stage: str, now: datetime, *,
             sprays: list[dict] | None = None, needs_spray: bool = True) -> list[dict]:
    """Every rule that fires. `values` hold raw numbers and datetimes as ISO
    strings; render() turns them into words in the farmer's language."""
    th, rules = am["thresholds"], {r["id"]: r for r in am["rules"]}
    today = now.date()
    out: list[dict] = []
    fired: set[str] = set()

    def add(rule_id: str, key: str, values: dict, valid_until: datetime, **extra):
        out.append(_adv(rules[rule_id], key, values, valid_until, **extra))
        fired.add(rule_id)

    next24, next48 = upcoming(b, now, 24), upcoming(b, now, 48)

    # Thunderstorm / lightning
    hits = [h for h in upcoming(b, now, th["thunder_hours_ahead"])
            if h.get("code") in th["thunder_codes"] and (h.get("prob") or 0) >= th["thunder_min_prob"]]
    if hits:
        first = _t(hits[0]["t"])
        add("thunderstorm", f"thunderstorm:{first.date()}", {"when": hits[0]["t"]},
            _t(hits[-1]["t"]) + timedelta(hours=1))

    # Heavy rain, then 'hold irrigation'
    coming = days_ahead(b, today, th["rain_days_ahead"])
    heavy = [d for d in coming if (d.get("rain") or 0) >= th["heavy_rain_mm_day"]]
    if heavy:
        d = max(heavy, key=lambda x: x["rain"])
        add("heavy_rain", f"heavy_rain:{d['on']}", {"day": d["on"], "mm": _r(d["rain"])},
            datetime.fromisoformat(d["on"]) + timedelta(days=1),
            very_heavy=d["rain"] >= th["very_heavy_rain_mm_day"])
    rain48 = sum(h.get("precip") or 0 for h in next48)
    prob48 = max((h.get("prob") or 0 for h in next48), default=0)
    if "heavy_rain" not in fired and rain48 >= th["skip_irrigation_mm_48h"] and prob48 >= th["skip_irrigation_min_prob"]:
        add("rain_skip_irrigation", f"rain_skip_irrigation:{today}", {"mm": _r(rain48), "prob": _r(prob48)},
            now + timedelta(hours=48))

    # Strong gusts
    if next24:
        g = max(next24, key=lambda h: h.get("gust") or 0)
        if (g.get("gust") or 0) >= th["strong_gust_kmh"]:
            add("strong_wind", f"strong_wind:{g['t'][:10]}", {"when": g["t"], "gust": _r(g["gust"])},
                now + timedelta(hours=24))

    # Frost (clear, calm, cold night) else cold
    for d in days_ahead(b, today, 2):
        if d.get("tmin") is None:
            continue
        on = date.fromisoformat(d["on"])
        night = between(b, datetime.combine(on, datetime.min.time()), datetime.combine(on, datetime.min.time()) + timedelta(hours=8))
        cloud = sum(h.get("cloud") or 0 for h in night) / len(night) if night else 100
        wind = sum(h.get("wind") or 0 for h in night) / len(night) if night else 99
        if d["tmin"] <= th["frost_tmin_c"] and cloud < th["frost_max_cloud_pct"] and wind < th["frost_max_wind_kmh"]:
            add("frost", f"frost:{d['on']}", {"day": d["on"], "tmin": _r(d["tmin"])},
                datetime.combine(on, datetime.min.time()) + timedelta(hours=10))
            break
    if "frost" not in fired:
        cold = [d for d in days_ahead(b, today, 3) if d.get("tmin") is not None and d["tmin"] <= th["cold_tmin_c"]]
        if cold:
            d = min(cold, key=lambda x: x["tmin"])
            add("cold", f"cold:{d['on']}", {"day": d["on"], "tmin": _r(d["tmin"])},
                datetime.fromisoformat(d["on"]) + timedelta(days=1))

    # Rain after a spray the farmer logged
    for s in sprays or []:
        t0 = _t(s["at"]) if isinstance(s["at"], str) else s["at"]
        if now - t0 > timedelta(hours=24) or t0 > now:
            continue
        win = between(b, t0, t0 + timedelta(hours=th["rain_after_spray_hours"]))
        mm = sum(h.get("precip") or 0 for h in win)
        if mm >= th["rain_after_spray_mm"]:
            done = t0 + timedelta(hours=th["rain_after_spray_hours"]) <= now
            add("rain_after_spray", f"rain_after_spray:{s['id']}",
                {"product": s.get("product"), "time": t0.strftime("%H:%M"), "mm": _r(mm, 1),
                 "hours": th["rain_after_spray_hours"], "verb": "past" if done else "future"},
                t0 + timedelta(hours=24))

    # Heat on the crop
    heat_stages = am["heat_sensitive_stages"].get(crop, [])
    hot = [d for d in days_ahead(b, today, 3) if d.get("tmax") is not None]
    if hot:
        d = max(hot, key=lambda x: x["tmax"])
        why = "flowering" if stage in heat_stages and d["tmax"] >= th["heat_flowering_c"] else \
            "any" if d["tmax"] >= th["heat_any_stage_c"] else None
        if why:
            add("heat_crop", f"heat_crop:{d['on']}", {"day": d["on"], "tmax": _r(d["tmax"]), "why": why},
                datetime.fromisoformat(d["on"]) + timedelta(days=1))

    # Fungal weather
    wet = [h for h in next48 if (h.get("rh") or 0) >= th["fungal_rh"]
           and h.get("temp") is not None and th["fungal_t_min"] <= h["temp"] <= th["fungal_t_max"]]
    if len(wet) >= th["fungal_hours_48h"]:
        add("fungal_weather", f"fungal_weather:{today}",
            {"hours": len(wet), "tmin": _r(min(h["temp"] for h in wet)), "tmax": _r(max(h["temp"] for h in wet))},
            now + timedelta(hours=48))

    # Spraying: the next good window, or none in 24 h
    sp = am["spray"]
    scored = spray_hours(b, now, sp, horizon=48)
    windows = [w for w in spray_windows(scored, sp["min_window_hours"]) if _t(w["start"]) < now + timedelta(hours=24)]
    if windows:
        w = windows[0]
        add("spray_window", f"spray_window:{today}", {"start": w["start"], "end": w["end"], "wind": w["wind"]},
            _t(w["end"]))
    else:
        day_hours = [h for h in scored[:24] if h["status"] != "good" and h["reasons"][0][0] != "night"]
        tally = Counter(k for h in day_hours for k, _ in h["reasons"] if k != "night")
        top = [k for k, _ in tally.most_common(2)] or ["rain"]
        reasons = [(k, max((v for h in day_hours for kk, v in h["reasons"] if kk == k and v is not None), default=None))
                   for k in top]
        out.append(_adv(rules["spray_no_window"], f"spray_no_window:{today}", {"reasons": reasons},
                        now + timedelta(hours=24)) | {"notify": rules["spray_no_window"]["notify"] and needs_spray})
        fired.add("spray_no_window")

    # Irrigation from the water balance
    kc = am["kc"].get(crop, {}).get(stage)
    stop = stage in am.get("irrigation_stop_stages", {}).get(crop, [])
    wb = water_balance(b, today, kc, th, crop, stop)
    if wb["available"] and wb["verdict"] == "irrigate" and "rain_skip_irrigation" not in fired and "heavy_rain" not in fired:
        add("irrigate", f"irrigate:{today}", {"etc": _r(wb["etc_week"]), "rain": _r(wb["eff_rain_week"]),
                                              "deficit": _r(wb["deficit"])}, now + timedelta(hours=24))

    # People: strong sun and heat
    for d in days_ahead(b, today, 2):
        uv, tmax, feels = d.get("uv_max"), d.get("tmax"), d.get("feels_max")
        if uv is not None and uv >= th["uv_very_high"] and (
                (tmax or 0) >= th["heat_people_tmax_c"] or (feels or 0) >= th["heat_people_feels_c"]):
            add("heat_people", f"heat_people:{d['on']}",
                {"day": d["on"], "uv": _r(uv), "tmax": _r(tmax), "feels": _r(feels if feels is not None else tmax)},
                datetime.fromisoformat(d["on"]) + timedelta(days=1))
            break

    # Fog
    foggy = [h for h in upcoming(b, now, th["fog_hours_ahead"]) if h.get("vis") is not None and h["vis"] < th["fog_visibility_m"]]
    if foggy:
        f = min(foggy, key=lambda h: h["vis"])
        add("fog", f"fog:{f['t'][:10]}", {"when": f["t"], "vis": int(round(f["vis"], -1))}, _t(foggy[-1]["t"]) + timedelta(hours=1))

    out.sort(key=lambda a: SEVERITY_ORDER[a["severity"]])
    return out


def render(adv: dict, am: dict, lang: str, crop: str, now: datetime) -> dict:
    """An advisory in the farmer's language: title, text, what to do, source."""
    rule = next(r for r in am["rules"] if r["id"] == adv["rule"])
    words = am["words"]
    v = dict(adv["values"])
    for k in ("when", "start", "end"):
        if k in v and isinstance(v[k], str):
            t = _t(v[k])
            v[k] = when(t, now, words, lang) if k == "when" else f"{t:%H:%M}"
    if "day" in v:
        v["day"] = day_word(date.fromisoformat(v["day"]), now.date(), words, lang)
    for k in ("d1", "d2"):
        if k in v:
            v[k] = date.fromisoformat(v[k]).strftime("%d/%m")
    for k in ("before", "after"):
        if isinstance(v.get(k), float):
            v[k] = f"{v[k]:.2f}"
    if adv["rule"] == "spray_no_window":
        v["reason"] = reason_text([tuple(x) for x in v.pop("reasons")], words, lang)
    if adv["rule"] == "rain_after_spray":
        v["verb"] = tr(words["rain_verbs"][v["verb"]], lang)
        v["product"] = v.get("product") or tr(words["product_unknown"], lang)
    if adv["rule"] == "heat_crop":
        v["why"] = tr(rule["why"][v["why"]], lang)
    do = trl(rule["do"], lang)
    if crop in rule.get("crop_do", {}):
        do.insert(0, tr(rule["crop_do"][crop], lang))
    return {
        "id": adv["key"], "rule": adv["rule"], "severity": adv["severity"], "category": adv["category"],
        "title": tr(rule["title"], lang).format(**v), "text": tr(rule["text"], lang).format(**v),
        "do": do, "source": rule["source"], "valid_until": adv["valid_until"],
    }


# --------------------------------------------------------------------------
# The weather screen
# --------------------------------------------------------------------------

def view(b: dict, am: dict, crop: str, stage: str, now: datetime, lang: str, *,
         sprays: list[dict] | None = None, needs_spray: bool = True) -> dict:
    cur = b["current"]
    hours = upcoming(b, now, 48)
    day_ago = [h for h in b["hours"] if _t(h["t"]) == _hour_floor(now) - timedelta(hours=24)]
    pressure_trend = None
    if cur.get("pressure") is not None and day_ago and day_ago[0].get("pressure") is not None:
        pressure_trend = round(cur["pressure"] - day_ago[0]["pressure"], 1)
    next3h = upcoming(b, now, 3)
    now_row = hours[0] if hours else {}
    sp = am["spray"]
    scored = spray_hours(b, now, sp, horizon=48)
    windows = spray_windows(scored, sp["min_window_hours"])
    kc = am["kc"].get(crop, {}).get(stage)
    stop = stage in am.get("irrigation_stop_stages", {}).get(crop, [])
    soil_row = now_row if now_row.get("sm0") is not None or now_row.get("soil_t0") is not None else None
    advisories = [render(a, am, lang, crop, now)
                  for a in evaluate(b, am, crop, stage, now, sprays=sprays, needs_spray=needs_spray)]
    return {
        "fetched_at": b["fetched_at"], "stale": b.get("stale", False), "source": b["source"],
        "current": {
            "time": cur.get("time"), "temp": _r(cur.get("temp"), 1), "feels": _r(cur.get("feels"), 1),
            "rh": _r(cur.get("rh")), "dew": _r(now_row.get("dew"), 1), "precip": _r(cur.get("precip"), 1),
            "prob_3h": max((h.get("prob") or 0 for h in next3h), default=None) if next3h else None,
            "wind": _r(cur.get("wind")), "gust": _r(cur.get("gust")), "wdir": _r(cur.get("wdir")),
            "uv": _r(cur.get("uv"), 1), "uv_band": uv_band(cur.get("uv")), "cloud": _r(cur.get("cloud")),
            "vis": _r(cur.get("vis")), "pressure": _r(cur.get("pressure")), "pressure_trend_24h": pressure_trend,
            "code": cur.get("code"), "is_day": cur.get("is_day"), "station": cur.get("station"),
        },
        "hourly": [
            {"t": h["t"], "temp": _r(h.get("temp"), 1), "rh": _r(h.get("rh")), "prob": _r(h.get("prob")),
             "precip": _r(h.get("precip"), 1), "wind": _r(h.get("wind")), "gust": _r(h.get("gust")),
             "wdir": _r(h.get("wdir")), "uv": _r(h.get("uv"), 1), "cloud": _r(h.get("cloud")),
             "vis": _r(h.get("vis")), "code": h.get("code"), "is_day": h.get("is_day"),
             "spray": s["status"]}
            for h, s in zip(hours, scored)
        ],
        "daily": [
            {"on": d["on"], "tmin": _r(d.get("tmin"), 1), "tmax": _r(d.get("tmax"), 1),
             "rain": _r(d.get("rain"), 1), "prob": _r(d.get("prob")), "rain_hours": _r(d.get("rain_hours")),
             "wind_max": _r(d.get("wind_max")), "gust_max": _r(d.get("gust_max")), "wdir": _r(d.get("wdir")),
             "uv_max": _r(d.get("uv_max"), 1),
             "sunshine_h": _r(d["sunshine_s"] / 3600, 1) if d.get("sunshine_s") is not None else None,
             "radiation": _r(d.get("radiation"), 1), "et0": _r(d.get("et0"), 1), "code": d.get("code"),
             "sunrise": d.get("sunrise"), "sunset": d.get("sunset")}
            for d in days_ahead(b, now.date(), 7)
        ],
        "soil": None if soil_row is None else {
            "temp_surface": _r(soil_row.get("soil_t0"), 1), "temp_6cm": _r(soil_row.get("soil_t6"), 1),
            "moisture": [{"depth": d, "pct": _r(soil_row[k] * 100) if soil_row.get(k) is not None else None}
                         for d, k in (("0–1 cm", "sm0"), ("1–3 cm", "sm1"), ("3–9 cm", "sm3"), ("9–27 cm", "sm9"))],
        },
        "water": water_balance(b, now.date(), kc, am["thresholds"], crop, stop),
        "spray": {"now": scored[0] if scored else None, "windows": windows[:4],
                  "reasons_text": reason_text(scored[0]["reasons"], am["words"], lang) if scored and scored[0]["reasons"] else None},
        "advisories": advisories,
    }
