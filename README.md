# AnnRakshak

Early detection and management of crop diseases and pest infestations.
Smart India Hackathon 2026 — PS 26131 (Govt. of Maharashtra).

## Layout

- `backend/` — FastAPI app
- `frontend/landing/` — showcase/pitch site
- `frontend/farmer-app/` — lightweight PWA for farmers
- `frontend/officer-dashboard/` — district-level console
- `ml/` — training scripts, notebooks, model artifacts
- `data/` — ingestion/ETL scripts, raw data stays out of git

## Run

Backend (port 8010 — 8000 is taken on this machine):

```
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --port 8010 --app-dir backend
```

Frontend, from the repo root:

```
npm install
npm run dev:landing   # :5173
npm run dev:farmer    # :5174
npm run dev:officer   # :5175
```

## Status

- [x] Repo skeleton
- [ ] Dataset #1 (ICAR crop disease/pest images) ingestion
- [ ] CNN training, /predict, Grad-CAM
- [ ] Risk forecast, geospatial hotspots, dosage calculator
- [ ] Bhashini voice/multilingual, SMS/IVR fallback, expert validation
- [ ] Landing showcase, nearby-outbreak signal, demo script

## Real vs mocked

Tracked in `DEMO.md` once Day 1's model lands. Every stub gets flagged in code
and in the demo script.
