# AnnRakshak

## Satellite Intelligence for Crop Stress & Drought Monitoring

**Autonomous Satellite Imagery Crop Disease & Drought Segmentation Suite**  

AnnRakshak is an agricultural intelligence platform designed to help farmers and agricultural stakeholders identify crop-health risks earlier. Its existing crop-diagnosis workflow combines image-based disease identification, confidence-aware decision-making, expert escalation, weather risk signals, and field-level monitoring.

This README reframes AnnRakshak toward satellite-driven crop stress analysis: using multispectral imagery, vegetation indices, geospatial visualization, and (as the satellite segmentation capability is developed and validated) pixel-level stress maps and yield-depletion risk estimates.

> **Implementation note:** The repository currently documents a deployed EfficientNetV2-S leaf-image diagnosis pipeline and satellite greenness/soil-moisture signals. Do not interpret this README as confirmation that a U-Net multispectral segmentation model or validated yield-forecasting model is already deployed. Those capabilities should be marked *in development* until implemented and evaluated.

---

## Overview

Crop stress is rarely uniform across a field. Ground-level diagnosis can identify symptoms on an individual plant, while satellite imagery can help monitor broader spatial patterns.

AnnRakshak is being positioned to connect these perspectives:

- **Ground-level diagnosis:** classify crop disease symptoms from farmer-submitted images.
- **Satellite crop monitoring:** use NDVI and other geospatial signals to highlight potential vegetation stress.
- **Spatial intelligence:** visualize field-level conditions and prioritize areas for inspection.
- **Decision support:** route uncertain cases to experts and provide localized, safety-conscious guidance.

The satellite-focused direction is to process multispectral satellite tiles, segment crop-stress regions, quantify affected areas, and estimate yield-depletion risk where sufficient reference and validation data are available.

## Core Capabilities

### Existing platform capabilities

| Capability | Implementation / location |
|---|---|
| Crop disease image diagnosis | `ml/train.py` — EfficientNetV2-S; FastAPI diagnosis endpoint |
| Confidence-aware decision gate | `backend/app/engine/gate.py` — advise, clarify, escalate, or retake |
| Weather-based risk forecasting | `backend/app/engine/risk.py` — weather windows, crop stage, farm history, rainfall normals |
| Satellite greenness signals | NDVI from Sentinel-2/Landsat 8 and soil-moisture signals per field; greenness drops can trigger alerts |
| Geospatial hotspot mapping | Officials' map for confirmed, awaiting-expert, and AI-advised cases |
| Expert validation | `/expert` console for confirming/correcting cases and lab referrals |
| Multilingual advisories | Eleven languages; authored and machine-translated content with review caveats |
| Weather alerts | Hourly weather screen and weather-to-action rules |
| Farmer and expert workflows | Role-based signup, farm profiles, case routing, and access checks |
| Field follow-up | Day-4 check-in and automatic re-escalation when conditions worsen |
| Officials' dashboard | `/officer` KPIs, risk outlook, district data, and model card |

### Satellite segmentation suite — target workflow

The following describes the satellite-focused architecture and intended workflow. List each item as *implemented* only after the corresponding code path and evaluation are available.

| Target capability | Intended approach |
|---|---|
| Multispectral tile ingestion | Load georeferenced raster bands with Rasterio |
| Vegetation-health indices | Compute NDVI from red and near-infrared reflectance; document nodata and scaling |
| Pixel-level crop-stress segmentation | PyTorch U-Net producing spatial masks |
| Geospatial visualization | Leaflet overlays aligned to raster coordinates and field boundaries |
| Stress quantification | Aggregate valid stress pixels into area and percentage summaries |
| Drought/stress trend analysis | Compare compatible observations across dates, accounting for cloud and seasonal effects |
| Yield-depletion risk | Forecast only with a defined, validated methodology and appropriate crop, weather, and historical yield data |

**NDVI is a vegetation greenness indicator, not a disease diagnosis by itself.** Low or declining NDVI may reflect drought, crop stage, soil/background effects, management practices, cloud contamination, or other causes. Satellite outputs should therefore be presented as risk signals and validated against field observations.

---

## System Architecture

### Existing application

```text
React Farmer PWA / Expert Console / Officials Dashboard
                       |
                    FastAPI
                       |
       +---------------+----------------+
       |               |                |
  Diagnosis Gate   Risk & Weather   Expert Workflow
       |               |                |
 EfficientNetV2-S   Weather/data     Case validation
       |
 Confidence-aware outcome:
 advise / clarify / escalate / retake
```

### Satellite-focused pipeline

```text
Multispectral Satellite Tiles
            |
     Rasterio preprocessing
            |
  Band checks + georeferencing
            |
       NDVI / indices
            |
   PyTorch U-Net segmentation
            |
  Stress mask + confidence/QA
            |
 Area statistics + temporal comparison
            |
       Leaflet map layers
            |
 Field inspection / risk assessment
            |
 Yield-depletion estimate*
```

`*` Yield estimates require a separately specified and validated forecasting method. A segmentation mask alone does not establish yield loss.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Backend API | FastAPI |
| Existing image classifier | PyTorch, EfficientNetV2-S |
| Satellite segmentation target | PyTorch, U-Net |
| Geospatial raster processing | Rasterio |
| Interactive maps | Leaflet |
| Data and advisory workflows | Python, JSON knowledge base |
| Weather integrations | Open-Meteo and documented external sources |

