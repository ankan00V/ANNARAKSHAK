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
| **MoSPI eSankhyiki** (`api.mospi.gov.in`) | State pesticide-consumption baseline (ENVSTATS 56/58) | none | ✅ pulled by `data/ingest.py` (via curl — Python's TLS stack times out on this host) |
| **OpenStreetMap tiles** | Officials' hotspot map basemap | none | ✅ fine for demos; OSM policy forbids heavy use |

## To make it production-grade

These are the next integrations, **not wired yet** — today the code reads only `SARVAM_API_KEY`, `ANNRAKSHAK_DATA_DIR`, `ANNRAKSHAK_DB_URL`, `ANNRAKSHAK_VISION`, `VITE_MAP_TILE_URL` and `ANNRAKSHAK_API`. Each row names the variable its adapter will read.

| Want | Service | Env vars | Why |
|---|---|---|---|
| Reliable real-time weather | Open-Meteo commercial plan (or IMD API via IP whitelisting) | `OPEN_METEO_API_KEY` | Keyless tier is per-IP rate-limited; a district sweep of thousands of farms needs a key. The engine already caches per location and falls back to the archive. |
| Alerts to basic phones | SMS gateway (MSG91 / Exotel / Twilio) + IVR | `SMS_PROVIDER`, `SMS_API_KEY`, `SMS_SENDER_ID`, `SMS_DLT_TEMPLATE_ID` | Many smallholders don't run apps. Indian SMS needs TRAI DLT template registration — start early. |
| Push notifications | Web Push (VAPID) | `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | Wake the PWA when a spread or trap alert fires. |
| Automated government data | data.gov.in API | `DATA_GOV_IN_API_KEY` | Pull Kisan Call Centre queries (calibrate risk rules against real complaint peaks), APY crop area by district, IMD tables — instead of manual CAPTCHA downloads. Register at data.gov.in → My Account. |
| Production map tiles | MapTiler / Stadia / self-hosted | `VITE_MAP_TILE_URL` | CARTO basemaps now require a key; OSM public tiles are for light use. |
| Production database | PostgreSQL (+ PostGIS for radius queries at scale) | `ANNRAKSHAK_DB_URL` (already read) | SQLite is right for a single-box demo; Postgres for concurrent district use. |

`ANNRAKSHAK_VISION=stub` forces the labelled stub model even when `ml/artifacts/` holds a trained one — the test suite sets it so tests stay deterministic.

## Deliberately not integrated

- **LLM-written advice.** Every advisory sentence is authored in the knowledge base with a citation; nothing is generated at runtime, so nothing can be hallucinated. Sarvam is used only for speech and for translating free-text expert notes.
- **Any "safe to spray" verdict.** The spray check can only veto; the printed label decides dose.
