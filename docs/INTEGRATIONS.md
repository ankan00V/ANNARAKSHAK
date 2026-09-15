# External services and keys

What AnnRakshak talks to, what is live today, and which keys would make each
part real-time in production. Secrets go in `.env` (gitignored; template in
`.env.example`). Nothing secret is ever sent to the browser — the frontend
calls our API, and our API calls the providers.

## Live today

| Service | Used for | Key | Status |
|---|---|---|---|
| **Sarvam AI** — Bulbul v3 TTS, Saaras v3 STT, Sarvam-Translate v1 | Advisories read aloud in Marathi/Hindi, spoken product names in the spray check, translating expert notes | `SARVAM_API_KEY` | ✅ configured, verified live (Marathi TTS 1.4 s, en→mr translate 0.8 s) |
| **Open-Meteo forecast** | 7-day past + 7-day forecast per farm for the risk engine | none | ⚠ keyless; this dev machine's shared IP hits the daily limit |
| **Open-Meteo archive** | Fallback weather (last 14 days) and month-to-date rain vs IMD normal | none | ✅ answering |
| **OpenWeather current weather** | "Weather right now" at the farmer's GPS point during the live field check (condition text mapped to our own Hindi/Marathi words) | `OPENWEATHER_API_KEY` | ✅ configured, verified live; Open-Meteo current is the automatic fallback |
| **Open-Meteo soil model** | Modelled surface and 3–9 cm soil moisture and soil temperature for the live check — labelled *modelled, not measured* | none | ✅ answering |
| **ISRIC SoilGrids 2.0** | Soil pH (0–5 cm) and organic carbon at the farm when there is no sensor or Soil Health Card value — labelled *estimated (soil map)* | none | ⚠ REST API returning 503; the WCS GeoTIFF fallback answers; results cached on disk |
| **MoSPI eSankhyiki** (`api.mospi.gov.in`) | State pesticide-consumption baseline (ENVSTATS 56/58) | none | ✅ pulled by `data/ingest.py` (via curl — Python's TLS stack times out on this host) |
| **OpenStreetMap tiles** | Officials' hotspot map basemap | none | ✅ fine for demos; OSM policy forbids heavy use |
| **Sarvam AI key pool** | Several team keys, round-robin; a key out of credits (401/402/403) is benched 6 h, a rate-limited one (429) 1 min, shared across workers through Redis | `SARVAM_API_KEYS` | ✅ 4 keys configured |
| **Sarvam-Translate (offline job)** | `backend/translate_i18n.py` builds the machine-translated languages once from the approved English — Bengali, Tamil, Telugu, Kannada done; Malayalam, Gujarati, Punjabi, Odia next | Sarvam keys | ✅ translation memory committed, under native review |
| **Open-Meteo hourly** | The weather screen and weather→action rules: hourly temperature, humidity, dew point, rain and its probability, cloud, visibility, wind, gusts, direction, UV, pressure, FAO-56 ET0, soil temperature and 4 soil-moisture layers | none | ✅ batched per grid cell, 30-min cache (Redis/disk) |
| **OpenWeather** | Observed "now" overlaid on the model; 5-day/3-h forecast fallback when Open-Meteo is rate-limited (ET0 by FAO-56 Hargreaves) | `OPENWEATHER_API_KEY` | ✅ (One Call 3.0 needs a paid subscription — not used) |
| **AgroMonitoring** | Per-field polygon; clear-scene NDVI (Sentinel-2 / Landsat 8) and satellite soil moisture/temperature; greenness-drop notices | `AGRO_API_KEY` | ✅ polygons created on first sweep; provider image URLs carry the key, so only numbers reach the browser. Verify the account email at agromonitoring.com to keep the key active |
| **data.gov.in — Kisan Call Centre** | 262,778 Maharashtra plant-protection calls (2010–2025) pulled by `data/kcc_pull.py` and grouped by `data/kcc_signals.py` | `DATA_GOV_IN_API_KEY` | ✅ the OGD API answers only over IPv4 with a browser User-Agent from this network — the client forces both |
| **Supabase Postgres (Mumbai)** | The app database | `ANNRAKSHAK_DB_URL` | ✅ via the IPv4 transaction pooler (port 6543); the direct host is IPv6-only. `backend/migrate_db.py` copies any database to another |
| **Upstash Redis** | Shared cache, rate limits, one-watcher lease, in-app events across instances | `REDIS_URL` | ✅ ~40 ms; everything falls back to in-process when Redis is down |
| **Gmail SMTP** | Warning emails and the 6 am farm summary, in the farmer's language | `SMTP_*`, `EMAIL_FROM` | ✅ app password for the helpdesk account; List-Unsubscribe + one-click unsubscribe; per-day caps |
| **Web Push (VAPID)** | Phone notifications when the app is closed | `VAPID_PRIVATE_KEY` (optional) | ✅ keys generated into the data dir; needs HTTPS on a public host (localhost works for the demo) |

## To make it production-grade

These are the next integrations, **not wired yet**. Each row names the variable its adapter will read.

| Want | Service | Env vars | Why |
|---|---|---|---|
| Reliable real-time weather | Open-Meteo commercial plan (or IMD API via IP whitelisting) | `OPEN_METEO_API_KEY` | Keyless tier is per-IP rate-limited; a district sweep of thousands of farms needs a key. The engine already caches per location and falls back to the archive. |
| More languages | Malayalam, Gujarati, Punjabi, Odia (and native review of Bengali, Tamil, Telugu, Kannada) | Sarvam keys | `backend/translate_i18n.py --lang ml,gu,pa,od`, then native speakers correct `backend/kb/i18n/<lang>.json` and `frontend/landing/src/locales/<lang>.json` in place |
| Radar crop monitoring in the monsoon | Sentinel-1 SAR (sees through cloud) | — | Optical NDVI goes blind for weeks under monsoon cloud (Bhandara: one clear image in 90 days) |
| Alerts to basic phones | SMS gateway (MSG91 / Exotel / Twilio) + IVR | `SMS_PROVIDER`, `SMS_API_KEY`, `SMS_SENDER_ID`, `SMS_DLT_TEMPLATE_ID` | Many smallholders don't run apps. Indian SMS needs TRAI DLT template registration — start early. |
| Production map tiles | MapTiler / Stadia / self-hosted | `VITE_MAP_TILE_URL` | CARTO basemaps now require a key; OSM public tiles are for light use. |
| Measured soil pH and moisture | Soil Health Card data (per-farm value entered at registration) and IoT soil probes | none — probes post to `/api/farms/{id}/sensor` (`soil_ph`, `soil_moisture_pct`) | The live check always prefers a measured value (sensor, then Soil Health Card) over the soil map and says which it used. |
| Live check on phones | HTTPS on the public host | — | Browsers only open the camera on HTTPS (or localhost). Any TLS-terminating host or tunnel works; the WebSocket then runs as `wss://` automatically. |

`ANNRAKSHAK_VISION=stub` forces the labelled stub model even when `ml/artifacts/` holds a trained one — the test suite sets it so tests stay deterministic.

## Deliberately not integrated

- **LLM-written advice.** Every advisory sentence is authored in the knowledge base with a citation; nothing is generated at runtime, so nothing can be hallucinated. Sarvam is used only for speech and for translating free-text expert notes.
- **Any "safe to spray" verdict.** The spray check can only veto; the printed label decides dose.