---

## Model Evaluation & Responsible Deployment

### Existing leaf-image model

The repository's documented model report describes a held-out ICAR test set of 126 images, with duplicates removed before splitting.

| Method | Test accuracy | Macro-F1 |
|---|---:|---:|
| DenseNet201 + frozen ANN head | 81.7% | 0.818 |
| EfficientNetV2-S + frozen ANN head | 82.5% | 0.823 |
| MobileNetV3 + frozen ANN head | 79.4% | 0.791 |
| **EfficientNetV2-S fine-tuned** | **89.7%** | **0.896** |

The README's existing live-evaluation notes report 469 held-out photo diagnoses: the system advised on 84% and was correct on 97.5% of advised cases. These are **leaf-image diagnosis results**, not satellite segmentation metrics.

### Satellite model evaluation (to be added)

Do not publish satellite model accuracy until an evaluation has been run on a clearly defined, geographically and temporally separated test set. At minimum, report:

- Dataset/source, satellite sensor, bands, acquisition dates, and preprocessing.
- Ground-truth labeling protocol and class definitions.
- Train/validation/test split strategy, including geographic and temporal separation.
- Per-class precision, recall, F1, IoU, and Dice score.
- Performance by crop, region, season, and stress severity where sample sizes permit.
- Cloud, nodata, mixed-pixel, and out-of-distribution handling.
- Area-estimation error and yield-forecast error, if those outputs are claimed.

### Safety and uncertainty principles

- **Do not guess:** uncertain diagnosis cases can be clarified or escalated.
- **Show uncertainty:** confidence and alternatives should be visible where appropriate.
- **Treat satellite outputs as screening signals:** require field validation before high-impact recommendations.
- **Chemical advice is constrained:** the advisory ladder prioritizes cultural, then biological, then chemical interventions.
- **Separate evidence from inference:** NDVI, segmentation, disease diagnosis, and yield forecasts are different outputs.
- **Label stubs and prototypes:** an untrained or unavailable model must never appear as a successful prediction.

---

## Repository Layout

```text
backend/            FastAPI app
  app/engine/       gate, advisory, risk, weather, prior, vision
  app/routers/      farmer, expert, officials APIs
  kb/               crop knowledge, advisories, cues, risk rules
  tests/            backend tests
  seed.py           demo farms
  demo_story.py     demo workflow

frontend/landing/   React app: landing, farmer PWA, expert, officials
ml/                 training scripts, reports, confusion matrix, Grad-CAM
data/               ingestion scripts and dataset documentation
docs/               integration notes
```

If a satellite segmentation module is added, document its exact location here (for example, a dedicated satellite inference/training module) only after that path exists in the repository.

## Getting Started

The following commands reflect the existing application workflow. Satellite-specific dependencies, data preparation, and model commands should be added when that pipeline is implemented.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r ml/requirements.txt

cp .env.example .env
# Add required API keys as documented in .env.example

.venv/bin/python data/ingest.py
.venv/bin/python ml/train.py
.venv/bin/python ml/sample_outcomes.py

.venv/bin/python backend/seed.py --reset
.venv/bin/uvicorn app.main:app --port 8010 --app-dir backend

npm install
npm run dev:landing
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8010`

Optional demo workflow:

```bash
.venv/bin/python backend/demo_story.py
```

Run backend tests:

```bash
cd backend
../.venv/bin/python -m pytest -q
```

Check `data/DATASETS.md`, `data/MANUAL_DOWNLOADS.md`, and `docs/INTEGRATIONS.md` for data provenance, manual dataset requirements, and external API setup.

## Data Sources & Provenance

The repository documents:

- ICAR crop disease and insect-pest images for rice and maize.
- Additional de-duplicated cotton, soybean, maize, and rice field photos.
- IMD rainfall data and rainfall normals.
- MoSPI pesticide-consumption baseline.
- ICAR technology repository entries linked to pests.
- Open-Meteo weather data.
- INSAT-3DS Hydro-Estimator rainfall from MOSDAC.

Satellite imagery, derived indices, labels, and any yield data used by the segmentation suite should be documented with source, license/access terms, acquisition dates, spatial resolution, preprocessing, and known limitations.

**Acknowledgement:** Satellite rainfall data courtesy of MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre), Space Applications Centre, ISRO — https://mosdac.gov.in/

## Roadmap

- [x] Confidence-aware crop disease diagnosis workflow
- [x] Expert validation and farmer follow-up workflows
- [x] Weather-based risk signals and field-level geospatial views
- [x] Satellite greenness / NDVI signals documented in the existing platform
- [ ] Dedicated multispectral tile ingestion and quality-control pipeline
- [ ] Validated PyTorch U-Net crop-stress segmentation
- [ ] Georeferenced stress-mask overlays in Leaflet
- [ ] Field-level stress area quantification and temporal comparison
- [ ] Validated crop- and region-aware yield-depletion forecasting
- [ ] Satellite-specific benchmark report and model card

## License

This project is released under the MIT License. See the repository's `LICENSE` file.
